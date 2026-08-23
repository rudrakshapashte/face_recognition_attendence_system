import os
import time
import cv2
import numpy as np

from database import get_connection, mark_attendance

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset", "students")
TRAINER_DIR = os.path.join(BASE_DIR, "trainer")
MODEL_FILE = os.path.join(TRAINER_DIR, "trainer.yml")

CASCADE_FILE = os.path.join(
    cv2.data.haarcascades, "haarcascade_frontalface_default.xml"
)
FACE_CASCADE = cv2.CascadeClassifier(CASCADE_FILE)


def _check_face_detector():
    if FACE_CASCADE.empty():
        raise RuntimeError("OpenCV Haar Cascade could not be loaded.")


def _check_opencv_contrib():
    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "OpenCV Face module is missing. Remove opencv-python and install "
            "opencv-contrib-python==4.10.0.84."
        )


def _get_camera():
    # CAP_DSHOW usually gives better webcam compatibility on Windows.
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cam.isOpened():
        cam.release()
        cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        raise RuntimeError(
            "Webcam could not be opened. Check Windows Camera permission "
            "and close Zoom/Teams/Camera or other apps using the webcam."
        )

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cam


def capture_faces(student_id, name, samples=30):
    _check_face_detector()
    os.makedirs(DATASET_DIR, exist_ok=True)

    cam = _get_camera()
    count = 0
    last_saved = 0
    window = "Register Face - Press Q to cancel"

    try:
        while count < samples:
            ok, frame = cam.read()
            if not ok:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
            )

            for (x, y, w, h) in faces[:1]:
                # Save at most one sample every ~0.15 sec.
                now = time.time()
                if now - last_saved >= 0.15:
                    count += 1
                    face = gray[y:y+h, x:x+w]
                    path = os.path.join(
                        DATASET_DIR, f"User.{student_id}.{count}.jpg"
                    )
                    cv2.imwrite(path, face)
                    last_saved = now

                cv2.rectangle(
                    frame, (x, y), (x+w, y+h), (0, 255, 0), 2
                )
                cv2.putText(
                    frame, f"Samples: {count}/{samples}",
                    (x, max(25, y-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                )

            cv2.putText(
                frame, "Look at camera and move slightly | Q = cancel",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2
            )
            cv2.imshow(window, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cam.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)

    if count < 5:
        # Remove incomplete samples for this student.
        for filename in os.listdir(DATASET_DIR):
            if filename.startswith(f"User.{student_id}."):
                try:
                    os.remove(os.path.join(DATASET_DIR, filename))
                except OSError:
                    pass
        raise RuntimeError(
            "Not enough face samples captured. Please try again in good lighting."
        )

    return count


def train_model():
    _check_opencv_contrib()
    os.makedirs(TRAINER_DIR, exist_ok=True)

    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1, neighbors=8, grid_x=8, grid_y=8
    )

    faces = []
    ids = []

    if not os.path.isdir(DATASET_DIR):
        raise RuntimeError("No dataset folder found. Register a student first.")

    for filename in os.listdir(DATASET_DIR):
        if not filename.lower().endswith(".jpg"):
            continue

        parts = filename.split(".")
        if len(parts) < 3:
            continue

        try:
            student_id = int(parts[1])
        except ValueError:
            continue

        image = cv2.imread(
            os.path.join(DATASET_DIR, filename), cv2.IMREAD_GRAYSCALE
        )
        if image is not None:
            faces.append(image)
            ids.append(student_id)

    if not faces:
        raise RuntimeError("No face images found. Register a student first.")

    recognizer.train(faces, np.array(ids, dtype=np.int32))
    recognizer.write(MODEL_FILE)
    return len(faces)


def get_student_name(student_id):
    with get_connection() as con:
        row = con.execute(
            "SELECT name, roll_no FROM students WHERE id=?", (student_id,)
        ).fetchone()
    return (row["name"], row["roll_no"]) if row else None


def recognize_and_mark(seconds=15, threshold=65):
    _check_opencv_contrib()
    _check_face_detector()

    if not os.path.exists(MODEL_FILE):
        return {
            "success": False,
            "message": "No trained model found. Register a student first.",
            "recognized": []
        }

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_FILE)

    cam = _get_camera()
    start = time.time()
    newly_marked = []
    seen_ids = set()
    window = "Attendance - Press Q to stop"

    try:
        while time.time() - start < seconds:
            ok, frame = cam.read()
            if not ok:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
            )

            for (x, y, w, h) in faces[:3]:
                student_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                student = get_student_name(student_id)

                if student and confidence < threshold:
                    name, roll_no = student
                    is_new = mark_attendance(student_id)

                    if is_new and student_id not in seen_ids:
                        newly_marked.append({
                            "name": name,
                            "roll_no": roll_no
                        })
                        seen_ids.add(student_id)

                    label = f"{name} ({roll_no})"
                    status = "Present"
                    text_color = (0, 255, 0)
                else:
                    label = "Unknown"
                    status = ""
                    text_color = (0, 0, 255)

                cv2.rectangle(
                    frame, (x, y), (x+w, y+h), text_color, 2
                )
                cv2.putText(
                    frame, label, (x, max(25, y-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2
                )
                if status:
                    cv2.putText(
                        frame, status, (x, y+h+25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2
                    )

            remaining = max(0, int(seconds - (time.time() - start)))
            cv2.putText(
                frame, f"Scanning... {remaining}s | Q = stop",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2
            )
            cv2.imshow(window, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cam.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)

    if newly_marked:
        names = ", ".join(
            f"{x['name']} ({x['roll_no']})" for x in newly_marked
        )
        message = f"Attendance marked for: {names}"
    else:
        message = (
            "No new attendance marked. The student may already be present today, "
            "or the face was not recognized. Try better lighting."
        )

    return {
        "success": True,
        "message": message,
        "recognized": newly_marked
    }


def delete_student_faces(student_id):
    if not os.path.isdir(DATASET_DIR):
        return

    prefix = f"User.{student_id}."
    for filename in os.listdir(DATASET_DIR):
        if filename.startswith(prefix):
            try:
                os.remove(os.path.join(DATASET_DIR, filename))
            except OSError:
                pass
