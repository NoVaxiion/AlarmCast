PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT UNIQUE,
  password_hash TEXT,
  password_algo TEXT
);

CREATE TABLE IF NOT EXISTS hub (
    hub_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    hub_name        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS member (
  member_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hub_id    INTEGER NOT NULL,
  name      TEXT,
  phone     TEXT,
  role      TEXT NOT NULL DEFAULT 'member'
            CHECK (role IN ('member', 'owner')),
  user_id   INTEGER,
  FOREIGN KEY (hub_id) REFERENCES hub(hub_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
  UNIQUE (hub_id, user_id)
);

CREATE TABLE IF NOT EXISTS device (
  device_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  hub_id     INTEGER NOT NULL,
  is_active  INTEGER DEFAULT 1,
  is_initialized INTEGER DEFAULT 0,
  FOREIGN KEY (hub_id) REFERENCES hub(hub_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_event (
  device_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id       INTEGER NOT NULL,
  event_type      TEXT NOT NULL
                  CHECK (event_type IN ('SMOKE', 'CO', 'TEST')),
  detected_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (device_id) REFERENCES device(device_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alert (
  alert_id       INTEGER PRIMARY KEY AUTOINCREMENT,
  hub_id         INTEGER NOT NULL,
  device_event_id INTEGER NOT NULL,
  status         TEXT DEFAULT 'pending',
  FOREIGN KEY (hub_id) REFERENCES hub(hub_id) ON DELETE CASCADE,
  FOREIGN KEY (device_event_id) REFERENCES device_event(device_event_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alert_delivery (
  alert_delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
  alert_id          INTEGER NOT NULL,
  member_id         INTEGER NOT NULL,
  status            TEXT DEFAULT 'pending',
  FOREIGN KEY (alert_id) REFERENCES alert(alert_id) ON DELETE CASCADE,
  FOREIGN KEY (member_id) REFERENCES member(member_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_calibration (
  calibration_id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id      INTEGER NOT NULL,
  event_type     TEXT NOT NULL,
  audio_uri      TEXT,
  features       TEXT,
  status         TEXT DEFAULT 'pending',
  FOREIGN KEY (device_id) REFERENCES device(device_id) ON DELETE CASCADE
);
