import streamlit as st
import speech_recognition as sr
from groq import Groq
from gtts import gTTS
import os
import tempfile
import time
import re
from apikey import groq_apikey

# Configurar API key de Groq
os.environ['GROQ_API_KEY'] = groq_apikey

# Inicializar cliente Groq
@st.cache_resource
def init_groq_client():
    return Groq(api_key=groq_apikey)

# Inicializar reconocedor de voz
@st.cache_resource
def init_speech_recognizer():
    return sr.Recognizer()

def transcribe_audio_file(audio_file):
    """
    Transcribe un archivo de audio usando Groq Whisper
    """
    try:
        client = init_groq_client()
        
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(audio_file.getvalue())
            tmp_file_path = tmp_file.name
        
        # Transcribir con Groq Whisper
        with open(tmp_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(tmp_file_path, file.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )
        
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_file_path)
        except:
            pass
        
        return transcription.text
    except Exception as e:
        return f"Error en transcripción: {str(e)}"

def get_translation_response(text, direction):
    """
    Obtiene respuesta del LLM para traduccion de lenguaje de senas
    """
    client = init_groq_client()
    
    if direction == "texto_a_senas":
        prompt = f"""
        Eres un asistente de voz experto en lenguaje de señas. Traduce: "{text}".
        
        Describe brevemente los movimientos necesarios.
        Usa un tono conversacional y natural.
        Sé conciso (máximo 3 frases).
        No uses listas ni formato complejo.
        """
    else:  # senas_a_texto
        prompt = f"""
        Eres un asistente de voz experto en lenguaje de señas. Interpreta esta descripción: "{text}".
        
        Dime qué significa y sugiere mejoras si es necesario.
        Usa un tono conversacional y natural.
        Sé conciso (máximo 3 frases).
        """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres un experto en lenguaje de señas. Responde siempre en español de forma hablada, breve y natural."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al obtener respuesta: {str(e)}"

def get_feedback_response(user_message):
    """
    Genera respuestas para capturar impresiones del usuario sobre la aplicacion
    """
    client = init_groq_client()
    
    prompt = f"""
    Eres un asistente amable recopilando opiniones sobre una app de señas.
    El usuario dice: "{user_message}"
    
    Responde brevemente (1-2 frases) agradeciendo y haciendo una pregunta corta de seguimiento.
    Usa tono natural y conversacional.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres un asistente amable. Responde en español de forma breve y hablada."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al obtener respuesta: {str(e)}"

def get_educational_chat_response(user_message):
    """
    Genera respuestas para el chat educativo sobre el uso de la aplicación y el avatar
    """
    client = init_groq_client()
    
    prompt = f"""
    Eres Sara, la asistente virtual de la aplicación "Traductor de Señas Pro".
    
    Características de la aplicación que debes explicar:
    1. Traducción Voz a Señas: El usuario habla y un AVATAR 3D realiza los movimientos.
    2. Traducción Señas a Voz: La cámara detecta las manos y traduce a texto/audio.
    3. Modo Aprendizaje: El AVATAR enseña paso a paso cómo hacer gestos.
    
    El usuario dice: "{user_message}"
    
    Objetivo: Mantener un diálogo fluido (más de 2 turnos) explicando cómo usar estas funciones.
    Instrucciones:
    - Responde de forma breve y natural (como si hablaras).
    - NO uses formato Markdown (ni negritas, ni listas).
    - Enfócate en mencionar al Avatar 3D como la herramienta principal de enseñanza.
    - Termina siempre con una pregunta corta para que el usuario responda y siga la conversación.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Eres Sara, una asistente útil y conversadora. Responde en español plano, sin formato."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def clean_markdown(text):
    """Elimina formato Markdown para lectura de voz"""
    # Eliminar negritas y cursivas
    text = re.sub(r'\*\*|__|\*|_', '', text)
    # Eliminar encabezados
    text = re.sub(r'#+\s', '', text)
    # Eliminar listas (guiones o asteriscos al inicio de linea)
    text = re.sub(r'^\s*[-*]\s', '', text, flags=re.MULTILINE)
    # Eliminar enlaces
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Eliminar código
    text = re.sub(r'`', '', text)
    return text

