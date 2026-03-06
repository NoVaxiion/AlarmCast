from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from passlib.hash import argon2
import sqlite3
import os
from contextlib import contextmanager
import smtplib
from email.message import EmailMessage
import re
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

DB_PATH = os.getenv("DATABASE_PATH", "alarmcast.db")

CARRIER_GATEWAYS = {
    "verizon": "vtext.com",
    "att": "txt.att.net",
    "tmobile": "tmomail.net"
}

ALERT_MESSAGES = {
    "SMOKE": "AlarmCast: FIRE/SMOKE alarm detected",
    "FIRE": "AlarmCast: FIRE/SMOKE alarm detected",
    "CO": "AlarmCast: CO alarm detected",
    "CARBON": "AlarmCast: CO alarm detected",
    "TEST": "AlarmCast: TEST alert",
}

def build_alert_message(event_type: str) -> str:
    et = (event_type or "").upper()
    return ALERT_MESSAGES.get(et, f"AlarmCast: Alert detected ({et})")

def is_expo_token(token: str) -> bool:
    return isinstance(token, str) and (
        token.startswith("ExponentPushToken[") or token.startswith("ExpoPushToken[")
    )

def send_expo_push(token: str, title: str, body: str):
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default",
        "priority": "high",
    }

    response = requests.post(
        "https://exp.host/--/api/v2/push/send",
        json=payload,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def normalize_phone_digits(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Phone must be a US 10-digit number (or +1 + 10 digits).")
    return digits

def normalize_carrier(carrier: str) -> str:
    c = (carrier or "").lower().strip()
    c = c.replace("-", "").replace(" ", "")
    if c in ["tmobile", "tmo"]:
        return "tmobile"
    if c in ["att", "at&t", "atandt"]:
        return "att"
    if c in ["verizon", "vz"]:
        return "verizon"
    return c

def send_sms_via_email(phone: str, carrier: str, message: str):
    email_user = os.getenv("ALERT_EMAIL_USER")
    email_pass = os.getenv("ALERT_EMAIL_PASS")
    if not email_user or not email_pass:
        raise RuntimeError("Missing ALERT_EMAIL_USER or ALERT_EMAIL_PASS environment variables")

    carrier_key = normalize_carrier(carrier)
    if carrier_key not in CARRIER_GATEWAYS:
        raise ValueError(f"Unknown carrier '{carrier}'. Supported: {list(CARRIER_GATEWAYS.keys())}")

    phone_digits = normalize_phone_digits(phone)
    to_addr = f"{phone_digits}@{CARRIER_GATEWAYS[carrier_key]}"

    msg = EmailMessage()
    msg["From"] = email_user
    msg["To"] = to_addr
    msg["Subject"] = ""
    msg.set_content((message or "")[:160])

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_pass)
        smtp.send_message(msg)

def notify_hub_members(hub_id: int, message: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone, carrier FROM member WHERE hub_id = ?", (hub_id,))
        rows = cursor.fetchall()

    results = []
    for r in rows:
        try:
            send_sms_via_email(r["phone"], r["carrier"], message)
            results.append({"phone": r["phone"], "ok": True})
        except Exception as e:
            results.append({"phone": r["phone"], "ok": False, "error": str(e)})
    return results

def notify_hub_users_push(hub_id: int, message: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT u.user_id, u.username, u.expo_push_token
            FROM users u
            JOIN member m ON m.user_id = u.user_id
            WHERE m.hub_id = ?
              AND u.expo_push_token IS NOT NULL
              AND u.expo_push_token != ''
            """,
            (hub_id,)
        )
        rows = cursor.fetchall()

    results = []
    for row in rows:
        token = row["expo_push_token"]

        if not is_expo_token(token):
            results.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "ok": False,
                "error": "Invalid Expo push token"
            })
            continue

        try:
            expo_result = send_expo_push(token, "AlarmCast", message)
            results.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "ok": True,
                "result": expo_result
            })
        except Exception as e:
            results.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "ok": False,
                "error": str(e)
            })

    return results

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = f.read()
        with get_db() as conn:
            conn.executescript(schema)

with app.app_context():
    init_db()

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})

@app.route("/api/auth/register", methods=["POST"])
def register_user():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        abort(400, description="Username and password_hash are required")

    with get_db() as conn:
        password_hash = argon2.hash(data["password"])

        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, password_algo) VALUES (?, ?, ?)",
                (data["username"], password_hash, data.get("password_algo", "argon2"))
            )
            user_id = cursor.lastrowid
            return jsonify({
                "user_id": user_id,
                "username": data["username"]
            }), 201
        except sqlite3.IntegrityError:
            abort(400, description="Username already exists")

@app.route("/api/auth/login", methods=["POST"])
def login_user():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        abort(400, description="Username and password are required")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, password_hash FROM users WHERE username = ?",
            (data["username"],)
        )
        row = cursor.fetchone()
        if not row:
            abort(401, description="Invalid credentials")

        if not argon2.verify(data["password"], row["password_hash"]):
            abort(401, description="Invalid credentials")

        return jsonify({
            "user_id": row["user_id"],
            "username": row["username"]
        })

@app.route("/api/users/<int:user_id>/push-token", methods=["POST"])
def upsert_push_token(user_id):
    data = request.get_json() or {}
    token = data.get("expo_push_token")

    if not token or not is_expo_token(token):
        abort(400, description="Valid expo_push_token is required")

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            abort(404, description="User not found")

        cursor.execute(
            """
            UPDATE users
            SET expo_push_token = ?, expo_push_token_updated_at = ?
            WHERE user_id = ?
            """,
            (token, datetime.utcnow().isoformat(), user_id),
        )

    return jsonify({
        "message": "Push token saved",
        "user_id": user_id
    })

@app.route("/api/hubs", methods=["POST"])
def create_hub():
    data = request.get_json()
    if not data or not data.get("hub_name"):
        abort(400, description="hub_name is required")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hub (hub_name) VALUES (?)",
            (data["hub_name"],)
        )
        hub_id = cursor.lastrowid
        return jsonify({
            "hub_id": hub_id,
            "hub_name": data["hub_name"]
        }), 201

@app.route("/api/hubs/<int:hub_id>", methods=["GET"])
def get_hub(hub_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hub_id, hub_name FROM hub WHERE hub_id = ?", (hub_id,))
        row = cursor.fetchone()
        if not row:
            abort(404, description="Hub not found")
        return jsonify({
            "hub_id": row["hub_id"],
            "hub_name": row["hub_name"]
        })

@app.route("/api/hubs/<int:hub_id>/members", methods=["POST"])
def create_member(hub_id):
    data = request.get_json()
    if not data or not data.get("name") or not data.get("phone") or not data.get("carrier"):
        abort(400, description="name, phone, and carrier are required")

    carrier_key = normalize_carrier(data["carrier"])
    if carrier_key not in CARRIER_GATEWAYS:
        abort(400, description="carrier must be verizon, att, or tmobile")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hub_id FROM hub WHERE hub_id = ?", (hub_id,))
        if not cursor.fetchone():
            abort(404, description="Hub not found")

        cursor.execute(
            """INSERT INTO member (hub_id, name, phone, carrier, role, user_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (hub_id, data["name"], data["phone"], carrier_key, data.get("role", "member"), data.get("user_id"))
        )

        member_id = cursor.lastrowid
        return jsonify({
            "member_id": member_id,
            "hub_id": hub_id,
            "name": data["name"],
            "phone": data["phone"],
            "carrier": carrier_key,
            "role": data.get("role", "member"),
            "user_id": data.get("user_id")
        }), 201

@app.route("/api/hubs/<int:hub_id>/members", methods=["GET"])
def get_members(hub_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT member_id, hub_id, name, phone, carrier, role, user_id
               FROM member WHERE hub_id = ?""",
            (hub_id,)
        )
        members = [{
            "member_id": row["member_id"],
            "hub_id": row["hub_id"],
            "name": row["name"],
            "phone": row["phone"],
            "carrier": row["carrier"],
            "role": row["role"],
            "user_id": row["user_id"]
        } for row in cursor.fetchall()]
        return jsonify(members)

@app.route("/api/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM member WHERE member_id = ?", (member_id,))
        if cursor.rowcount == 0:
            abort(404, description="Member not found")
        return jsonify({"message": "Member deleted successfully"})

@app.route("/api/hubs/<int:hub_id>/devices", methods=["POST"])
def create_device(hub_id):
    data = request.get_json() or {}

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hub_id FROM hub WHERE hub_id = ?", (hub_id,))
        if not cursor.fetchone():
            abort(404, description="Hub not found")

        is_active = data.get("is_active", 1)
        is_initialized = data.get("is_initialized", 0)

        cursor.execute(
            """INSERT INTO device (hub_id, is_active, is_initialized)
               VALUES (?, ?, ?)""",
            (hub_id, is_active, is_initialized)
        )
        device_id = cursor.lastrowid
        return jsonify({
            "device_id": device_id,
            "hub_id": hub_id,
            "is_active": bool(is_active),
            "is_initialized": bool(is_initialized)
        }), 201

@app.route("/api/hubs/<int:hub_id>/devices", methods=["GET"])
def get_devices(hub_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT device_id, hub_id, is_active, is_initialized FROM device WHERE hub_id = ?",
            (hub_id,)
        )
        devices = [{
            "device_id": row["device_id"],
            "hub_id": row["hub_id"],
            "is_active": bool(row["is_active"]),
            "is_initialized": bool(row["is_initialized"])
        } for row in cursor.fetchall()]
        return jsonify(devices)

@app.route("/api/devices/<int:device_id>/events", methods=["POST"])
def create_device_event(device_id):
    data = request.get_json()
    if not data or not data.get("event_type"):
        abort(400, description="event_type is required")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM device WHERE device_id = ?", (device_id,))
        if not cursor.fetchone():
            abort(404, description="Device not found")

        cursor.execute(
            "INSERT INTO device_event (device_id, event_type) VALUES (?, ?)",
            (device_id, data["event_type"])
        )
        event_id = cursor.lastrowid
        cursor.execute(
            "SELECT device_event_id, device_id, event_type, detected_at FROM device_event WHERE device_event_id = ?",
            (event_id,)
        )
        row = cursor.fetchone()
        return jsonify({
            "device_event_id": row["device_event_id"],
            "device_id": row["device_id"],
            "event_type": row["event_type"],
            "detected_at": row["detected_at"]
        }), 201

@app.route("/api/alerts", methods=["POST"])
def create_alert():
    data = request.get_json()
    if not data or not data.get("hub_id") or not data.get("device_event_id"):
        abort(400, description="hub_id and device_event_id are required")

    hub_id = data["hub_id"]
    device_event_id = data["device_event_id"]
    status = data.get("status", "pending")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hub_id FROM hub WHERE hub_id = ?", (hub_id,))
        if not cursor.fetchone():
            abort(404, description="Hub not found")

        cursor.execute(
            "SELECT device_event_id, event_type FROM device_event WHERE device_event_id = ?",
            (device_event_id,)
        )
        event_row = cursor.fetchone()
        if not event_row:
            abort(404, description="Device event not found")

        event_type = event_row["event_type"]

        cursor.execute(
            "INSERT INTO alert (hub_id, device_event_id, status) VALUES (?, ?, ?)",
            (hub_id, device_event_id, status)
        )
        alert_id = cursor.lastrowid

    msg = build_alert_message(event_type)
    sms_notify_results = notify_hub_members(hub_id, msg)
    push_notify_results = notify_hub_users_push(hub_id, msg)

    return jsonify({
        "alert_id": alert_id,
        "hub_id": data["hub_id"],
        "device_event_id": data["device_event_id"],
        "status": status,
        "event_type": event_type,
        "sms_notify_results": sms_notify_results,
        "push_notify_results": push_notify_results
    }), 201

@app.route("/api/hubs/<int:hub_id>/alerts", methods=["GET"])
def get_alert_history(hub_id):
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT
                a.alert_id,
                a.hub_id,
                a.device_event_id,
                a.status,
                de.device_id,
                de.event_type,
                de.detected_at
            FROM alert a
            JOIN device_event de ON a.device_event_id = de.device_event_id
            WHERE a.hub_id = ?
            ORDER BY de.detected_at DESC
            LIMIT ? OFFSET ?""",
            (hub_id, limit, offset)
        )
        alerts = [{
            "alert_id": row["alert_id"],
            "hub_id": row["hub_id"],
            "device_event_id": row["device_event_id"],
            "status": row["status"],
            "event_type": row["event_type"],
            "detected_at": row["detected_at"]
        } for row in cursor.fetchall()]
        return jsonify(alerts)

@app.route("/api/hubs/<int:hub_id>/monitoring/status", methods=["GET"])
def get_monitoring_status(hub_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM device WHERE hub_id = ? AND is_active = 1",
            (hub_id,)
        )
        active_devices = cursor.fetchone()["count"]

        return jsonify({
            "is_monitoring": active_devices > 0,
            "sound_level": 0,
            "active_devices": active_devices
        })

@app.route("/api/hubs/<int:hub_id>/monitoring/start", methods=["POST"])
def start_monitoring(hub_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE device SET is_active = 1 WHERE hub_id = ?",
            (hub_id,)
        )
        return jsonify({"message": "Monitoring started", "hub_id": hub_id})

@app.route("/api/hubs/<int:hub_id>/monitoring/stop", methods=["POST"])
def stop_monitoring(hub_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE device SET is_active = 0 WHERE hub_id = ?",
            (hub_id,)
        )
        return jsonify({"message": "Monitoring stopped", "hub_id": hub_id})

@app.route("/api/hubs/<int:hub_id>/test-alert", methods=["POST"])
def test_alert(hub_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT device_id FROM device WHERE hub_id = ? LIMIT 1",
            (hub_id,)
        )
        device_row = cursor.fetchone()
        if not device_row:
            abort(404, description="No devices found for hub")

        device_id = device_row["device_id"]

        cursor.execute(
            "INSERT INTO device_event (device_id, event_type) VALUES (?, 'TEST')",
            (device_id,)
        )
        device_event_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO alert (hub_id, device_event_id, status) VALUES (?, ?, 'pending')",
            (hub_id, device_event_id)
        )
        alert_id = cursor.lastrowid

        msg = build_alert_message("TEST")
        sms_notify_results = notify_hub_members(hub_id, msg)
        push_notify_results = notify_hub_users_push(hub_id, msg)

        return jsonify({
            "message": "Test alert created",
            "alert_id": alert_id,
            "device_event_id": device_event_id,
            "sms_notify_results": sms_notify_results,
            "push_notify_results": push_notify_results
        }), 201

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description or "Bad request"}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": error.description or "Unauthorized"}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description or "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": error.description or "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)