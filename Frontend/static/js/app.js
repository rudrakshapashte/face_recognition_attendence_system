async function api(url, options = {}) {
    const response = await fetch(url, options);
    let data;
    try {
        data = await response.json();
    } catch {
        throw new Error(`Server error (${response.status})`);
    }
    if (!response.ok) {
        throw new Error(data.message || `Request failed (${response.status})`);
    }
    return data;
}

function setMessage(text, type = "") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = "message " + type;
}

async function loadStats() {
    try {
        const d = await api("/api/stats");
        const set = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        set("total", d.total_students);
        set("present", d.present);
        set("absent", d.absent);
        set("percentage", d.percentage + "%");
        set("dateText", d.date);
    } catch (err) {
        setMessage(err.message, "error");
    }
}

async function registerStudent() {
    const nameEl = document.getElementById("name");
    const rollEl = document.getElementById("roll_no");
    const btn = document.getElementById("registerBtn");

    const name = nameEl.value.trim();
    const roll_no = rollEl.value.trim();

    if (!name || !roll_no) {
        setMessage("Please enter Name and Roll Number.", "error");
        return;
    }

    btn.disabled = true;
    setMessage("Opening webcam... Please look at the camera.");

    try {
        const d = await api("/api/register", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, roll_no})
        });

        setMessage(d.message, "success");
        nameEl.value = "";
        rollEl.value = "";
    } catch (err) {
        setMessage(err.message, "error");
    } finally {
        btn.disabled = false;
    }
}

async function startAttendance() {
    const buttons = document.querySelectorAll("button");
    buttons.forEach(b => b.disabled = true);
    setMessage("Opening camera for attendance...");

    try {
        const d = await api("/api/start-attendance", {method: "POST"});
        setMessage(d.message, d.success ? "success" : "error");
        await loadStats();
    } catch (err) {
        setMessage(err.message, "error");
    } finally {
        buttons.forEach(b => b.disabled = false);
    }
}

async function loadAttendance() {
    const body = document.getElementById("attendanceBody");
    if (!body) return;

    const date = document.getElementById("dateFilter")?.value || "";
    body.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';

    try {
        const data = await api("/api/attendance" + (date ? "?date=" + encodeURIComponent(date) : ""));
        if (!data.length) {
            body.innerHTML = '<tr><td colspan="5">No attendance records found.</td></tr>';
            return;
        }
        body.innerHTML = data.map(x =>
            `<tr><td>${escapeHtml(x.date)}</td><td>${escapeHtml(x.time)}</td>
             <td>${escapeHtml(x.name)}</td><td>${escapeHtml(x.roll_no)}</td>
             <td><span class="status">${escapeHtml(x.status)}</span></td></tr>`
        ).join("");
    } catch (err) {
        body.innerHTML = `<tr><td colspan="5">${escapeHtml(err.message)}</td></tr>`;
    }
}

async function loadStudents() {
    const body = document.getElementById("studentsBody");
    if (!body) return;

    body.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';

    try {
        const data = await api("/api/students");
        if (!data.length) {
            body.innerHTML = '<tr><td colspan="5">No students registered.</td></tr>';
            return;
        }
        body.innerHTML = data.map(x =>
            `<tr><td>${x.id}</td><td>${escapeHtml(x.name)}</td>
             <td>${escapeHtml(x.roll_no)}</td><td>${escapeHtml(x.created_at)}</td>
             <td><button class="danger" onclick="deleteStudent(${x.id})">Delete</button></td></tr>`
        ).join("");
    } catch (err) {
        body.innerHTML = `<tr><td colspan="5">${escapeHtml(err.message)}</td></tr>`;
    }
}

async function deleteStudent(id) {
    if (!confirm("Delete this student, face data and attendance records?")) return;

    try {
        const d = await api("/api/students/" + id, {method: "DELETE"});
        alert(d.message);
        await loadStudents();
        await loadStats();
    } catch (err) {
        alert(err.message);
    }
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;",
        '"': "&quot;", "'": "&#039;"
    }[char]));
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("total")) loadStats();
});
