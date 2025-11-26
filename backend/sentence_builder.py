"""
Módulo para construir oraciones naturales a partir de señas detectadas
Usa Groq LLM para convertir secuencias de señas en español natural
"""

import os
import time
from typing import List, Optional
from collections import deque

# Intentar importar Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ Groq no instalado. Ejecuta: pip install groq")


class SentenceBuilder:
    """
    Construye oraciones naturales a partir de señas detectadas usando LLM
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializar el constructor de oraciones
        
        Args:
            api_key: API key de Groq (opcional, puede venir del entorno)
        """
        self.api_key = api_key or os.environ.get('GROQ_API_KEY')
        self.client = None
        
        # Buffer de señas detectadas
        self.signs_buffer: deque = deque(maxlen=20)  # Máximo 20 señas
        
        # Última oración generada
        self.current_sentence = ""
        self.last_raw_signs = ""
        
        # Control de tiempo
        self.last_sign_time = 0
        self.sentence_cooldown = 2.0  # Segundos sin señas para generar oración
        self.sentence_generated = False  # Flag para evitar repeticiones
        
        # Inicializar cliente Groq
        self._init_client()
    
    def _init_client(self):
        """Inicializar cliente Groq"""
        if not GROQ_AVAILABLE:
            print("❌ Groq no disponible")
            return
            
        if not self.api_key:
            print("⚠️ No se encontró GROQ_API_KEY")
            return
            
        try:
            self.client = Groq(api_key=self.api_key)
            print("✅ Cliente Groq inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando Groq: {e}")
            self.client = None
    
    def add_sign(self, sign: str) -> dict:
        """
        Agregar una seña detectada al buffer
        
        Args:
            sign: Nombre de la seña detectada
            
        Returns:
            Dict con el estado actual
        """
        current_time = time.time()
        
        # Evitar duplicados consecutivos
        if len(self.signs_buffer) > 0 and self.signs_buffer[-1] == sign:
            # Misma seña, solo actualizar tiempo
            self.last_sign_time = current_time
            return self._get_status()
        
        # Agregar nueva seña
        self.signs_buffer.append(sign)
        self.last_sign_time = current_time
        self.sentence_generated = False  # Resetear flag al agregar seña
        
        # Actualizar la vista de señas crudas
        self.last_raw_signs = " ".join(list(self.signs_buffer))
        
        return self._get_status()
    
    def check_and_build_sentence(self) -> dict:
        """
        Verificar si es momento de construir una oración
        
        Returns:
            Dict con el estado y posible oración generada
        """
        current_time = time.time()
        time_since_last = current_time - self.last_sign_time
        
        # Si pasó el cooldown y hay señas en el buffer
        if (time_since_last >= self.sentence_cooldown and 
            len(self.signs_buffer) >= 2 and
            self.last_sign_time > 0 and
            not self.sentence_generated):  # Verificar que no se haya generado ya
            
            # Generar oración
            signs_list = list(self.signs_buffer)
            self.current_sentence = self._generate_natural_sentence(signs_list)
            self.sentence_generated = True  # Marcar como generado
            
            # Limpiar buffer después de generar
            # self.signs_buffer.clear()  # Descomenta si quieres limpiar
            
        return self._get_status()
    
    def _generate_natural_sentence(self, signs: List[str]) -> str:
        """
        Usar LLM para convertir señas en oración natural
        
        Args:
            signs: Lista de señas detectadas
            
        Returns:
            Oración en español natural
        """
        if not self.client:
            # Sin LLM, simplemente concatenar
            return " ".join(signs).capitalize()
        
        signs_text = ", ".join(signs)
        
        prompt = f"""Actúa como un traductor directo de lenguaje de señas a español.
Convierte las siguientes señas en una ÚNICA oración simple y coherente.

Señas: [{signs_text}]

Reglas:
1. Usa un lenguaje simple, cotidiano y directo.
2. Infiere los conectores necesarios (quiero, voy, estoy, etc).
3. Ejemplo: "hola yo beber" -> "Hola, quiero beber"
4. Ejemplo: "yo casa ir" -> "Voy a casa"
5. NO des explicaciones ni variantes. Solo la oración final.

Oración traducida:"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un traductor conciso. Respondes únicamente con la oración traducida final."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Temperatura mínima para respuestas directas
                max_tokens=60
            )
            
            sentence = response.choices[0].message.content.strip()
            
            # Limpiar posibles comillas o formatos
            sentence = sentence.strip('"\'')
            
            print(f"🔄 Señas: {signs_text}")
            print(f"📝 Oración: {sentence}")
            
            return sentence
            
        except Exception as e:
            print(f"❌ Error en LLM: {e}")
            # Fallback: concatenar señas
            return " ".join(signs).capitalize()
    
    def force_build_sentence(self) -> str:
        """
        Forzar la construcción de una oración con las señas actuales
        
        Returns:
            Oración generada
        """
        if len(self.signs_buffer) == 0:
            return ""
            
        signs_list = list(self.signs_buffer)
        self.current_sentence = self._generate_natural_sentence(signs_list)
        return self.current_sentence
    
    def clear_buffer(self):
        """Limpiar el buffer de señas"""
        self.signs_buffer.clear()
        self.current_sentence = ""
        self.last_raw_signs = ""
        self.last_sign_time = 0
        self.sentence_generated = False
    
    def remove_last_sign(self) -> dict:
        """Eliminar la última seña del buffer"""
        if len(self.signs_buffer) > 0:
            self.signs_buffer.pop()
            self.last_raw_signs = " ".join(list(self.signs_buffer))
        return self._get_status()
    
    def _get_status(self) -> dict:
        """Obtener estado actual del constructor"""
        return {
            "signs_buffer": list(self.signs_buffer),
            "signs_count": len(self.signs_buffer),
            "raw_signs": self.last_raw_signs,
            "current_sentence": self.current_sentence,
            "ready_to_build": len(self.signs_buffer) >= 2
        }
    
    def get_signs_as_text(self) -> str:
        """Obtener las señas como texto simple"""
        return " ".join(list(self.signs_buffer))


# Función de utilidad para usar sin instanciar la clase
def translate_signs_to_sentence(signs: List[str], api_key: Optional[str] = None) -> str:
    """
    Traducir una lista de señas a una oración natural
    
    Args:
        signs: Lista de señas
        api_key: API key de Groq (opcional)
        
    Returns:
        Oración en español natural
    """
    builder = SentenceBuilder(api_key)
    for sign in signs:
        builder.add_sign(sign)
    return builder.force_build_sentence()


if __name__ == "__main__":
    # Test del módulo
    print("=== Test de SentenceBuilder ===\n")
    
    # Crear instancia (necesita GROQ_API_KEY en el entorno)
    builder = SentenceBuilder()
    
    # Simular detección de señas
    test_signs = ["hola", "yo", "querer", "comer"]
    
    print(f"Señas de prueba: {test_signs}\n")
    
    for sign in test_signs:
        result = builder.add_sign(sign)
        print(f"Agregado: '{sign}' -> Buffer: {result['raw_signs']}")
    
    print("\nForzando construcción de oración...")
    sentence = builder.force_build_sentence()
    print(f"\n✨ Resultado: {sentence}")
