# 🤟 ConnectSigns - Traductor de Lenguaje de Señas en Tiempo Real

![Python](https://img.shields.io/badge/Python-3.11-blue)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.17.0-orange)
![React](https://img.shields.io/badge/React-18.3.1-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688)

ConnectSigns es una aplicación de traducción bidireccional de lenguaje de señas que utiliza inteligencia artificial para reconocer señas en tiempo real mediante la cámara web y convertirlas a texto/voz, así como mostrar señas mediante un avatar 3D.

## ✨ Características

- 🎥 **Reconocimiento en Tiempo Real**: Detecta 18 señas del lenguaje de señas peruano mediante la cámara web
- 🤖 **Avatar 3D Interactivo**: Visualización de señas mediante un avatar animado en 3D
- 💬 **Construcción de Oraciones**: Construcción automática de oraciones gramaticalmente correctas a partir de señas detectadas
- 🎓 **Modo Práctica**: Sistema de lecciones para aprender señas paso a paso
- 📊 **Dashboard de Progreso**: Seguimiento de avances y logros
- 🔄 **Traducción Bidireccional**: Seña a texto/voz y texto a seña

## 🎯 Señas Soportadas

El modelo reconoce las siguientes 18 señas:
- Saludos: `hola`, `gracias`, `adios`
- Pronombres: `yo`, `tu`
- Acciones: `comer`, `beber`, `ir`, `venir`, `espera`, `querer`
- Lugares/Necesidades: `casa`, `baño`, `ayuda`, `dolor`
- Cortesía: `porfavor`
- Interrogativos: `donde`
- Artículos: `el`

## 🛠️ Tecnologías

### Backend
- **FastAPI**: Framework web de alto rendimiento
- **TensorFlow 2.17.0**: Modelo de deep learning para reconocimiento de señas
- **Keras 3.10.0**: API de alto nivel para redes neuronales
- **MediaPipe**: Detección de landmarks de manos y pose
- **OpenCV**: Procesamiento de video en tiempo real
- **WebSockets**: Comunicación bidireccional en tiempo real

### Frontend
- **React 18.3.1**: Framework UI
- **TypeScript**: Tipado estático
- **Vite**: Build tool y dev server
- **Tailwind CSS**: Estilos
- **Three.js**: Renderizado del avatar 3D

### Modelo de IA
- **Arquitectura**: Bidirectional LSTM
- **Capas**: Masking → BiLSTM(256) → Dropout → BiLSTM(128) → Dropout → Dense(256) → Dense(128) → Dense(18)
- **Parámetros**: 1,560,210
- **Input**: (30 frames, 135 features) - Secuencias de landmarks de MediaPipe
- **Output**: 18 clases de señas

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.11** (IMPORTANTE: Debe ser exactamente versión 3.11.x)
- **Node.js 18+** y **npm 9+**
- **Git** (para clonar el repositorio)
- **Cámara web** (para detección de señas en tiempo real)

### Verificar versiones instaladas:

```bash
# Verificar Python
python --version  # Debe mostrar Python 3.11.x

# Verificar Node.js y npm
node --version    # Debe ser 18.x o superior
npm --version     # Debe ser 9.x o superior
```

---

## 🚀 Instalación

### 1️⃣ Clonar el Repositorio

```bash
git clone https://github.com/YoelMantari/SLanguageT.git
cd SLanguageT
```

### 2️⃣ Configurar el Backend (Python)

#### Crear entorno virtual con Python 3.11

**Windows (PowerShell):**
```powershell
# Asegúrate de usar Python 3.11
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
# Asegúrate de usar Python 3.11
python3.11 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate
```

#### Instalar dependencias de Python

```bash
# El entorno virtual debe estar activado (verás (.venv) en el prompt)
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias principales instaladas:**
- `tensorflow==2.17.0` - Framework de deep learning
- `keras==3.10.0` - API de redes neuronales
- `fastapi==0.109.0` - Framework web
- `uvicorn[standard]==0.27.0` - Servidor ASGI
- `mediapipe==0.10.9` - Detección de landmarks
- `opencv-python==4.9.0.80` - Procesamiento de video
- `numpy==1.26.4` - Computación numérica

> ⚠️ **IMPORTANTE**: La instalación puede tardar 5-10 minutos debido a TensorFlow y sus dependencias.

#### Verificar instalación del modelo

El modelo `modelo_senas.keras` debe estar en la carpeta `Traine/`:

```bash
# Windows
dir Traine\modelo_senas.keras

# Linux/macOS
ls -lh Traine/modelo_senas.keras
```

Si existe, deberías ver un archivo de aproximadamente 19-20 MB.

### 3️⃣ Configurar el Frontend (React + Vite)

```bash
# Instalar dependencias de Node.js
npm install
```

**Dependencias principales instaladas:**
- `react` y `react-dom` - Framework UI
- `typescript` - Tipado estático
- `vite` - Build tool
- `tailwindcss` - Estilos
- `three` - Avatar 3D
- `lucide-react` - Iconos

---

## ▶️ Ejecución del Proyecto

El proyecto requiere ejecutar **2 servidores simultáneamente**: backend (Python) y frontend (React).

### Opción 1: Usando 2 Terminales (Recomendado)

#### Terminal 1 - Backend (FastAPI)

```bash
# Activar entorno virtual Python 3.11
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Navegar a la carpeta backend
cd backend

# Iniciar servidor FastAPI
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

**Salida esperada:**
```
INFO:     Will watch for changes in these directories: ['D:\...\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
Labels cargados: 18 clases
✅ Modelo cargado exitosamente
📊 Input shape: (None, 30, 135)
📊 Output shape: (None, 18)
INFO:     Application startup complete.
```

El backend estará disponible en: **http://127.0.0.1:8000**

#### Terminal 2 - Frontend (Vite)

**Abre una NUEVA terminal** (sin cerrar la anterior):

```bash
# Desde la raíz del proyecto
npm run dev
```

**Salida esperada:**
```
VITE v6.3.5  ready in XXX ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

El frontend estará disponible en: **http://localhost:3000** (o puerto 3001 si 3000 está ocupado)

### Opción 2: Script Único (Avanzado)

**Windows (PowerShell):**
```powershell
# En la raíz del proyecto
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; ..\\.venv\\Scripts\\Activate.ps1; uvicorn app:app --reload --host 127.0.0.1 --port 8000"
npm run dev
```

**Linux/macOS:**
```bash
# Backend en background
cd backend && source ../.venv/bin/activate && uvicorn app:app --reload --host 127.0.0.1 --port 8000 &

# Frontend en foreground
cd .. && npm run dev
```

---

## 🎮 Uso de la Aplicación

1. **Abrir el navegador** en `http://localhost:3000`

2. **Modo Traducción** (Seña a Texto):
   - Clic en "Traducir Ahora"
   - Permitir acceso a la cámara
   - Activar detección con el botón "Iniciar Detección"
   - Realizar señas frente a la cámara
   - Las señas detectadas se acumulan y forman oraciones automáticamente

3. **Modo Práctica**:
   - Clic en "Practicar Señas"
   - Seleccionar una lección
   - Ver el avatar 3D realizar la seña
   - Replicar la seña frente a la cámara
   - Recibir feedback instantáneo

4. **Dashboard de Progreso**:
   - Ver estadísticas de aprendizaje
   - Consultar logros desbloqueados
   - Racha de días consecutivos

---

## 🏗️ Estructura del Proyecto

```
SLanguageT/
├── backend/                      # Backend FastAPI
│   ├── app.py                   # Servidor principal + WebSocket
│   ├── sign_detector.py         # Detector de señas con MediaPipe + TensorFlow
│   └── sentence_builder.py      # Constructor de oraciones
│
├── src/                         # Frontend React
│   ├── main.tsx                # Entry point
│   ├── App.tsx                 # Componente principal
│   └── components/
│       ├── HomePage.tsx        # Página de inicio
│       ├── TranslationMode.tsx # Modo traducción en tiempo real
│       ├── PracticeMode.tsx    # Modo práctica con lecciones
│       ├── ProgressDashboard.tsx # Dashboard de progreso
│       ├── BottomTabBar.tsx    # Navegación inferior
│       ├── avatar/             # Avatar 3D
│       │   ├── Avatar3D.jsx
│       │   ├── AvatarAnimationPlayer.jsx
│       │   └── animaciones/    # Archivos JSON de animaciones
│       └── ui/                 # Componentes UI reutilizables
│
├── Traine/                      # Modelo de IA
│   ├── modelo_senas.keras      # Modelo entrenado (19 MB)
│   └── labels.json             # Etiquetas de las 18 señas
│
├── .venv/                       # Entorno virtual Python (generado)
├── node_modules/                # Dependencias Node.js (generado)
├── package.json                 # Configuración npm
├── requirements.txt             # Dependencias Python
├── vite.config.ts              # Configuración Vite
├── tailwind.config.js          # Configuración Tailwind
└── tsconfig.json               # Configuración TypeScript
```

---

## 🔧 Solución de Problemas

### ❌ Error: "Python version 3.11 required"

**Causa**: No estás usando Python 3.11

**Solución**:
```bash
# Verificar versión
python --version

# Si es diferente a 3.11.x, instalar Python 3.11 desde:
# https://www.python.org/downloads/release/python-3110/
```

### ❌ Error: "No module named 'tensorflow'"

**Causa**: El entorno virtual no está activado o las dependencias no se instalaron

**Solución**:
```bash
# Activar entorno virtual
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### ❌ Error: "Could not load model: Unrecognized keyword arguments"

**Causa**: Versión incorrecta de TensorFlow o Keras

**Solución**:
```bash
# Verificar versiones
pip show tensorflow keras

# Deben ser exactamente:
# tensorflow==2.17.0
# keras==3.10.0

# Si son diferentes, reinstalar:
pip uninstall tensorflow keras -y
pip install tensorflow==2.17.0 keras==3.10.0
```

### ❌ Error: "Port 8000 is already in use"

**Causa**: El puerto 8000 está ocupado

**Solución**:
```bash
# Opción 1: Cambiar puerto
uvicorn app:app --reload --host 127.0.0.1 --port 8001

# Opción 2: Matar proceso en Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Opción 3: Matar proceso en Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### ❌ Error: "Camera permission denied"

**Causa**: El navegador no tiene permisos de cámara

**Solución**:
1. Chrome: `chrome://settings/content/camera` → Permitir
2. Asegurarse de usar HTTPS o localhost (HTTP funciona solo en localhost)
3. Verificar que ninguna otra aplicación esté usando la cámara

### ❌ Error: "WebSocket connection failed"

**Causa**: El backend no está corriendo o hay problema de CORS

**Solución**:
```bash
# Verificar que el backend esté corriendo
curl http://127.0.0.1:8000/health

# Debe responder:
# {"status":"healthy","model_loaded":true}

# Si no responde, reiniciar backend
```

### ❌ Señas no se detectan (hand_detected=False)

**Causa**: Iluminación pobre o manos fuera del encuadre

**Solución**:
- Mejorar iluminación
- Acercar las manos a la cámara
- Fondo simple y contrastante
- Palmas visibles hacia la cámara

---

## 📊 API Endpoints

### REST Endpoints

#### `GET /health`
Verificar estado del servidor y modelo

**Respuesta:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

#### `POST /api/detect-image`
Detectar seña desde imagen estática

**Request:**
- Tipo: `multipart/form-data`
- Campo: `file` (imagen JPG/PNG)

**Respuesta:**
```json
{
  "hand_detected": true,
  "sign": "hola",
  "confidence": 0.95
}
```

### WebSocket Endpoint

#### `WS /ws/detect`
Detección en tiempo real

**Enviar (cliente → servidor):**
```json
{
  "type": "frame",
  "data": "base64_encoded_image"
}
```

**Recibir (servidor → cliente):**
```json
{
  "hand_detected": true,
  "sign": "hola",
  "confidence": 0.95,
  "sentence": "Hola, yo quiero comer"
}
```

---

## 🧪 Testing

```bash
# Verificar que el modelo cargue correctamente
cd backend
python -c "from sign_detector import SignLanguageDetector; d = SignLanguageDetector('../Traine/modelo_senas.keras'); print('✅ OK')"

# Verificar versiones de dependencias críticas
python -c "import tensorflow as tf; import keras; print(f'TF: {tf.__version__}, Keras: {keras.__version__}')"
# Debe mostrar: TF: 2.17.0, Keras: 3.10.0
```

---

## 📝 Notas Importantes

1. **Python 3.11 es OBLIGATORIO**: El modelo fue entrenado y guardado con TensorFlow 2.17.0 que requiere Python 3.11. Versiones superiores o inferiores pueden causar incompatibilidades.

2. **Activar entorno virtual**: SIEMPRE activa el entorno virtual antes de ejecutar comandos de Python.

3. **Orden de inicio**: Inicia primero el backend, luego el frontend.

4. **Requisitos de hardware**:
   - Mínimo 8GB RAM
   - Procesador con soporte AVX (la mayoría de CPUs modernas)
   - Cámara web con resolución 640x480 o superior

5. **Navegadores soportados**:
   - Chrome/Edge (recomendado)
   - Firefox
   - Safari (puede tener limitaciones con WebSockets)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es software educativo desarrollado para fines académicos.

---

## 👥 Autores

- **Yoel Mantari** - [@YoelMantari](https://github.com/YoelMantari)

---

## 🙏 Agradecimientos

- MediaPipe por la detección de landmarks
- TensorFlow/Keras por el framework de deep learning
- Comunidad de lenguaje de señas peruano

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa la sección [Solución de Problemas](#-solución-de-problemas)
2. Verifica que estés usando Python 3.11
3. Abre un issue en GitHub con:
   - Descripción del problema
   - Logs completos del error
   - Versiones de Python, TensorFlow y Keras
   - Sistema operativo

---

**⭐ Si te resultó útil este proyecto, considera darle una estrella en GitHub!**
