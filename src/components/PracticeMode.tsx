import { useState, useRef, useEffect } from "react";
import {
  ArrowLeft,
  Camera,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Video,
  VideoOff,
  StopCircle,
} from "lucide-react";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import AvatarAnimationPlayer from "./avatar/AvatarAnimationPlayer";

interface PracticeModeProps {
  onBack: () => void;
}

const lessons = [
  { id: 1, phrase: "Hola", difficulty: "easy", signKey: "hola" },
  { id: 2, phrase: "Yo", difficulty: "easy", signKey: "yo" },
  { id: 3, phrase: "Tú", difficulty: "easy", signKey: "tu" },
  { id: 4, phrase: "Gracias", difficulty: "easy", signKey: "gracias" },
  { id: 5, phrase: "Por favor", difficulty: "medium", signKey: "porfavor" },
  { id: 6, phrase: "Ayuda", difficulty: "medium", signKey: "ayuda" },
  { id: 7, phrase: "Baño", difficulty: "medium", signKey: "baño" },
  { id: 8, phrase: "Casa", difficulty: "easy", signKey: "casa" },
  { id: 9, phrase: "Comer", difficulty: "easy", signKey: "comer" },
  { id: 10, phrase: "Beber", difficulty: "easy", signKey: "beber" },
  { id: 11, phrase: "Dolor", difficulty: "medium", signKey: "dolor" },
  { id: 12, phrase: "¿Dónde?", difficulty: "medium", signKey: "donde" },
  { id: 13, phrase: "Espera", difficulty: "medium", signKey: "espera" },
  { id: 14, phrase: "Ir", difficulty: "easy", signKey: "ir" },
  { id: 15, phrase: "Venir", difficulty: "easy", signKey: "venir" },
  { id: 16, phrase: "Querer", difficulty: "medium", signKey: "querer" },
  { id: 17, phrase: "Adiós", difficulty: "easy", signKey: "adios" },
];

