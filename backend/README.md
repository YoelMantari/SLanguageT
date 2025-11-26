# Backend - ConnectSigns

Backend de la aplicación ConnectSigns para detección y traducción de lenguaje de señas en tiempo real.

## Tecnologías

- **FastAPI**: Framework web para crear la API REST y WebSocket
- **MediaPipe**: Detección de landmarks de manos
- **TensorFlow**: Modelo de machine learning para clasificación de señas
- **OpenCV**: Procesamiento de imágenes
- **NumPy**: Operaciones numéricas

## Instalación

### 1. Crear entorno virtual (si no existe)

```bash
python -m venv ../.venv
```

### 2. Activar entorno virtual

**Windows (PowerShell):**

```powershell
../.venv/Scripts/Activate.ps1
```

**Windows (CMD):**

```cmd
..\.venv\Scripts\activate.bat
```

**Linux/Mac:**

```bash
source ../.venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## Uso

### Iniciar el servidor

```bash
python app.py
```

El servidor se iniciará en `http://localhost:8000`

### Endpoints disponibles

#### REST API

- `GET /` - Verificar que el servidor está funcionando
- `GET /health` - Estado del servidor y modelo
- `POST /api/detect-image` - Detectar seña desde una imagen
- `GET /api/signs` - Obtener lista de señas disponibles

#### WebSocket

- `WS /ws/detect` - Conexión WebSocket para detección en tiempo real

## Estructura del proyecto

```
backend/
├── app.py              # Servidor FastAPI principal
├── sign_detector.py    # Clase para detección de señas
├── requirements.txt    # Dependencias de Python
└── README.md          # Este archivo
```

## Cómo funciona

### 1. Detección de manos con MediaPipe

MediaPipe detecta 21 landmarks (puntos clave) en cada mano detectada:

- Muñeca
- Dedos (pulgar, índice, medio, anular, meñique)
- Articulaciones de cada dedo

### 2. Preprocesamiento

Los landmarks se normalizan:

- Se restan las coordenadas de la muñeca (hacer la pose relativa)
- Se escalan para mantener un rango consistente

### 3. Predicción con el modelo

El modelo de TensorFlow (`modelo_senas.h5`) recibe los landmarks procesados y predice la seña correspondiente.

### 4. Estabilización

Se usa un buffer de predicciones para evitar fluctuaciones y mostrar solo predicciones con alta confianza (>70%).

## Personalización del modelo

### Ajustar las señas reconocidas

Edita el método `get_available_signs()` en `sign_detector.py` para que coincida con las clases de tu modelo:

```python
def get_available_signs(self) -> List[str]:
    return [
        "Hola", "Gracias", "Por favor",
        # ... tus señas aquí
    ]
```

### Ajustar el umbral de confianza

En `sign_detector.py`, cambia:

```python
self.confidence_threshold = 0.7  # 70% de confianza mínima
```

## Troubleshooting

### Error: "No se pudo cargar el modelo"

- Verifica que `modelo_senas.h5` existe en la raíz del proyecto
- Verifica que la ruta en `app.py` es correcta: `model_path="../modelo_senas.h5"`

### Error: "No se detectó ninguna mano"

- Asegúrate de que hay buena iluminación
- La mano debe estar visible completamente
- Ajusta `min_detection_confidence` en `sign_detector.py`

### WebSocket se desconecta

- Verifica que el frontend está conectándose a la URL correcta
- Revisa los logs del servidor para errores
- Asegúrate de que CORS está configurado correctamente

## Desarrollo

Para modo de desarrollo con recarga automática:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
