from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import base64
import json
from typing import Optional
import asyncio
import os
from dotenv import load_dotenv
from sign_detector import SignLanguageDetector

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="ConnectSigns API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar el detector de señas
import os
model_path = os.path.join(os.path.dirname(__file__), "..", "Traine", "modelo_senas.keras")
detector = SignLanguageDetector(model_path=model_path)

# Estado de las conexiones WebSocket activas
active_connections = []


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)


manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": "ConnectSigns API está funcionando", "status": "OK"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": detector.model is not None,
        "mediapipe_ready": detector.holistic is not None,
        "sentence_builder_ready": detector.sentence_builder is not None
    }


@app.websocket("/ws/detect")
async def websocket_detect_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint para detección en tiempo real de lenguaje de señas
    """
    await manager.connect(websocket)
    print("Cliente conectado al WebSocket")
    frame_count = 0
    
    try:
        while True:
            # Recibir datos del cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "frame":
                frame_count += 1
                print(f"\n[Frame {frame_count}] Recibido")
                
                # Decodificar la imagen base64
                image_data = message.get("image", "").split(",")[1] if "," in message.get("image", "") else message.get("image", "")
                print(f"[Frame {frame_count}] Tamaño de datos base64: {len(image_data)} caracteres")
                
                try:
                    # Convertir base64 a imagen
                    image_bytes = base64.b64decode(image_data)
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        print(f"[Frame {frame_count}] Frame decodificado: {frame.shape}")
                        
                        # Guardar frame de muestra cada 100 frames para debugging
                        if frame_count % 100 == 0:
                            import os
                            debug_dir = os.path.join(os.path.dirname(__file__), "debug_frames")
                            os.makedirs(debug_dir, exist_ok=True)
                            debug_path = os.path.join(debug_dir, f"frame_{frame_count}.jpg")
                            cv2.imwrite(debug_path, frame)
                            print(f"[DEBUG] Frame guardado en: {debug_path}")
                        
                        # Procesar el frame y detectar señas
                        result = detector.detect_sign(frame)
                        print(f"[Frame {frame_count}] Resultado: hand_detected={result.get('hand_detected')}, sign={result.get('sign')}, confidence={result.get('confidence')}")
                        
                        # Enviar resultado al cliente
                        await manager.send_personal_message({
                            "type": "detection",
                            "data": result
                        }, websocket)
                    else:
                        print(f"[Frame {frame_count}] ERROR: No se pudo decodificar el frame")
                        await manager.send_personal_message({
                            "type": "error",
                            "message": "No se pudo decodificar el frame"
                        }, websocket)
                        
                except Exception as e:
                    print(f"[Frame {frame_count}] ERROR procesando frame: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Error procesando imagen: {str(e)}"
                    }, websocket)
            
            elif message.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong"
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Cliente desconectado del WebSocket")
    except Exception as e:
        print(f"Error en WebSocket: {str(e)}")
        manager.disconnect(websocket)


@app.post("/api/detect-image")
async def detect_sign_from_image(file: UploadFile = File(...)):
    """
    Endpoint REST para detectar señas desde una imagen
    """
    try:
        # Leer la imagen
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse(
                status_code=400,
                content={"error": "No se pudo decodificar la imagen"}
            )
        
        # Detectar seña
        result = detector.detect_sign(frame)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error procesando imagen: {str(e)}"}
        )


@app.get("/api/signs")
async def get_available_signs():
    """
    Obtener lista de señas disponibles en el modelo
    """
    return {
        "signs": detector.get_available_signs(),
        "total": len(detector.get_available_signs())
    }


@app.post("/api/continuous-mode")
async def set_continuous_mode(enabled: bool = True):
    """
    Habilitar/deshabilitar modo de traducción continua
    """
    try:
        detector.set_continuous_mode(enabled)
        return {
            "success": True,
            "continuous_mode": enabled,
            "message": f"Modo continuo {'habilitado' if enabled else 'deshabilitado'}"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error configurando modo continuo: {str(e)}"}
        )


# ====== ENDPOINTS PARA CONSTRUCCIÓN DE ORACIONES ======

@app.get("/api/sentence")
async def get_sentence_status():
    """
    Obtener el estado actual del constructor de oraciones
    """
    try:
        if detector.sentence_builder:
            status = detector.sentence_builder._get_status()
            return {
                "success": True,
                "data": status
            }
        else:
            return {
                "success": False,
                "error": "Constructor de oraciones no disponible"
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error obteniendo estado: {str(e)}"}
        )


@app.post("/api/sentence/build")
async def force_build_sentence():
    """
    Forzar la construcción de una oración con las señas actuales
    """
    try:
        if detector.sentence_builder:
            sentence = detector.sentence_builder.force_build_sentence()
            return {
                "success": True,
                "sentence": sentence,
                "data": detector.sentence_builder._get_status()
            }
        else:
            return {
                "success": False,
                "error": "Constructor de oraciones no disponible"
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error construyendo oración: {str(e)}"}
        )


@app.post("/api/sentence/clear")
async def clear_sentence_buffer():
    """
    Limpiar el buffer de señas y la oración actual
    """
    try:
        if detector.sentence_builder:
            detector.sentence_builder.clear_buffer()
            return {
                "success": True,
                "message": "Buffer limpiado correctamente"
            }
        else:
            return {
                "success": False,
                "error": "Constructor de oraciones no disponible"
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error limpiando buffer: {str(e)}"}
        )


@app.delete("/api/sentence/last")
async def remove_last_sign():
    """
    Eliminar la última seña del buffer
    """
    try:
        if detector.sentence_builder:
            status = detector.sentence_builder.remove_last_sign()
            return {
                "success": True,
                "data": status
            }
        else:
            return {
                "success": False,
                "error": "Constructor de oraciones no disponible"
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error eliminando seña: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor ConnectSigns...")
    print("Modelo cargado:", detector.model is not None)
    # Usar string de importación para permitir reload
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