def text_to_speech(text):
    """
    Convierte texto a voz usando gTTS
    """
    try:
        # Limpiar texto de markdown para que suene natural
        clean_text = clean_markdown(text)
        
        tts = gTTS(text=clean_text, lang='es')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            return tmp_file.name
    except Exception as e:
        st.error(f"Error en síntesis de voz: {str(e)}")
        return None

def speech_to_text():
    """
    Convierte voz a texto usando Groq Whisper (Sustituye a Google Speech Recognition)
    Captura el audio del micrófono, lo guarda temporalmente y lo envía a la API de Groq.
    """
    recognizer = init_speech_recognizer()
    status_container = st.empty()
    
    try:
        with sr.Microphone() as source:
            status_container.info("Ajustando ruido ambiental... Por favor espera.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            status_container.success("🎤 Escuchando... ¡Habla ahora!")
            # Escuchar audio
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            
            status_container.info("Transcribiendo con Groq Whisper...")
            
            # Guardar audio temporalmente para enviar a Groq
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio.get_wav_data())
                tmp_filename = tmp_file.name
            
            # Transcribir con Groq
            client = init_groq_client()
            with open(tmp_filename, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(tmp_filename, file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                )
            
            # Limpiar archivo temporal
            try:
                os.unlink(tmp_filename)
            except:
                pass
            
            status_container.empty()
            return transcription.text

    except sr.WaitTimeoutError:
        status_container.warning("No se detectó voz en el tiempo límite")
        return None
    except Exception as e:
        status_container.error(f"Error: {str(e)}")
        return None

# Configuración de la página
st.set_page_config(
    page_title="Traductor de Lenguaje de Señas",
    page_icon="🤟",
    layout="wide"
)

# Título principal
st.title("Traductor de Lenguaje de Señas con IA")
st.markdown("### Sistema inteligente para traducción bidireccional entre texto y lenguaje de señas")

# Inicializar estado de la sesión
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'conversation_started' not in st.session_state:
    st.session_state.conversation_started = False
if 'mode' not in st.session_state:
    st.session_state.mode = "Conversacion"
if 'audio_response' not in st.session_state:
    st.session_state.audio_response = None
if 'feedback_count' not in st.session_state:
    st.session_state.feedback_count = 0

# Sidebar para configuración
st.sidebar.header("Configuración")

# Selector de modo de aplicación
app_mode = st.sidebar.radio(
    "Modo de Aplicación:",
    ["Conversacion Tiempo Real", "Subir Archivo de Audio", "Feedback", "Chat Educativo"],
    key="app_mode_selector"
)

st.session_state.mode = app_mode

translation_mode = st.sidebar.selectbox(
    "Modo de traducción:",
    ["Texto a Señas", "Señas a Texto"]
)

audio_enabled = st.sidebar.checkbox("Habilitar síntesis de voz", value=True)
voice_input = st.sidebar.checkbox("Habilitar entrada por voz")

# Función para agregar mensaje al historial
def add_to_conversation(role, message):
    st.session_state.conversation_history.append({
        'role': role,
        'message': message,
        'timestamp': time.strftime("%H:%M:%S")
    })

# ==================== MODO CONVERSACION TIEMPO REAL ====================
if st.session_state.mode == "Conversacion Tiempo Real":
    st.subheader("Conversación de Voz en Tiempo Real")
    st.info("Presiona el botón, habla y el asistente te responderá con voz.")
    
    # Contenedor para mostrar el intercambio actual
    interaction_container = st.container()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🎤 Hablar con el Asistente", type="primary", use_container_width=True):
            # 1. Capturar Voz
            user_text = speech_to_text()
            
            if user_text:
                # Mostrar lo que entendió
                with interaction_container:
                    st.markdown(f"**🗣️ Tú dijiste:** {user_text}")
                
                # 2. Obtener respuesta LLM
                with st.spinner("Procesando respuesta..."):
                    direction = "texto_a_senas" if translation_mode == "Texto a Señas" else "senas_a_texto"
                    response_text = get_translation_response(user_text, direction)
                
                # Mostrar respuesta texto
                with interaction_container:
                    st.markdown(f"**🤖 Asistente:** {response_text}")
                
                # 3. Generar y reproducir Audio
                with st.spinner("Generando voz..."):
                    audio_file = text_to_speech(response_text)
                    if audio_file:
                        # Autoplay si es posible
                        st.audio(audio_file, format='audio/mp3', autoplay=True)
                        
                        # Guardar en historial para referencia
                        add_to_conversation('usuario', f"[Audio] {user_text}")
                        add_to_conversation('asistente', f"[Audio] {response_text}")

# ==================== MODO SUBIR ARCHIVO DE AUDIO ====================
elif st.session_state.mode == "Subir Archivo de Audio":
    st.subheader("Modo: Archivo de Audio a Audio")
    st.info("Sube un archivo de audio y recibe una respuesta en audio automáticamente")
    
    uploaded_file = st.file_uploader("Sube tu archivo de audio (MP3, WAV, M4A)", type=['mp3', 'wav', 'm4a', 'ogg'])
    
    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/mp3')
        
        if st.button("Procesar Audio", type="primary"):
            with st.spinner("Transcribiendo audio..."):
                # Paso 1: Transcribir audio
                transcribed_text = transcribe_audio_file(uploaded_file)
                st.success(f"Texto transcrito: {transcribed_text}")
            
            with st.spinner("Generando respuesta..."):
                # Paso 2: Obtener respuesta del LLM
                direction = "texto_a_senas" if translation_mode == "Texto a Señas" else "senas_a_texto"
                response_text = get_translation_response(transcribed_text, direction)
                st.info(f"Respuesta: {response_text}")
            
            with st.spinner("Generando audio de respuesta..."):
                # Paso 3: Convertir respuesta a audio
                audio_file = text_to_speech(response_text)
                if audio_file:
                    st.success("Audio generado correctamente")
                    st.audio(audio_file, format='audio/mp3')
                    
                    # Guardar para descarga
                    with open(audio_file, 'rb') as f:
                        st.download_button(
                            label="Descargar respuesta en audio",
                            data=f,
                            file_name="respuesta_audio.mp3",
                            mime="audio/mp3"
                        )
                    
                    # Limpiar archivo temporal
                    try:
                        os.unlink(audio_file)
                    except:
                        pass

# ==================== MODO FEEDBACK ====================
elif st.session_state.mode == "Feedback":
    st.subheader("Comparte tu Opinión")
    st.info("Queremos conocer tu experiencia con la aplicación")
    
    # Reproducir audio pendiente si existe
    if st.session_state.audio_response:
        st.audio(st.session_state.audio_response, format='audio/mp3', autoplay=True)
        st.session_state.audio_response = None
    
    # Mostrar historial de conversación de feedback
    chat_container = st.container()
    
    with chat_container:
        if len(st.session_state.conversation_history) == 0:
            welcome_msg = """
            Hola! Gracias por usar nuestro Traductor de Lenguaje de Señas.
            
            Me encantaría conocer tu opinión sobre la aplicación:
            - ¿Qué te pareció la experiencia?
            - ¿Fue fácil de usar?
            - ¿Qué mejorarías?
            - ¿Cumplió con tus expectativas?
            
            Cuéntame, ¿cómo ha sido tu experiencia?
            """
            add_to_conversation('asistente', welcome_msg)
        
        for chat in st.session_state.conversation_history:
            if chat['role'] == 'usuario':
                st.write(f"**Tú ({chat['timestamp']}):** {chat['message']}")
            else:
                st.write(f"**Asistente ({chat['timestamp']}):** {chat['message']}")
            st.write("---")
    
    # Entrada de feedback
    input_method = st.radio("Método de entrada:", ["Voz (Tiempo Real)", "Texto"], horizontal=True, key="feedback_input_method")

    if input_method == "Texto":
        user_feedback = st.text_area("Tu opinión:", height=100, key="feedback_input")
        
        if st.button("Enviar", type="primary"):
            if user_feedback:
                add_to_conversation('usuario', user_feedback)
                st.session_state.feedback_count += 1
                
                # Generar respuesta de seguimiento
                if st.session_state.feedback_count < 4:
                    response = get_feedback_response(user_feedback)
                else:
                    response = """
                    Muchas gracias por compartir tus valiosas opiniones! 
                    Tu feedback es muy importante para nosotros y nos ayudará a mejorar la aplicación.
                    
                    Hemos registrado todos tus comentarios. ¿Hay algo más que quieras añadir?
                    """
                
                add_to_conversation('asistente', response)
                
                # Audio si está habilitado
                if audio_enabled:
                    with st.spinner("Generando audio..."):
                        audio_file = text_to_speech(response)
                        if audio_file:
                            with open(audio_file, 'rb') as f:
                                st.session_state.audio_response = f.read()
                            try:
                                os.unlink(audio_file)
                            except:
                                pass
                
                st.rerun()
    
    else: # Voz Tiempo Real
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🎤 Hablar para dar Feedback", type="primary", use_container_width=True):
                user_feedback = speech_to_text()
                
                if user_feedback:
                    add_to_conversation('usuario', f"[Audio] {user_feedback}")
                    st.session_state.feedback_count += 1
                    
                    with st.spinner("Procesando tu opinión..."):
                        if st.session_state.feedback_count < 4:
                            response = get_feedback_response(user_feedback)
                        else:
                            response = """
                            Muchas gracias por compartir tus valiosas opiniones! 
                            Tu feedback es muy importante para nosotros y nos ayudará a mejorar la aplicación.
                            
                            Hemos registrado todos tus comentarios. ¿Hay algo más que quieras añadir?
                            """
                    
                    add_to_conversation('asistente', response)
                    
                    with st.spinner("Generando respuesta de voz..."):
                        audio_file = text_to_speech(response)
                        if audio_file:
                            with open(audio_file, 'rb') as f:
                                st.session_state.audio_response = f.read()
                            try:
                                os.unlink(audio_file)
                            except:
                                pass
                    
                    st.rerun()

# ==================== MODO CONVERSACION ====================
else:  # Modo Chat Educativo
    st.subheader("Chat Educativo con el Asistente")
    st.info("Conversa con Sara para aprender sobre el Avatar 3D y las funciones de la app.")

    # Reproducir audio pendiente si existe (después de rerun)
    if st.session_state.audio_response:
        st.audio(st.session_state.audio_response, format='audio/mp3', autoplay=True)
        st.session_state.audio_response = None

    # Contenedor para el chat
    chat_container = st.container()

    with chat_container:
        # Mostrar historial de conversación
        for chat in st.session_state.conversation_history:
            if chat['role'] == 'usuario':
                st.write(f"**Tú ({chat['timestamp']}):** {chat['message']}")
            else:
                st.write(f"**Asistente ({chat['timestamp']}):** {chat['message']}")
            st.write("---")

    # Iniciar conversación si es la primera vez
    if not st.session_state.conversation_started:
        welcome_message = """
        ¡Hola! Soy Sara, tu asistente de aprendizaje de señas.
        
        Puedo ayudarte a traducir voz a señas, señas a voz, y enseñarte gestos con nuestro Avatar 3D interactivo.
        
        ¿Qué te gustaría aprender hoy?
        """
        add_to_conversation('asistente', welcome_message)
        st.session_state.conversation_started = True
        st.rerun()

    # Área de entrada de texto
    st.subheader("Tu mensaje")

    # Entrada por voz o texto
    input_method = st.radio("Método de entrada:", ["Voz (Tiempo Real)", "Texto"], horizontal=True)

    user_input = ""

    if input_method == "Texto":
        user_input = st.text_area("Escribe tu mensaje:", height=100, key="text_input")
        if st.button("Enviar Mensaje", type="primary"):
            if user_input:
                # Procesar entrada de texto
                add_to_conversation('usuario', user_input)
                
                # Lógica de respuesta
                if any(palabra in user_input.lower() for palabra in ['nombre', 'me llamo', 'soy']):
                    if 'me llamo' in user_input.lower() or 'soy' in user_input.lower():
                        name_part = user_input.lower().split('me llamo')[-1] if 'me llamo' in user_input.lower() else user_input.lower().split('soy')[-1]
                        st.session_state.user_name = name_part.strip()
                    
                    response = f"""
                    ¡Hola! Soy Sara, tu asistente virtual. Me alegra conocerte.
                    
                    Puedo ayudarte a traducir voz a señas con nuestro Avatar 3D, o interpretar señas a voz.
                    
                    ¿Te gustaría ver cómo el avatar te enseña alguna palabra?
                    """
                else:
                    response = get_educational_chat_response(user_input)
                
                add_to_conversation('asistente', response)
                
                if audio_enabled:
                    with st.spinner("Generando audio..."):
                        audio_file = text_to_speech(response)
                        if audio_file:
                            with open(audio_file, 'rb') as f:
                                st.session_state.audio_response = f.read()
                            try:
                                os.unlink(audio_file)
                            except:
                                pass
                st.rerun()

    else: # Voz Tiempo Real
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🎤 Hablar con Sara", type="primary", use_container_width=True):
                # 1. Capturar Voz
                user_text = speech_to_text()
                
                if user_text:
                    # Agregar al historial
                    add_to_conversation('usuario', f"[Audio] {user_text}")
                    
                    # 2. Obtener respuesta
                    with st.spinner("Sara está pensando..."):
                        if any(palabra in user_text.lower() for palabra in ['nombre', 'me llamo', 'soy']):
                            if 'me llamo' in user_text.lower() or 'soy' in user_text.lower():
                                name_part = user_text.lower().split('me llamo')[-1] if 'me llamo' in user_text.lower() else user_text.lower().split('soy')[-1]
                                st.session_state.user_name = name_part.strip()
                            
                            response = f"""
                            ¡Hola! Soy Sara, tu asistente virtual. Me alegra conocerte.
                            
                            Puedo ayudarte a traducir voz a señas con nuestro Avatar 3D, o interpretar señas a voz.
                            
                            ¿Te gustaría ver cómo el avatar te enseña alguna palabra?
                            """
                        else:
                            response = get_educational_chat_response(user_text)
                    
                    # Agregar respuesta al historial
                    add_to_conversation('asistente', response)
                    
                    # 3. Generar Audio y guardar en session_state
                    with st.spinner("Generando voz..."):
                        audio_file = text_to_speech(response)
                        if audio_file:
                            with open(audio_file, 'rb') as f:
                                st.session_state.audio_response = f.read()
                            try:
                                os.unlink(audio_file)
                            except:
                                pass
                    
                    st.rerun()

# Información adicional en sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Información del Sistema")
st.sidebar.markdown(f"**Modo actual:** {translation_mode}")
st.sidebar.markdown(f"**Audio:** {'Habilitado' if audio_enabled else 'Deshabilitado'}")
st.sidebar.markdown(f"**Entrada por voz:** {'Habilitada' if voice_input else 'Deshabilitada'}")

# Botón para limpiar conversación
if st.sidebar.button("Limpiar Conversación"):
    st.session_state.conversation_history = []
    st.session_state.conversation_started = False
    st.rerun()

# Footer
st.markdown("---")
st.markdown("**Proyecto Lab12 - IHC 2025 | Traductor de Lenguaje de Señas con IA**")