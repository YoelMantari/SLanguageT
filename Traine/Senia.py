import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
import json
from collections import deque

# ================================
# CARGAR MODELO Y LABELS
# ================================
MODEL_PATH = "modelo_senas.keras"
LABELS_PATH = "labels.json"
NUM_FRAMES = 30
CONFIDENCE_THRESHOLD = 0.70   # 🔥 evita confusiones
SMOOTHING_WINDOW = 5          # 🔥 suavizado de predicción

model = tf.keras.models.load_model(MODEL_PATH)

with open(LABELS_PATH, "r") as f:
    LABELS = json.load(f)

# ================================
# MEDIAPIPE HOLISTIC
# ================================
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ================================
# EXTRAER KEYPOINTS
# ================================
def extract_keypoints(res):
    out = []
    pose_map = {"left_shoulder": 11, "right_shoulder": 12, "nose": 0}

    # Pose básica
    if res.pose_landmarks:
        for name in pose_map:
            lm = res.pose_landmarks.landmark[pose_map[name]]
            out.extend([lm.x, lm.y, lm.z])
    else:
        out.extend([0.0] * 9)

    # Mano izquierda
    if res.left_hand_landmarks:
        for lm in res.left_hand_landmarks.landmark:
            out.extend([lm.x, lm.y, lm.z])
    else:
        out.extend([0.0] * 63)

    # Mano derecha
    if res.right_hand_landmarks:
        for lm in res.right_hand_landmarks.landmark:
            out.extend([lm.x, lm.y, lm.z])
    else:
        out.extend([0.0] * 63)

    return np.array(out, dtype=np.float32)

# ================================
# AJUSTAR SECUENCIA A 30 FRAMES
# ================================
def fix_sequence(seq):
    seq = np.array(seq)

    if len(seq) >= NUM_FRAMES:
        idxs = np.linspace(0, len(seq)-1, NUM_FRAMES).astype(int)
        return seq[idxs]

    last = seq[-1]
    while len(seq) < NUM_FRAMES:
        seq = np.vstack([seq, last])

    return seq[:NUM_FRAMES]

# ================================
# DETECTAR MANOS
# ================================
def hands_present(res):
    return (
        res.left_hand_landmarks is not None or 
        res.right_hand_landmarks is not None
    )

# ================================
# REAL-TIME LOOP
# ================================
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

state = "WAIT_HANDS"
sequence = []
predicted_label = ""
smooth_preds = deque(maxlen=SMOOTHING_WINDOW)

print("\n🟢 Sistema Real-Time LISTO (versión mejorada)\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = holistic.process(rgb)
    have_hands = hands_present(res)

    # Dibujar manos
    if res.left_hand_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            frame, res.left_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
    if res.right_hand_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            frame, res.right_hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

    # ===============================
    # ESTADOS
    # ===============================
    if state == "WAIT_HANDS":
        predicted_label = ""
        sequence = []
        smooth_preds.clear()

        if have_hands:
            state = "RECORDING"

    elif state == "RECORDING":
        if not have_hands:
            state = "WAIT_HANDS"
            sequence = []
        else:
            kp = extract_keypoints(res)
            sequence.append(kp)

            if len(sequence) == NUM_FRAMES:
                seq30 = fix_sequence(sequence)
                seq30 = np.expand_dims(seq30, axis=0)

                pred = model.predict(seq30, verbose=0)[0]
                idx = int(np.argmax(pred))
                prob = float(pred[idx])

                # Guardar en suavizado
                smooth_preds.append((idx, prob))

                # Predicción final con suavizado
                ids = [p[0] for p in smooth_preds]
                probs = [p[1] for p in smooth_preds]

                final_idx = max(set(ids), key=ids.count)
                final_prob = np.mean([probs[i] for i in range(len(ids)) if ids[i]==final_idx])

                if final_prob >= CONFIDENCE_THRESHOLD:
                    predicted_label = LABELS[final_idx]
                else:
                    predicted_label = ""

                state = "HOLD_RESULT"

    elif state == "HOLD_RESULT":
        if not have_hands:
            predicted_label = ""
            state = "WAIT_HANDS"
            sequence = []
            smooth_preds.clear()

    # ===============================
    # UI
    # ===============================
    if predicted_label != "":
        cv2.putText(frame, predicted_label, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0,255,0), 3)

    cv2.putText(frame, f"Estado: {state}", (20, 430),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    cv2.imshow("Sign Recognition PRO", frame)

    if cv2.waitKey(1) & 0xFF in [27, ord("q")]:
        break

cap.release()
cv2.destroyAllWindows()
