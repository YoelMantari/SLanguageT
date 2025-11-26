# Traductor de Lengua de Señas

Aplicación web interactiva para traducir lengua de señas en tiempo real utilizando inteligencia artificial y visión por computadora.

## Descripción

Este proyecto permite la comunicación bidireccional entre personas que utilizan lengua de señas y personas que no la conocen. La aplicación cuenta con tres modos principales:

1. **Modo Traducción**: Detecta señas en tiempo real a través de la cámara web y las traduce a texto/voz en español.
2. **Modo Práctica**: Permite aprender y practicar señas mediante un avatar 3D que demuestra cada seña. El sistema valida si la seña realizada es correcta.
3. **Panel de Progreso**: Muestra estadísticas de uso y mejora en el aprendizaje de señas.

### Tecnologías Utilizadas

**Frontend:**

- React 18
- TypeScript
- Vite
- Three.js (renderizado 3D del avatar)
- Tailwind CSS
- Radix UI (componentes de interfaz)

**Backend:**

- Python 3.11
- FastAPI
- MediaPipe (detección de manos y poses)
- TensorFlow (clasificación de señas)
- OpenCV (procesamiento de video)
- WebSockets (comunicación en tiempo real)

## Requisitos Previos

Antes de instalar el proyecto, asegúrate de tener instalado:

- **Node.js** versión 16 o superior
- **Python 3.11** (recomendado) o Python 3.10
- **npm** o **yarn**
- **Git** (opcional, para clonar el repositorio)

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/YoelMantari/SLanguageT.git
cd sign-language-translator
```

### 2. Configurar el Frontend

```bash
# Instalar dependencias de Node.js
npm install

# O si prefieres usar yarn
yarn install
```

### 3. Configurar el Backend

#### Opción A: Usando un Entorno Virtual (Recomendado)

**En Windows (PowerShell):**

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Si PowerShell no permite ejecutar scripts, ejecuta primero:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Instalar dependencias
pip install -r backend/requirements.txt
```

**En Linux/macOS:**

```bash
# Crear entorno virtual
python3.11 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt
```

#### Opción B: Instalación Global (No Recomendado)

```bash
# Instalar dependencias directamente en el sistema
pip install -r backend/requirements.txt
```

### 4. Configurar Variables de Entorno

El backend utiliza la API de Groq para mejorar la construcción de oraciones. Crea un archivo `.env` dentro de la carpeta `backend/`:

```bash
cd backend
# En Windows
echo GROQ_API_KEY=tu_clave_api_aqui > .env

# En Linux/macOS
echo "GROQ_API_KEY=tu_clave_api_aqui" > .env
```

Para obtener una clave API de Groq:

1. Visita https://console.groq.com/
2. Crea una cuenta o inicia sesión
3. Genera una nueva API key
4. Copia la clave en el archivo `.env`

Nota: El sistema puede funcionar sin la API de Groq, pero la construcción de oraciones será más básica.

## Ejecución

Para ejecutar la aplicación, necesitas iniciar tanto el frontend como el backend simultáneamente.

### Terminal 1: Iniciar el Frontend

```bash
# Desde la raíz del proyecto
npm run dev
```

El frontend estará disponible en: http://localhost:5173

### Terminal 2: Iniciar el Backend

**En Windows (PowerShell):**

```powershell
# Activar entorno virtual (si lo usaste)
.\.venv\Scripts\Activate.ps1

# Navegar a la carpeta backend
cd backend

# Ejecutar el servidor
python app.py
```

**En Linux/macOS:**

```bash
# Activar entorno virtual (si lo usaste)
source .venv/bin/activate

# Navegar a la carpeta backend
cd backend

# Ejecutar el servidor
python app.py
```

El backend estará disponible en: http://localhost:8000

### Verificar que Todo Funciona

1. Abre tu navegador en http://localhost:5173
2. Deberías ver la pantalla principal de la aplicación
3. Selecciona "Modo Traducción" y activa la cámara
4. Inicia la detección y muestra una seña con tu mano
5. La aplicación debería detectar y traducir tu seña

## Estructura del Proyecto

```
sign-language-translator/
├── src/                          # Código fuente del frontend
│   ├── components/               # Componentes React
│   │   ├── avatar/              # Sistema de avatar 3D
│   │   │   ├── Avatar3D.jsx    # Renderizador Three.js
│   │   │   ├── AvatarAnimationPlayer.jsx
│   │   │   └── animaciones/    # Archivos JSON de señas
│   │   ├── TranslationMode.tsx # Modo traducción
│   │   ├── PracticeMode.tsx    # Modo práctica
│   │   └── ui/                 # Componentes de interfaz
│   └── App.tsx                  # Componente principal
├── backend/                      # Código fuente del backend
│   ├── app.py                   # Servidor FastAPI principal
│   ├── requirements.txt         # Dependencias Python
│   └── .env                     # Variables de entorno (crear)
├── package.json                 # Dependencias Node.js
└── README.md                    # Este archivo
```

## Solución de Problemas

### El backend no se inicia

- Verifica que estés usando Python 3.11 o 3.10
- Asegúrate de que todas las dependencias estén instaladas: `pip list`
- Si usas entorno virtual, verifica que esté activado

### La cámara no funciona

- Asegúrate de dar permisos de cámara al navegador
- Verifica que no haya otra aplicación usando la cámara
- En navegadores basados en Chromium, la cámara solo funciona en HTTPS o localhost

### El WebSocket no se conecta

- Verifica que el backend esté corriendo en http://localhost:8000
- Revisa la consola del navegador en busca de errores
- Asegúrate de que no haya firewalls bloqueando la conexión

### Error al instalar TensorFlow

- En Windows, puede ser necesario instalar Microsoft Visual C++ Redistributable
- En Linux, asegúrate de tener las bibliotecas de desarrollo instaladas
- Considera usar una versión de TensorFlow compatible con tu sistema

## Contribución

Este proyecto fue desarrollado como parte del curso de Interacción Humano-Computadora.

## Licencia

Este proyecto es de código abierto y está disponible para uso educativo.
