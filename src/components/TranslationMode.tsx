import { useState, useRef, useEffect } from "react";
import {
  ArrowLeft,
  Camera,
  Mic,
  Volume2,
  Send,
  VideoOff,
  Video,
} from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

interface TranslationModeProps {
  onBack: () => void;
}

export function TranslationMode({ onBack }: TranslationModeProps) {
  // Referencias
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const isDetectingRef = useRef<boolean>(false);
  const detectionIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Estado para Seña a Voz/Texto (mitad superior)
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [translatedText, setTranslatedText] = useState("");
  const [detectionStatus, setDetectionStatus] = useState("");
  const [confidence, setConfidence] = useState(0);

  // Estado para Voz/Texto a Seña (mitad inferior)
  const [inputText, setInputText] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [showAvatarSigns, setShowAvatarSigns] = useState(false);

  // Constantes
  const WS_URL = "ws://localhost:8000/ws/detect";
  const DETECTION_INTERVAL = 100; // ms entre detecciones

  // Inicializar/detener cámara
  const toggleCamera = async () => {
    if (isCameraOn) {
      stopCamera();
    } else {
      await startCamera();
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: 640,
          height: 480,
          facingMode: "user",
        },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;

        // Asegurarse de que el video se reproduzca
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch((err) => {
            console.error("Error playing video:", err);
          });
        };

        setIsCameraOn(true);
        setDetectionStatus("Cámara iniciada");
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
      setDetectionStatus("Error al acceder a la cámara");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraOn(false);
    setIsDetecting(false);
    setDetectionStatus("");
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  // Conectar/desconectar WebSocket
  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log("✓ WebSocket conectado");
      setDetectionStatus("Conectado al servidor");
    };

    ws.onmessage = (event) => {
      console.log("📩 Mensaje recibido del servidor:", event.data);
      try {
        const data = JSON.parse(event.data);
        console.log("📦 Datos parseados:", data);

        if (data.type === "detection") {
          const result = data.data;
          console.log("🔍 Resultado de detección:", result);

          // Actualizar estado basado en el resultado
          if (result.hand_detected) {
            if (result.sign && result.confidence > 0.7) {
              console.log(
                `✓✓✓ SEÑA DETECTADA: ${result.sign} (${result.confidence})`
              );
              setTranslatedText(result.sign);
              setConfidence(result.confidence);
              setDetectionStatus(`✓ Seña: ${result.sign}`);
            } else if (result.buffer_status) {
              setDetectionStatus(`🖐️ Mano detectada - ${result.buffer_status}`);
            } else {
              setDetectionStatus(result.message || "🖐️ Mano detectada");
            }
          } else {
            setDetectionStatus(
              "❌ No se detecta mano - Acerca tu mano a la cámara"
            );
          }
        }
      } catch (error) {
        console.error("❌ Error procesando mensaje:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setDetectionStatus("Error de conexión");
    };

    ws.onclose = () => {
      console.log("WebSocket desconectado");
      setDetectionStatus("Desconectado del servidor");
    };

    wsRef.current = ws;
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  // Enviar frame al servidor
  const sendFrameToServer = () => {
    if (!videoRef.current || !canvasRef.current || !wsRef.current) {
      console.log(
        "❌ No se puede enviar frame: video, canvas o ws no disponible"
      );
      return;
    }
    if (wsRef.current.readyState !== WebSocket.OPEN) {
      console.log("❌ WebSocket no está abierto:", wsRef.current.readyState);
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    if (!context || video.readyState !== video.HAVE_ENOUGH_DATA) {
      console.log("❌ Video no tiene suficientes datos:", video.readyState);
      return;
    }

    // Dibujar frame actual en el canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    // Convertir a base64
    const imageData = canvas.toDataURL("image/jpeg", 0.8);
    console.log("📸 Enviando frame:", {
      width: canvas.width,
      height: canvas.height,
      dataSize: imageData.length,
    });

    // Enviar al servidor
    try {
      wsRef.current.send(
        JSON.stringify({
          type: "frame",
          image: imageData,
        })
      );
      console.log("✓ Frame enviado");
    } catch (error) {
      console.error("❌ Error enviando frame:", error);
    }
  };

  // Loop de detección usando setInterval
  const startDetectionLoop = () => {
    console.log("🔄 Iniciando loop con setInterval...");

    // Limpiar intervalo anterior si existe
    if (detectionIntervalRef.current) {
      clearInterval(detectionIntervalRef.current);
    }

    // Crear nuevo intervalo
    detectionIntervalRef.current = setInterval(() => {
      if (!isDetectingRef.current) {
        console.log("⏹ Deteniendo intervalo - isDetectingRef es false");
        if (detectionIntervalRef.current) {
          clearInterval(detectionIntervalRef.current);
          detectionIntervalRef.current = null;
        }
        return;
      }

      console.log("📸 Tick del intervalo - enviando frame...");
      sendFrameToServer();
    }, DETECTION_INTERVAL);

    console.log("✓ Intervalo creado:", detectionIntervalRef.current);
  };

  // Iniciar/detener detección
  const toggleDetection = () => {
    console.log("=== toggleDetection llamado ===");
    console.log("isCameraOn:", isCameraOn);
    console.log("isDetecting actual:", isDetecting);

    if (!isCameraOn) {
      console.log("❌ Cámara no está encendida");
      setDetectionStatus("Primero enciende la cámara");
      return;
    }

    if (isDetecting) {
      console.log("⏹ Deteniendo detección...");
      setIsDetecting(false);
      isDetectingRef.current = false;

      // Limpiar intervalo
      if (detectionIntervalRef.current) {
        clearInterval(detectionIntervalRef.current);
        detectionIntervalRef.current = null;
      }

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      disconnectWebSocket();
      setDetectionStatus("Detección detenida");
    } else {
      console.log("▶ Iniciando detección...");
      console.log(
        "Estableciendo isDetecting = true y isDetectingRef.current = true"
      );
      setIsDetecting(true);
      isDetectingRef.current = true;
      setTranslatedText("");

      console.log("Conectando WebSocket...");
      connectWebSocket();

      // Esperar un poco para que el WebSocket se conecte y luego iniciar loop
      setTimeout(() => {
        console.log("🚀 Iniciando loop de detección...");
        console.log("isDetectingRef.current:", isDetectingRef.current);
        console.log("wsRef.current:", wsRef.current);
        console.log("wsRef.current?.readyState:", wsRef.current?.readyState);
        startDetectionLoop();
      }, 1500);
    }
  };

  // Cleanup al desmontar
  useEffect(() => {
    return () => {
      isDetectingRef.current = false;
      if (detectionIntervalRef.current) {
        clearInterval(detectionIntervalRef.current);
      }
      stopCamera();
      disconnectWebSocket();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Funciones para Seña a Voz/Texto
  const handlePlayVoice = () => {
    if (!translatedText) return;

    // Usar Web Speech API para text-to-speech
    const utterance = new SpeechSynthesisUtterance(translatedText);
    utterance.lang = "es-ES";
    window.speechSynthesis.speak(utterance);
  };

  // Funciones para Voz/Texto a Seña
  const handleVoiceInput = () => {
    setIsListening(true);

    // Simular captura de voz (puedes implementar Web Speech API aquí)
    setTimeout(() => {
      setInputText("Muy bien, gracias. ¿Y tú?");
      setIsListening(false);
    }, 2000);
  };

  const handleShowSigns = () => {
    if (!inputText.trim()) return;

    setShowAvatarSigns(true);
    // Simular animación del avatar haciendo las señas
    setTimeout(() => {
      setShowAvatarSigns(false);
      setInputText("");
    }, 4000);
  };

  return (
    <div className="flex flex-col h-full bg-white pb-16">
      {/* Canvas oculto para capturar frames */}
      <canvas ref={canvasRef} style={{ display: "none" }} />

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 pt-12 pb-4 flex items-center gap-4 shrink-0">
        <Button
          variant="ghost"
          size="icon"
          onClick={onBack}
          className="rounded-full"
          aria-label="Volver"
        >
          <ArrowLeft size={24} />
        </Button>
        <h2 className="text-lg font-semibold">Traducción en Tiempo Real</h2>
      </div>

      {/* ========== MITAD SUPERIOR: SEÑA A VOZ/TEXTO ========== */}
      <div className="flex flex-col h-1/2 border-b-4 border-[#F2F2F7]">
        {/* Vista de Cámara */}
        <div className="relative flex-1 bg-gradient-to-br from-gray-800 to-gray-900 overflow-hidden">
          {/* Video de la cámara */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="absolute inset-0 w-full h-full object-cover scale-x-[-1]"
            style={{ display: isCameraOn ? "block" : "none" }}
          />

          {/* Placeholder cuando la cámara está apagada */}
          {!isCameraOn && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-white/60">
                <VideoOff size={48} className="mx-auto mb-2" />
                <p className="text-sm">Cámara apagada</p>
              </div>
            </div>
          )}

          {/* Indicador de detección activa */}
          {isDetecting && (
            <div className="absolute inset-0 border-4 border-[#50E3C2] animate-pulse pointer-events-none" />
          )}

          {/* Estado de detección */}
          {detectionStatus && (
            <div className="absolute top-4 left-4 right-4">
              <div className="bg-black/70 text-white px-4 py-3 rounded-lg text-sm backdrop-blur-sm">
                <div className="flex items-center justify-between">
                  <span>{detectionStatus}</span>
                  {confidence > 0 && (
                    <span className="ml-2 text-[#50E3C2] font-bold">
                      {Math.round(confidence * 100)}%
                    </span>
                  )}
                </div>
                {!detectionStatus.includes("mano") &&
                  !detectionStatus.includes("Conectado") && (
                    <div className="mt-2 text-xs text-yellow-300">
                      💡 Asegúrate de que tu mano esté bien visible y con buena
                      iluminación
                    </div>
                  )}
              </div>
            </div>
          )}
        </div>

        {/* Área de Salida de Texto */}
        <div className="shrink-0 px-4 py-3 bg-white">
          <div className="min-h-[60px] bg-[#F2F2F7] rounded-xl p-3 flex items-center justify-between">
            {translatedText ? (
              <>
                <p className="flex-1 font-medium">{translatedText}</p>
                <Button
                  onClick={handlePlayVoice}
                  size="icon"
                  className="ml-3 shrink-0 bg-[#50E3C2] hover:bg-[#40D3B2] text-white rounded-full"
                  aria-label="Reproducir voz"
                >
                  <Volume2 size={20} />
                </Button>
              </>
            ) : (
              <p className="text-[#8E8E93] text-sm">
                La traducción aparecerá aquí
              </p>
            )}
          </div>
        </div>

        {/* Controles de cámara */}
        <div className="shrink-0 px-4 pb-3 space-y-2">
          <div className="flex gap-2">
            <Button
              onClick={toggleCamera}
              className={`flex-1 py-4 ${
                isCameraOn
                  ? "bg-red-500 hover:bg-red-600"
                  : "bg-[#4A90E2] hover:bg-[#3A7BC8]"
              } text-white rounded-xl flex items-center justify-center gap-2`}
            >
              {isCameraOn ? (
                <>
                  <VideoOff size={20} />
                  Detener Cámara
                </>
              ) : (
                <>
                  <Video size={20} />
                  Iniciar Cámara
                </>
              )}
            </Button>
          </div>

          <Button
            onClick={toggleDetection}
            disabled={!isCameraOn}
            className={`w-full py-5 ${
              isDetecting
                ? "bg-orange-500 hover:bg-orange-600"
                : "bg-[#50E3C2] hover:bg-[#40D3B2]"
            } text-white rounded-xl flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <Camera size={24} />
            {isDetecting ? "Detener Detección" : "Iniciar Detección"}
          </Button>
        </div>
      </div>

      {/* ========== MITAD INFERIOR: VOZ/TEXTO A SEÑA ========== */}
      <div className="flex flex-col h-1/2">
        {/* Vista de Avatar para mostrar señas */}
        <div className="relative flex-1 bg-gradient-to-br from-[#50E3C2]/10 to-[#4A90E2]/10">
          {showAvatarSigns ? (
            <div className="absolute inset-0 bg-gradient-to-br from-[#50E3C2] to-[#4A90E2] flex items-center justify-center animate-in fade-in duration-300">
              <div className="text-white text-center">
                <div className="w-32 h-32 bg-white/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-6xl animate-bounce">👋</span>
                </div>
                <p>Avatar mostrando señas...</p>
                <p className="text-sm text-white/80 mt-2">"{inputText}"</p>
              </div>
            </div>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-[#8E8E93]">
                <div className="text-5xl mb-2">🤖</div>
                <p className="text-sm">El avatar mostrará las señas aquí</p>
              </div>
            </div>
          )}
        </div>

        {/* Panel de Control: Entrada de Texto/Voz */}
        <div className="shrink-0 px-4 py-3 bg-white space-y-3">
          {/* Campo de texto con botón de micrófono */}
          <div className="flex gap-2">
            <Input
              placeholder="Escribe tu mensaje..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleShowSigns();
                }
              }}
              className="flex-1 h-12 rounded-xl border-2"
              disabled={isListening}
            />
            <Button
              onClick={handleVoiceInput}
              disabled={isListening}
              size="icon"
              variant="outline"
              className="h-12 w-12 shrink-0 border-2 border-[#4A90E2] text-[#4A90E2] hover:bg-[#4A90E2] hover:text-white rounded-xl"
              aria-label="Activar entrada de voz"
            >
              <Mic size={20} className={isListening ? "animate-pulse" : ""} />
            </Button>
          </div>

          {/* Botón: Mostrar en Señas */}
          <Button
            onClick={handleShowSigns}
            disabled={!inputText.trim() || showAvatarSigns}
            className="w-full py-5 bg-[#50E3C2] hover:bg-[#40D3B2] text-white rounded-xl flex items-center justify-center gap-3 disabled:opacity-50"
          >
            <Send size={24} />
            Mostrar en Señas
          </Button>

          {isListening && (
            <p className="text-center text-sm text-[#4A90E2] animate-pulse">
              Escuchando...
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