export function PracticeMode({ onBack }: PracticeModeProps) {
  const [currentLesson, setCurrentLesson] = useState(0);
  const [feedback, setFeedback] = useState<
    "correct" | "almost" | "incorrect" | null
  >(null);
  const [showDemo, setShowDemo] = useState(false);

  // Camera & Detection State
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const isDetectingRef = useRef<boolean>(false);
  const detectionIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [isCameraOn, setIsCameraOn] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectionStatus, setDetectionStatus] = useState("");
  const [confidence, setConfidence] = useState(0);

  const lesson = lessons[currentLesson];
  const progress = ((currentLesson + 1) / lessons.length) * 100;

  // Ref to track current lesson inside WebSocket callback without stale closures
  const lessonRef = useRef(lesson);

  useEffect(() => {
    lessonRef.current = lessons[currentLesson];
  }, [currentLesson]);

  // Auto-advance when feedback is correct
  useEffect(() => {
    if (feedback === "correct") {
      const timer = setTimeout(() => {
        handleNext();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [feedback]);

  const WS_URL = "ws://localhost:8000/ws/detect";
  const DETECTION_INTERVAL = 100;

  // --- Camera Logic ---
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
        video: { width: 640, height: 480, facingMode: "user" },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current
            ?.play()
            .catch((err) => console.error("Error playing video:", err));
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

  // --- WebSocket & Detection Logic ---
  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      console.log("✓ WebSocket conectado");
      setDetectionStatus("Conectado al servidor");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "detection") {
          const result = data.data;
          if (result.hand_detected) {
            if (result.sign && result.confidence > 0.7) {
              setConfidence(result.confidence);
              setDetectionStatus(`✓ Seña: ${result.sign}`);

              // Check against the current lesson using the ref
              if (
                result.sign
                  .toLowerCase()
                  .includes(lessonRef.current.signKey.toLowerCase())
              ) {
                setFeedback("correct");
              }
            } else {
              setDetectionStatus(result.message || "🖐️ Mano detectada");
            }
          } else {
            setDetectionStatus("No se detecta mano");
          }
        }
      } catch (error) {
        console.error("Error procesando mensaje:", error);
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

  const sendFrameToServer = () => {
    if (!videoRef.current || !canvasRef.current || !wsRef.current) return;
    if (wsRef.current.readyState !== WebSocket.OPEN) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    if (!context || video.readyState !== video.HAVE_ENOUGH_DATA) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL("image/jpeg", 0.8);
    wsRef.current.send(JSON.stringify({ type: "frame", image: imageData }));
  };

  const startDetectionLoop = () => {
    if (detectionIntervalRef.current)
      clearInterval(detectionIntervalRef.current);
    detectionIntervalRef.current = setInterval(() => {
      if (!isDetectingRef.current) {
        if (detectionIntervalRef.current)
          clearInterval(detectionIntervalRef.current);
        return;
      }
      sendFrameToServer();
    }, DETECTION_INTERVAL);
  };

  const toggleDetection = () => {
    if (!isCameraOn) {
      setDetectionStatus("Primero enciende la cámara");
      return;
    }

    if (isDetecting) {
      setIsDetecting(false);
      isDetectingRef.current = false;
      if (detectionIntervalRef.current)
        clearInterval(detectionIntervalRef.current);
      disconnectWebSocket();
      setDetectionStatus("Detección detenida");
    } else {
      setIsDetecting(true);
      isDetectingRef.current = true;
      setFeedback(null);
      connectWebSocket();
      setTimeout(() => startDetectionLoop(), 1500);
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      isDetectingRef.current = false;
      if (detectionIntervalRef.current)
        clearInterval(detectionIntervalRef.current);
      stopCamera();
      disconnectWebSocket();
    };
  }, []);

  const handleNext = () => {
    if (currentLesson < lessons.length - 1) {
      setCurrentLesson(currentLesson + 1);
      setFeedback(null);
      setShowDemo(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white pb-4 overflow-hidden">
      <canvas ref={canvasRef} style={{ display: "none" }} />

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 shrink-0">
        <div className="flex items-center gap-4 mb-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="rounded-full"
            aria-label="Volver"
          >
            <ArrowLeft size={24} />
          </Button>
          <h2 className="text-lg font-semibold">Modo Práctica</h2>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1 max-w-md mx-auto w-full">
          <div className="flex justify-between text-xs text-[#8E8E93]">
            <span>
              Lección {currentLesson + 1} de {lessons.length}
            </span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-1.5" />
        </div>
      </div>

      {/* Main Content - Split View */}
      <div className="flex-1 overflow-hidden p-2 sm:p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 h-full max-w-7xl mx-auto">
          {/* Left Column: Target / Avatar */}
          <div className="flex flex-col gap-2 h-[45vh] lg:h-full">
            <div className="bg-slate-50 rounded-2xl p-3 border border-slate-100 shadow-sm flex flex-col items-center text-center h-full">
              <div className="mb-2 space-y-1 shrink-0">
                <div className="inline-block px-3 py-0.5 bg-blue-100 text-blue-600 rounded-full text-[10px] font-medium uppercase tracking-wide mb-1">
                  {lesson.difficulty === "easy" && "Nivel Fácil"}
                  {lesson.difficulty === "medium" && "Nivel Medio"}
                  {lesson.difficulty === "hard" && "Nivel Difícil"}
                </div>
                <h3 className="text-lg font-bold text-slate-900">
                  "{lesson.phrase}"
                </h3>
              </div>

              {/* Avatar Container */}
              <div className="w-full flex-1 bg-white rounded-xl overflow-hidden border border-slate-200 shadow-inner relative min-h-0">
                <div className="absolute inset-0">
                  <AvatarAnimationPlayer sign={lesson.signKey} />
                </div>
                <div className="absolute bottom-2 right-2 bg-black/50 text-white text-[10px] px-2 py-1 rounded backdrop-blur-sm">
                  Avatar
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Camera & Feedback */}
          <div className="flex flex-col gap-2 h-full lg:h-full overflow-hidden">
            {/* Camera View */}
            <div className="relative bg-black rounded-2xl overflow-hidden shadow-sm flex-1 border border-slate-200 min-h-0">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="absolute inset-0 w-full h-full object-cover scale-x-[-1]"
                style={{ display: isCameraOn ? "block" : "none" }}
              />

              {!isCameraOn && (
                <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center text-slate-500 gap-2">
                  <Camera size={32} className="opacity-50" />
                  <p className="text-xs">Cámara apagada</p>
                </div>
              )}

              {isDetecting && (
                <div className="absolute inset-0 border-4 border-[#50E3C2] animate-pulse pointer-events-none rounded-2xl" />
              )}

              {/* Status Overlay */}
              {detectionStatus && isCameraOn && (
                <div className="absolute top-4 left-4 right-4 flex justify-center pointer-events-none">
                  <div className="bg-black/70 text-white px-3 py-1.5 rounded-full text-xs backdrop-blur-md flex items-center gap-2 shadow-lg">
                    <div
                      className={`w-1.5 h-1.5 rounded-full ${
                        confidence > 0.7 ? "bg-[#50E3C2]" : "bg-orange-500"
                      }`}
                    />
                    {detectionStatus}
                    {confidence > 0 && (
                      <span className="font-mono text-[#50E3C2]">
                        {Math.round(confidence * 100)}%
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Controls Area */}
            <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-sm shrink-0">
              {/* Feedback Message */}
              {feedback && (
                <div
                  className={`mb-3 p-3 rounded-xl flex items-center gap-3 ${
                    feedback === "correct"
                      ? "bg-green-50 text-green-700 border border-green-100"
                      : feedback === "almost"
                      ? "bg-yellow-50 text-yellow-700 border border-yellow-100"
                      : "bg-red-50 text-red-700 border border-red-100"
                  }`}
                >
                  {feedback === "correct" ? (
                    <CheckCircle2 size={20} />
                  ) : feedback === "almost" ? (
                    <div className="text-lg">⚠️</div>
                  ) : (
                    <XCircle size={20} />
                  )}

                  <div className="flex-1">
                    <p className="font-bold text-sm">
                      {feedback === "correct"
                        ? "¡Excelente!"
                        : feedback === "almost"
                        ? "¡Casi lo tienes!"
                        : "Inténtalo de nuevo"}
                    </p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2">
                <Button
                  onClick={toggleCamera}
                  style={{
                    backgroundColor: isCameraOn ? "#EF4444" : "#2563EB",
                    color: "white",
                  }}
                  className="h-10 text-sm border-none hover:opacity-90"
                >
                  {isCameraOn ? (
                    <>
                      <VideoOff className="mr-2 h-3 w-3" /> Detener
                    </>
                  ) : (
                    <>
                      <Video className="mr-2 h-3 w-3" /> Cámara
                    </>
                  )}
                </Button>

                <Button
                  onClick={toggleDetection}
                  disabled={!isCameraOn}
                  style={{
                    backgroundColor: isDetecting ? "#F97316" : "#50E3C2",
                    color: isDetecting ? "white" : "#0F172A",
                  }}
                  className="h-10 text-sm border-none hover:opacity-90 disabled:opacity-50"
                >
                  {isDetecting ? (
                    <>
                      <StopCircle className="mr-2 h-3 w-3" /> Detener
                    </>
                  ) : (
                    <>
                      <Camera className="mr-2 h-3 w-3" /> Detectar
                    </>
                  )}
                </Button>
              </div>

              {/* Navigation (Only show when correct or manual override) */}
              <div className="mt-2 pt-2 border-t border-slate-100 flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNext}
                  disabled={currentLesson === lessons.length - 1}
                  className="text-slate-500 hover:text-slate-900 text-xs h-8"
                >
                  Saltar lección <ChevronRight className="ml-1 h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
