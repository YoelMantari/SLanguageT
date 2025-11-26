import cv2
import mediapipe as mp
import numpy as np
from tensorflow import keras
from typing import Dict, List, Optional, Tuple
import json
import time

# Importar el constructor de oraciones
try:
    from sentence_builder import SentenceBuilder
    SENTENCE_BUILDER_AVAILABLE = True
except ImportError:
    SENTENCE_BUILDER_AVAILABLE = False
    print("⚠️ SentenceBuilder no disponible")


class SignLanguageDetector:
    """
    Clase para detectar y traducir lenguaje de señas usando MediaPipe y un modelo de TensorFlow
    Implementación optimizada basada en Senia.py
    """
    
    def __init__(self, model_path: str):
        """
        Inicializar el detector de lenguaje de señas
        
        Args:
            model_path: Ruta al archivo del modelo .keras
        """
        self.model_path = model_path
        self.model = None
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Configuración de MediaPipe Holistic (optimizada como en Senia.py)
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Cargar labels
        self.labels = self._load_labels()
        
        # Cargar el modelo
        self._load_model()
        
        # Configuración del sistema (optimizada para flujo continuo)
        self.NUM_FRAMES = 10  # Frames por secuencia (más rápido)
        self.CONFIDENCE_THRESHOLD = 0.60  # Umbral más bajo para mejor flujo
        self.SMOOTHING_WINDOW = 2  # Ventana muy pequeña para respuesta rápida
        
        # Estados del sistema
        self.state = "WAIT_HANDS"
        self.sequence = []
        self.smooth_preds = []
        self.predicted_label = ""
        
        # Control de flujo continuo
        self.last_prediction_time = 0
        self.cooldown_seconds = 1.5  # Tiempo entre predicciones
        self.frames_since_last_pred = 0
        self.continuous_mode = True
        
        # Constructor de oraciones con LLM
        self.sentence_builder = None
        if SENTENCE_BUILDER_AVAILABLE:
            try:
                self.sentence_builder = SentenceBuilder()
                print("✅ SentenceBuilder inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando SentenceBuilder: {e}")
    
    def _load_labels(self):
        """Cargar labels desde el archivo JSON"""
        try:
            labels_path = self.model_path.replace('modelo_senas.keras', 'labels.json')
            with open(labels_path, "r") as f:
                labels = json.load(f)
            print(f"Labels cargados: {len(labels)} clases")
            return labels
        except Exception as e:
            print(f"Error cargando labels: {str(e)}")
            return []

        
    def _load_model(self):
        """Cargar el modelo de TensorFlow"""
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(self.model_path)
            print(f"Modelo cargado exitosamente desde {self.model_path}")
            print(f"Input shape: {self.model.input_shape}")
            print(f"Output shape: {self.model.output_shape}")
        except Exception as e:
            print(f"Error cargando modelo: {str(e)}")
            self.model = None
    
    def get_available_signs(self) -> List[str]:
        """
        Obtener lista de señas disponibles en el modelo
        
        Returns:
            Lista de nombres de señas
        """
        return self.labels
    
    def extract_keypoints(self, results) -> Optional[np.ndarray]:
        """
        Extraer keypoints usando la misma lógica que Senia.py
        El modelo espera 135 features:
        - Pose básica (3 puntos * 3 coords = 9 features)
        - Mano Izquierda (21*3=63)
        - Mano Derecha (21*3=63)
        Total: 135
        """
        out = []
        pose_map = {"left_shoulder": 11, "right_shoulder": 12, "nose": 0}

        # Pose básica (solo 3 puntos clave)
        if results.pose_landmarks:
            for name in pose_map:
                lm = results.pose_landmarks.landmark[pose_map[name]]
                out.extend([lm.x, lm.y, lm.z])
        else:
            out.extend([0.0] * 9)

        # Mano izquierda
        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                out.extend([lm.x, lm.y, lm.z])
        else:
            out.extend([0.0] * 63)

        # Mano derecha
        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                out.extend([lm.x, lm.y, lm.z])
        else:
            out.extend([0.0] * 63)

        return np.array(out, dtype=np.float32)
    
    def hands_present(self, results) -> bool:
        """Verificar si hay manos presentes"""
        return (
            results.left_hand_landmarks is not None or 
            results.right_hand_landmarks is not None
        )
    
    def fix_sequence(self, seq) -> np.ndarray:
        """Ajustar secuencia a NUM_FRAMES frames"""
        seq = np.array(seq)

        if len(seq) >= self.NUM_FRAMES:
            idxs = np.linspace(0, len(seq)-1, self.NUM_FRAMES).astype(int)
            return seq[idxs]

        last = seq[-1]
        while len(seq) < self.NUM_FRAMES:
            seq = np.vstack([seq, last])

        return seq[:self.NUM_FRAMES]
    

    
    def predict_sign(self, seq30) -> Tuple[str, float]:
        """
        Predecir la seña usando la lógica de Senia.py
        
        Args:
            seq30: Secuencia de frames ajustada
            
        Returns:
            Tupla de (nombre_de_seña, confianza)
        """
        if self.model is None:
            return ("Modelo no cargado", 0.0)
        
        try:
            # El modelo espera 30 frames, así que ajustamos la secuencia
            if len(seq30) < 30:
                # Interpolar para llegar a 30 frames
                indices = np.linspace(0, len(seq30)-1, 30).astype(int)
                seq30 = seq30[indices]
            elif len(seq30) > 30:
                # Tomar submuestreo uniforme
                indices = np.linspace(0, len(seq30)-1, 30).astype(int)
                seq30 = seq30[indices]
            
            # Expandir dimensiones para el modelo: (1, 30, 135)
            seq30 = np.expand_dims(seq30, axis=0)

            # Hacer predicción
            pred = self.model.predict(seq30, verbose=0)[0]
            idx = int(np.argmax(pred))
            prob = float(pred[idx])

            # Obtener el nombre de la seña
            if idx < len(self.labels):
                sign_name = self.labels[idx]
            else:
                sign_name = f"Clase_{idx}"
            
            return sign_name, prob
            
        except Exception as e:
            print(f"Error en predicción: {str(e)}")
            return ("Error", 0.0)
    
    def detect_sign(self, frame: np.ndarray) -> Dict:
        """
        Detectar seña con modo continuo mejorado para traducción fluida
        Incluye construcción de oraciones con LLM
        """
        # Convertir BGR a RGB y procesar
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.holistic.process(rgb)
        have_hands = self.hands_present(results)
        
        current_time = time.time()
        
        # Variables para la oración
        sentence_data = {
            "signs_buffer": [],
            "raw_signs": "",
            "natural_sentence": "",
            "signs_count": 0
        }
        
        # Modo continuo mejorado
        if have_hands:
            kp = self.extract_keypoints(results)
            if kp is not None:
                self.sequence.append(kp)
                
                # Mantener solo los últimos NUM_FRAMES
                if len(self.sequence) > self.NUM_FRAMES:
                    self.sequence.pop(0)
                
                # Predecir cada cierto número de frames Y después del cooldown
                self.frames_since_last_pred += 1
                
                if (len(self.sequence) >= self.NUM_FRAMES and 
                    self.frames_since_last_pred >= 5 and  # Cada 5 frames
                    (current_time - self.last_prediction_time) >= self.cooldown_seconds):
                    
                    # Ajustar secuencia
                    seq_for_model = self.fix_sequence(self.sequence)
                    
                    # Hacer predicción
                    sign_name, prob = self.predict_sign(seq_for_model)
                    
                    # Solo actualizar si la confianza es buena
                    if prob >= self.CONFIDENCE_THRESHOLD:
                        # Evitar repetir la misma seña inmediatamente
                        if sign_name != self.predicted_label:
                            self.predicted_label = sign_name
                            self.last_prediction_time = current_time
                            self.frames_since_last_pred = 0
                            print(f"🎯 Nueva seña detectada: {sign_name} ({prob:.2%})")
                            
                            # Agregar al constructor de oraciones
                            if self.sentence_builder:
                                self.sentence_builder.add_sign(sign_name)
                    
                    # Reset del contador de frames
                    self.frames_since_last_pred = 0
        else:
            # Sin manos - limpiar secuencia gradualmente
            if len(self.sequence) > 0:
                self.sequence = []
            
            # Verificar si es momento de construir oración (pausa sin manos)
            if self.sentence_builder:
                self.sentence_builder.check_and_build_sentence()
                
        # Limpiar predicción antigua después del cooldown
        if (current_time - self.last_prediction_time) > (self.cooldown_seconds + 1):
            self.predicted_label = ""
        
        # Obtener datos de la oración
        if self.sentence_builder:
            status = self.sentence_builder._get_status()
            sentence_data = {
                "signs_buffer": status["signs_buffer"],
                "raw_signs": status["raw_signs"],
                "natural_sentence": status["current_sentence"],
                "signs_count": status["signs_count"]
            }
        
        # Estado dinámico para UI
        if have_hands:
            if len(self.sequence) < self.NUM_FRAMES:
                state_msg = f"Capturando... {len(self.sequence)}/{self.NUM_FRAMES}"
            else:
                state_msg = "Analizando seña..."
        else:
            state_msg = "Muestra tus manos para traducir"
        
        # Resultado final
        result = {
            "hand_detected": have_hands,
            "sign": self.predicted_label if self.predicted_label else None,
            "confidence": 0.8 if self.predicted_label else 0.0,
            "landmarks": None,
            "message": state_msg,
            "buffer_status": f"{len(self.sequence)}/{self.NUM_FRAMES} frames",
            "continuous_mode": True,
            # Datos de construcción de oraciones
            "sentence": sentence_data
        }
        
        return result
    
    def set_continuous_mode(self, enabled: bool):
        """Habilitar/deshabilitar modo continuo"""
        self.continuous_mode = enabled
        if enabled:
            self.cooldown_seconds = 1.5  # Más rápido
            self.NUM_FRAMES = 8  # Menos frames para más velocidad
            self.CONFIDENCE_THRESHOLD = 0.55  # Más permisivo
        else:
            self.cooldown_seconds = 3.0  # Más lento pero preciso
            self.NUM_FRAMES = 15
            self.CONFIDENCE_THRESHOLD = 0.70
    
    def draw_landmarks(self, frame: np.ndarray, draw_skeleton: bool = True) -> np.ndarray:
        """
        Dibujar landmarks en el frame
        
        Args:
            frame: Frame de video
            draw_skeleton: Si se debe dibujar el esqueleto de la mano
            
        Returns:
            Frame con landmarks dibujados
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.holistic.process(frame_rgb)
        
        if draw_skeleton:
            # Dibujar Pose
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_holistic.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4),
                    self.mp_drawing.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2)
                )
            
            # Dibujar Mano Izquierda
            if results.left_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.left_hand_landmarks,
                    self.mp_holistic.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                    self.mp_drawing.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2)
                )
                
            # Dibujar Mano Derecha
            if results.right_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    results.right_hand_landmarks,
                    self.mp_holistic.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                    self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                )
        
        return frame
    
    def __del__(self):
        """Liberar recursos"""
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()
        if hasattr(self, 'holistic') and self.holistic:
            self.holistic.close()
