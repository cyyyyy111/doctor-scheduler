from flask import Flask, render_template, request, redirect, url_for
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict

app = Flask(__name__, template_folder="../templates")

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            slot1 DATE NOT NULL,
            slot2 DATE NOT NULL,
            slot3 DATE,
            slot4 DATE,
            submitted_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


try:
    init_db()
except Exception:
    pass


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
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO doctors (name, slot1, slot2, slot3, slot4) VALUES (%s, %s, %s, %s, %s)",
        (name, slot1, slot2, slot3, slot4),
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("success"))


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/admin")
def admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM doctors ORDER BY submitted_at ASC")
    doctors = cur.fetchall()
    cur.close()
    conn.close()

    date_entries = defaultdict(list)
    for d in doctors:
        for slot_key in ["slot1", "slot2", "slot3", "slot4"]:
            slot_val = d[slot_key]
            if slot_val:
                date_entries[str(slot_val)].append({
                    "name": d["name"],
                    "submitted_at": str(d["submitted_at"]),
                })

    schedule = {}
    for date in sorted(date_entries.keys()):
        entries = sorted(date_entries[date], key=lambda x: x["submitted_at"])
        schedule[date] = entries[:3]

    return render_template("admin.html", schedule=schedule)


@app.route("/admin/clear", methods=["POST"])
def clear_all():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM doctors")
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin"))
