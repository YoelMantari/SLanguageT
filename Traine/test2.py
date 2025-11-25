from openhands.models import STGCN
from openhands.data import WLASLDataset
from openhands.inference import PoseToGloss
import mediapipe as mp
import cv2

# Cargar modelo ST-GCN preentrenado para WLASL (ASL)
model = STGCN.load_from_checkpoint("checkpoints/wlasl_stgcn.ckpt")
model.eval()

# Inicializar MediaPipe
mp_holistic = mp.solutions.holistic.Holistic()
pose_to_gloss = PoseToGloss(model)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # detectar keypoints
    results = mp_holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # convertir landmarks a formato del modelo
    gloss = pose_to_gloss(results)
    
    if gloss:
        print("Seña detectada:", gloss)

    cv2.imshow("ASL Recognition", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
