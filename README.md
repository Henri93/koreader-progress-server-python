# Simple KOReader Progress Sync Server

[![Tests](https://github.com/Henri93/koreader-progress-server-python/actions/workflows/test.yml/badge.svg)](https://github.com/Henri93/koreader-progress-server-python/actions/workflows/test.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A simple Python/FastAPI server for syncing reading progress across KOReader devices.

## Running Sync Server

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

1. Open a book in KOReader
2. Open the menu (swipe down from top) and tap the settings icon (wrench)
3. Select **Progress sync** > **Custom sync server** > enter your server URL (e.g., `http://your-server:8080`)
4. Select **Register** or **Login** and enter your credentials
5. Select **Push progress from this device** to test
6. *optional* Enable **Auto sync** for automatic progress updates when opening/closing books

## iOS Setup

Since, iOS doesn't seem to have a KOReader app I could find, I went with [Readest](https://readest.com/) which supports KOReader progress sync.

1. Open Readest
2. Open a book(I used Calibre content server's OPDS library to sync book files across devices)
3. Open book menu table of contents in the bottom left(bullet list icon)
4. Select hamburger menu in the top right > Select KOReader Sync
5. Enter enter your server URL (e.g., `http://your-server:8080`) and credentials

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
| password_hash | TEXT | Bcrypt hash of salted MD5 password |

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
x-auth-key: <md5_hash_of_password>
```

**Note:** KOReader sends passwords as MD5 hashes. When using curl or other clients, you must send the MD5 hash of the password, not the raw password.

```bash
# Generate MD5 hash of password
echo -n "mypass" | md5  # macOS
echo -n "mypass" | md5sum | cut -d' ' -f1  # Linux
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
# MD5 of "mypass" is a029d0df84eb5549c641e04a9ef389e5
curl http://localhost:8080/users/auth \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
```

Response: `{"status": "authenticated"}` (200) or `{"detail": "Unauthorized"}` (401)

#### PUT /syncs/progress
Update reading progress for a document.

```bash
curl -X PUT http://localhost:8080/syncs/progress \
  -H "Content-Type: application/json" \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5" \
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
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
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

## References

- [calibre](https://calibre-ebook.com/) - calibre is a powerful and easy to use e-book manager. It’s also completely free and open source and great for both casual users and computer experts.

- [koreader/koreader](https://github.com/koreader/koreader) - KOReader ebook reader application

- [koreader-calibre-plugin](https://github.com/harmtemolder/koreader-calibre-plugin) - A calibre plugin to synchronize metadata from KOReader to calibre.

- [readest](https://github.com/readest/readest) - Readest is a modern, open-source ebook reader for immersive reading. Seamlessly sync your progress, notes, highlights, and library across macOS, Windows, Linux, Android, iOS, and the Web.

Other Sync server implementations:

- [koreader/koreader-sync-server](https://github.com/koreader/koreader-sync-server) - Official Lua/OpenResty implementation
- [nperez0111/koreader-sync](https://github.com/nperez0111/koreader-sync) - TypeScript/Bun implementation
- [myelsukov/koreader-sync](https://github.com/myelsukov/koreader-sync) - Go implementation
