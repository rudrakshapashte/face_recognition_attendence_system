import csv
import io
import os

from flask import Flask, render_template, request, jsonify, send_file

from database import (
    init_database, get_students, get_today_stats, get_attendance,
    add_student, student_exists, delete_student
)
from face_system import (
    capture_faces, train_model, recognize_and_mark, delete_student_faces
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder="Frontend", static_folder="Frontend/static")
app.config["JSON_SORT_KEYS"] = False

init_database()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")


@app.route("/reports")
def reports_page():
    return render_template("reports.html")


@app.get("/api/health")
def api_health():
    return jsonify({"success": True, "message": "Server is running."})


@app.get("/api/stats")
def api_stats():
    return jsonify(get_today_stats())


@app.get("/api/students")
def api_students():
    return jsonify(get_students())


@app.get("/api/attendance")
def api_attendance():
    date = request.args.get("date")
    return jsonify(get_attendance(date))


@app.post("/api/register")
def api_register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    roll_no = str(data.get("roll_no", "")).strip()

    if not name or not roll_no:
        return jsonify({
            "success": False,
            "message": "Name and Roll Number are required."
        }), 400

    if len(name) > 100 or len(roll_no) > 30:
        return jsonify({
            "success": False,
            "message": "Name or Roll Number is too long."
        }), 400

    if student_exists(roll_no):
        return jsonify({
            "success": False,
            "message": "This Roll Number is already registered."
        }), 409

    student_id = None

    try:
        student_id = add_student(name, roll_no)

        samples = capture_faces(student_id, name, samples=30)
        total_images = train_model()

        return jsonify({
            "success": True,
            "message": (
                f"{name} registered successfully. "
                f"{samples} face samples captured and model trained "
                f"with {total_images} images."
            ),
            "student_id": student_id
        })
    except Exception as exc:
        if student_id is not None:
            try:
                delete_student(student_id)
                delete_student_faces(student_id)
            except Exception:
                pass

        return jsonify({
            "success": False,
            "message": str(exc)
        }), 500


@app.post("/api/start-attendance")
def api_start_attendance():
    try:
        result = recognize_and_mark(seconds=15, threshold=65)
        return jsonify(result)
    except Exception as exc:
        return jsonify({
            "success": False,
            "message": str(exc),
            "recognized": []
        }), 500


@app.delete("/api/students/<int:student_id>")
def api_delete_student(student_id):
    try:
        delete_student_faces(student_id)
        delete_student(student_id)

        # Rebuild model from remaining faces if possible.
        remaining = get_students()
        if remaining:
            train_model()
        else:
            model = os.path.join(BASE_DIR, "trainer", "trainer.yml")
            if os.path.exists(model):
                os.remove(model)

        return jsonify({
            "success": True,
            "message": "Student and face data deleted."
        })
    except Exception as exc:
        return jsonify({
            "success": False,
            "message": str(exc)
        }), 500


@app.get("/api/export")
def api_export():
    rows = get_attendance(request.args.get("date"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Time", "Name", "Roll No", "Status"])
    for row in rows:
        writer.writerow([
            row["date"], row["time"], row["name"],
            row["roll_no"], row["status"]
        ])

    data = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    filename = "attendance_report.csv"
    return send_file(
        data,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )


@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": "API route not found."}), 404
    return "Page not found", 404


if __name__ == "__main__":
    # Disable the reloader so the webcam is never opened twice.
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
