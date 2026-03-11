/* USERS --> is for APP USERS, all OWNERS need the app, not all MEMBERS need app*/
CREATE TABLE IF NOT EXISTS users (
  user_id SERIAL PRIMARY KEY,
  username TEXT UNIQUE,
  password_hash TEXT,
  password_algo TEXT,
  expo_push_token TEXT,
  expo_push_token_updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hub (
  hub_id SERIAL PRIMARY KEY,
  hub_name TEXT NOT NULL
);

/* MEMBERS --> is for ALL PEOPLE, both OWNERS & MEMBERS*/
CREATE TABLE IF NOT EXISTS member (
  member_id SERIAL PRIMARY KEY,
  hub_id INTEGER NOT NULL,
  name TEXT,
  phone TEXT,
  carrier TEXT NOT NULL CHECK (carrier IN ('verizon','att','tmobile')),
  role TEXT NOT NULL DEFAULT 'member'
       CHECK (role IN ('member', 'owner')),
  user_id INTEGER,
  FOREIGN KEY (hub_id) REFERENCES hub(hub_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
  UNIQUE (hub_id, user_id)
);

CREATE TABLE IF NOT EXISTS device (
  device_id SERIAL PRIMARY KEY,
  hub_id INTEGER NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  is_initialized BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (hub_id) REFERENCES hub(hub_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_event (
  device_event_id SERIAL PRIMARY KEY,
  device_id INTEGER NOT NULL,
  event_type TEXT NOT NULL
            CHECK (event_type IN ('SMOKE', 'CO', 'TEST')),
  detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (device_id) REFERENCES device(device_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alert (
  alert_id SERIAL PRIMARY KEY,
  hub_id INTEGER NOT NULL,
  device_event_id INTEGER NOT NULL,
  status TEXT DEFAULT 'pending',
  FOREIGN KEY (hub_id) REFERENCES hub(hub_id) ON DELETE CASCADE,
  FOREIGN KEY (device_event_id) REFERENCES device_event(device_event_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alert_delivery (
  alert_delivery_id SERIAL PRIMARY KEY,
  alert_id INTEGER NOT NULL,
  member_id INTEGER NOT NULL,
  status TEXT DEFAULT 'pending',
  FOREIGN KEY (alert_id) REFERENCES alert(alert_id) ON DELETE CASCADE,
  FOREIGN KEY (member_id) REFERENCES member(member_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_calibration (
  calibration_id SERIAL PRIMARY KEY,
  device_id INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  audio_uri TEXT,
  features TEXT,
  status TEXT DEFAULT 'pending',
  FOREIGN KEY (device_id) REFERENCES device(device_id) ON DELETE CASCADE
);