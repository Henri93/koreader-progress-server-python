# Simple KOReader Progress Sync Server

[![Tests](https://github.com/Henri93/koreader-progress-server-python/actions/workflows/test.yml/badge.svg)](https://github.com/Henri93/koreader-progress-server-python/actions/workflows/test.yml)

A simple Python/FastAPI server for syncing reading progress across KOReader devices.

## How It Works

### Multi-User Model

Each user has their own isolated account with separate reading progress data. Users authenticate via HTTP headers on every request, and progress is stored per-user, per-document.

```
User A (kindle)     User A (phone)      User B (tablet)
     │                   │                    │
     └───────┬───────────┘                    │
             │                                │
      User A's Progress                User B's Progress
      ┌─────────────┐                  ┌─────────────┐
      │ book1: 25%  │                  │ book1: 80%  │
      │ book2: 50%  │                  │ book3: 10%  │
      └─────────────┘                  └─────────────┘
```

### Progress Sync Flow

1. **Device reads a book** - KOReader calculates a document hash (MD5 of the file) and tracks reading position
2. **Device uploads progress** - Sends document hash, XPath position, percentage, and device info
3. **Another device opens same book** - Queries server using the same document hash
4. **Server returns latest progress** - Device can jump to the synced position

The document hash ensures the same book is identified across devices regardless of filename.

## Database Structure

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Unique username |
| password_hash | TEXT | Bcrypt hash of salted password |

### Progress Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key to users.id |
| document | TEXT | MD5 hash of the document |
| progress | TEXT | XPath position (e.g., `/body/p[42]`) |
| percentage | REAL | Reading progress 0.0-1.0 |
| device | TEXT | Device name (e.g., "Kindle Paperwhite") |
| device_id | TEXT | Unique device identifier |
| timestamp | INTEGER | Unix timestamp of last update |

**Key constraint**: One progress record per (user_id, document) pair. Updates replace existing records.

## API Reference

### Authentication

All endpoints except `/users/create` and `/health` require authentication via headers:

```
x-auth-user: <username>
x-auth-key: <password>
```

### Endpoints

#### POST /users/create
Register a new user account.

```bash
curl -X POST http://localhost:8080/users/create \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypass"}'
```

Response: `{"status": "success"}` (201) or `{"detail": "Username already exists"}` (402)

#### GET /users/auth
Verify credentials are valid.

```bash
curl http://localhost:8080/users/auth \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: mypass"
```

Response: `{"status": "authenticated"}` (200) or `{"detail": "Unauthorized"}` (401)

#### PUT /syncs/progress
Update reading progress for a document.

```bash
curl -X PUT http://localhost:8080/syncs/progress \
  -H "Content-Type: application/json" \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: mypass" \
  -d '{
    "document": "0b229176d4e8db7f6d2b5a4952368d7a",
    "progress": "/body/DocFragment[42]/body/p[3]/text().0",
    "percentage": 0.25,
    "device": "Kindle Paperwhite",
    "device_id": "A1B2C3D4"
  }'
```

Response: `{"status": "success"}` (200)

#### GET /syncs/progress/{document}
Retrieve the latest progress for a document.

```bash
curl http://localhost:8080/syncs/progress/0b229176d4e8db7f6d2b5a4952368d7a \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: mypass"
```

Response:
```json
{
  "document": "0b229176d4e8db7f6d2b5a4952368d7a",
  "progress": "/body/DocFragment[42]/body/p[3]/text().0",
  "percentage": 0.25,
  "device": "Kindle Paperwhite",
  "device_id": "A1B2C3D4",
  "timestamp": 1706123456
}
```

#### GET /health, GET /healthcheck
Health check endpoints for monitoring.

## Running

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### Docker

```bash
docker compose up -d
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| PASSWORD_SALT | `default-salt-change-me` | Salt prepended to passwords before hashing |
| DATABASE_URL | `sqlite:///./data/koreader.db` | SQLite database path |

## KOReader Setup

1. Go to: Settings > Cloud storage > Progress sync
2. Set sync server to: `http://your-server:8080`
3. Register or login with your credentials
4. Enable "Auto sync" for automatic progress updates
