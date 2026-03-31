from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doctors.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slot1 DATE NOT NULL,
            slot2 DATE NOT NULL,
            slot3 DATE,
            slot4 DATE,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"].strip()
    slot1 = request.form["slot1"]
    slot2 = request.form["slot2"]
    slot3 = request.form.get("slot3", "").strip() or None
    slot4 = request.form.get("slot4", "").strip() or None

    if not name or not slot1 or not slot2:
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        "INSERT INTO doctors (name, slot1, slot2, slot3, slot4) VALUES (?, ?, ?, ?, ?)",
        (name, slot1, slot2, slot3, slot4),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("success"))


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/admin")
def admin():
    conn = get_db()
    doctors = conn.execute(
        "SELECT * FROM doctors ORDER BY submitted_at ASC"
    ).fetchall()
    conn.close()

    # Build per-date ranking: top 3 earliest submissions per date
    date_entries = defaultdict(list)
    for d in doctors:
        for slot_key in ["slot1", "slot2", "slot3", "slot4"]:
            slot_val = d[slot_key]
            if slot_val:
                date_entries[slot_val].append({
                    "name": d["name"],
                    "submitted_at": d["submitted_at"],
                })

    # Sort each date's entries by submission time, keep top 3
    schedule = {}
    for date in sorted(date_entries.keys()):
        entries = sorted(date_entries[date], key=lambda x: x["submitted_at"])
        schedule[date] = entries[:3]

    return render_template("admin.html", schedule=schedule)


@app.route("/admin/clear", methods=["POST"])
def clear_all():
    conn = get_db()
    conn.execute("DELETE FROM doctors")
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5050)
