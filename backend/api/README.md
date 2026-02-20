# AlarmCast API

Flask backend for the AlarmCast fire alarm monitoring system.

## Setup

1. Install dependencies:
```bash
pip install -r ../requirements.txt
```

2. Run the server:
```bash
python main.py
```

Or using Flask's development server:
```bash
flask --app main run --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Network Configuration

### For Raspberry Pi Connection (Socket Server)

The socket server in `util.py` accepts audio connections from Raspberry Pi devices.

**On the laptop (server):**
1. Find your laptop's IP address:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Mac/Linux: `ifconfig` or `ip addr`
   - Example: `192.168.1.100`

2. Run the socket server:
```bash
cd backend/api
python util.py
```

The server binds to `0.0.0.0:65432` by default, accepting connections from any network interface.

**On the Raspberry Pi (client):**
1. Set the laptop's IP address as an environment variable:
```bash
export SOCKET_HOST="192.168.1.100"  # Replace with your laptop's IP
export SOCKET_PORT="65432"
```

2. Run the Pi client:
```bash
python util.py
```

### For Expo App Connection (Flask API)

The Flask API server runs on `0.0.0.0:8000` by default, making it accessible from:
- Localhost: `http://localhost:8000`
- Network: `http://<laptop-ip>:8000`

**For Expo app on the same laptop:**
- Use `http://localhost:8000` or `http://127.0.0.1:8000`

**For Expo app on a different device (phone/tablet):**
- Use `http://<laptop-ip>:8000` (e.g., `http://192.168.1.100:8000`)
- Make sure your laptop and mobile device are on the same network
- Ensure your laptop's firewall allows incoming connections on port 8000

## API Documentation

The API follows RESTful conventions. All endpoints return JSON responses.

## Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user

### Hubs
- `POST /api/hubs` - Create a hub
- `GET /api/hubs/{hub_id}` - Get a specific hub

### Members/Contacts
- `POST /api/hubs/{hub_id}/members` - Add a member/contact
- `GET /api/hubs/{hub_id}/members` - Get all members for a hub
- `DELETE /api/members/{member_id}` - Delete a member

### Devices
- `POST /api/hubs/{hub_id}/devices` - Create a device
- `GET /api/hubs/{hub_id}/devices` - Get all devices for a hub

### Device Events
- `POST /api/devices/{device_id}/events` - Create a device event (SMOKE, CO, TEST)

### Alerts
- `POST /api/alerts` - Create an alert
- `GET /api/hubs/{hub_id}/alerts` - Get alert history for a hub

### Monitoring/Dashboard
- `GET /api/hubs/{hub_id}/monitoring/status` - Get monitoring status
- `POST /api/hubs/{hub_id}/monitoring/start` - Start monitoring
- `POST /api/hubs/{hub_id}/monitoring/stop` - Stop monitoring
- `POST /api/hubs/{hub_id}/test-alert` - Create a test alert

## Database

The API uses SQLite by default. The database file is created at `alarmcast.db` in the project root (configurable via `DATABASE_PATH` environment variable).

The database schema is automatically initialized from `firealarm/src/db/schema.sql` on startup.

## CORS

CORS is enabled for all origins by default. In production, you should restrict this to specific origins.

## Troubleshooting

### Pi can't connect to laptop
- Verify both devices are on the same network
- Check laptop's firewall allows port 65432
- Verify laptop's IP address is correct
- Test connection: `telnet <laptop-ip> 65432` from Pi

### Expo app can't reach API
- Verify laptop's IP address
- Check laptop's firewall allows port 8000
- For Expo Go, ensure you're using the laptop's IP, not localhost
- Test in browser: `http://<laptop-ip>:8000/health`
