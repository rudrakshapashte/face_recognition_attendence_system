# Face Recognition Attendance System

**TY Diploma ITR Project**

## Main features
- Student registration
- Laptop webcam face capture
- LBPH face recognition
- Automatic attendance
- SQLite database
- Attendance filter by date
- CSV attendance export
- Dashboard with total/present/absent/percentage
- Student delete and face-data cleanup
- Flask web interface

## Important: Python version

Use **Python 3.11** for the easiest OpenCV compatibility on Windows.

Do not use Python 3.14 for this project unless you have verified compatible OpenCV wheels.

## 1. Open the project

Open this project folder in VS Code.

Open **Terminal > New Terminal**.

## 2. Create virtual environment

```powershell
py -3.11 -m venv venv
```

If `py -3.11` is not recognized, install Python 3.11 first and then repeat the command.

## 3. Activate environment

PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` at the beginning of the terminal.

## 4. Remove conflicting OpenCV packages

Run:

```powershell
python -m pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y
```

## 5. Install packages

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 6. Check OpenCV Face module

Run:

```powershell
python -c "import cv2; print(cv2.__version__); print('cv2.face:', hasattr(cv2, 'face'))"
```

Expected result contains:

```text
4.10.0
cv2.face: True
```

If `cv2.face` is False, the wrong OpenCV package is installed.

## 7. Run the project

```powershell
python app.py
```

You should see:

```text
Running on http://127.0.0.1:5000
```

Open Chrome and type:

```text
http://127.0.0.1:5000
```

Keep the VS Code terminal running while using the website.

## 8. Register a student

1. Open **Register Student**.
2. Enter name.
3. Enter roll number.
4. Click **Capture & Register Face**.
5. A camera window opens.
6. Look at the camera and move your face slightly.
7. Wait for 30 samples.
8. The camera closes automatically.
9. The model is trained automatically.

## 9. Mark attendance

1. Go to Dashboard.
2. Click **Start Attendance**.
3. The webcam opens for about 15 seconds.
4. Look at the camera.
5. If recognized, the student is marked Present.
6. The same student cannot be marked twice on the same date.

## 10. View/export attendance

Open **Attendance**.

- Use the date field to filter records.
- Click Refresh.
- Click Export CSV to save an attendance report.

## 11. If webcam does not open

Check:
- Windows Settings > Privacy & security > Camera
- Allow desktop apps to access your camera
- Close Camera, Zoom, Teams, Google Meet, etc.
- Make sure the laptop webcam is not disabled
- Try the project again

## 12. If `cv2.face` is missing

Run:

```powershell
python -m pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y
python -m pip install opencv-contrib-python==4.10.0.84
```

Then check:

```powershell
python -c "import cv2; print(cv2.__version__); print(hasattr(cv2,'face'))"
```

## 13. Important project folders

- `Frontend/` = website pages
- `Frontend/static/` = CSS and JavaScript
- `dataset/students/` = captured face images
- `trainer/` = trained LBPH model
- `attendance.db` = SQLite database (created automatically)
- `attendance/` = reserved folder for attendance files

## 14. Viva explanation

**Face detection:** OpenCV Haar Cascade detects the face.

**Face recognition:** LBPH (Local Binary Patterns Histograms) recognizes the registered face.

**Database:** SQLite stores student and attendance information.

**Backend:** Flask handles web pages and API requests.

**Frontend:** HTML, CSS and JavaScript provide the user interface.

**Webcam:** The laptop webcam captures face images for registration and recognition.

**Attendance rule:** A student can be marked Present only once per day.

## 15. Project flow

Student Registration
→ Webcam Face Capture
→ Face Dataset
→ LBPH Model Training
→ Face Recognition
→ Attendance Marking
→ SQLite Database
→ Dashboard / Reports
