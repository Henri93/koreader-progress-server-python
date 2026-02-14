# Simple KOReader Progress Sync Server

[![Tests](https://github.com/Henri93/koreader-progress-server-python/actions/workflows/test.yml/badge.svg)](https://github.com/Henri93/koreader-progress-server-python/actions/workflows/test.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A simple Python/FastAPI server for syncing reading progress across KOReader devices.

## Quick Start (Hosted Server)

Don't want to deploy your own? 

Just [create an account](https://www.null-space.xyz/reader) then set your KOReader or Readest app to use `https://api.null-space.xyz/reader` for progress sync.

> [!WARNING]
> **Kindle Sync Timeout Issue**
>
> If you can login from KOReader on Kindle but sync fails with "something went wrong when syncing progress", you may need to increase KOReader's sync timeout. This commonly happens when using serverless backends (like AWS Lambda) that have cold start delays. If more people use this service, I can make it more available to improve response times.
>
> **Symptoms:**
> - Login works, but push/pull progress fails/isn't working
> - KOReader debug log shows: `KOSyncClient:update_progress failure: common/Spore/Protocols.lua:85: wantread`
>
> **Fix:**
> 1. Connect your Kindle to your computer via USB
> 2. Open the file: `<Kindle>/koreader/plugins/kosync.koplugin/KOSyncClient.lua`
> 3. Find this line near the top (around line 6):
>    ```lua
>    local PROGRESS_TIMEOUTS = { 2,  5 }
>    ```
> 4. Change it to:
>    ```lua
>    local PROGRESS_TIMEOUTS = { 5, 15 }
>    ```
> 5. Save the file, eject Kindle, and restart KOReader
>
> This increases the sync timeout from 5 seconds to 15 seconds, giving the server enough time to respond during cold starts.

## Running Sync Server (Self-Hosted)

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

### AWS Lambda

Deploy as a serverless Lambda function with DynamoDB storage.

#### Prerequisites

- AWS CLI configured with credentials
- Terraform >= 1.0
- Python 3.12

#### One-Time Bootstrap

Create the shared S3 bucket for Terraform state:

```bash
cd deployment
./bootstrap.sh
```

#### Deploy

1. Create terraform variables file:

```bash
cp deployment/terraform.tfvars.example terraform/terraform.tfvars
```

2. Edit `terraform/terraform.tfvars` with your password salt:

```hcl
password_salt = "your-secure-random-salt"  # Generate with: openssl rand -hex 32
```

3. Build and deploy:

```bash
./deployment/deploy.sh
```

This creates:
- Lambda function (`reader-progress-prod`)
- DynamoDB tables (`reader-progress-prod-users`, `reader-progress-prod-progress`)
- IAM role with minimal permissions

## Configuration

### Docker / Local Development

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DB_BACKEND` | `sql` | Database backend (`sql` or `dynamodb`) |
| `PASSWORD_SALT` | `default-salt-change-me` | Salt prepended to passwords before hashing |
| `DATABASE_URL` | `sqlite:///./data/koreader.db` | SQLite/PostgreSQL database URL |

### AWS Lambda

| Environment Variable | Description |
|---------------------|-------------|
| `DB_BACKEND` | Set to `dynamodb` |
| `PASSWORD_SALT` | Salt for password hashing (set via Terraform) |
| `DYNAMODB_USERS_TABLE` | Users table name (set via Terraform) |
| `DYNAMODB_PROGRESS_TABLE` | Progress table name (set via Terraform) |
| `AWS_REGION` | AWS region (set via Terraform) |

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

### SQLite/PostgreSQL (Docker/Local)

#### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Unique username |
| password_hash | TEXT | Bcrypt hash of salted MD5 password |

#### Progress Table

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

### DynamoDB (AWS Lambda)

#### Users Table

| Attribute | Type | Key |
|-----------|------|-----|
| username | String | Partition Key |
| password_hash | String | - |

#### Progress Table

| Attribute | Type | Key |
|-----------|------|-----|
| user_id | String | Partition Key |
| document | String | Sort Key |
| progress | String | - |
| percentage | Number | - |
| device | String | - |
| device_id | String | - |
| timestamp | Number | - |

## API Reference

> **Interactive API Docs**: This server uses FastAPI which auto-generates OpenAPI documentation.
> - **Swagger UI**: `http://your-server:8080/docs` — Interactive API explorer
> - **ReDoc**: `http://your-server:8080/redoc` — Clean reference documentation
> - **OpenAPI JSON**: `http://your-server:8080/openapi.json` — Machine-readable spec

---

### Authentication

All endpoints except `/users/create`, `/health`, `/healthcheck`, and `/card/{username}` require authentication via HTTP headers:

| Header | Value | Description |
|--------|-------|-------------|
| `x-auth-user` | `<username>` | Your registered username |
| `x-auth-key` | `<md5_hash>` | MD5 hash of your password |

**Password flow:**
1. Client computes `MD5(raw_password)`
2. Client sends MD5 hash to server (in JSON body for registration, in `x-auth-key` header for auth)
3. Server stores `bcrypt(salt + md5_hash)` in database

```bash
# Generate MD5 hash of password
echo -n "mypass" | md5                      # macOS
echo -n "mypass" | md5sum | cut -d' ' -f1   # Linux
# Result: a029d0df84eb5549c641e04a9ef389e5
```

---

### Endpoints

#### Health Check

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Returns `{"status": "ok"}` |
| GET | `/healthcheck` | No | Returns `{"state": "OK"}` |

---

#### User Management

##### POST `/users/create`

Register a new user account.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `password` | string | Yes | MD5 hash of password |

```bash
curl -X POST http://localhost:8080/users/create \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "a029d0df84eb5549c641e04a9ef389e5"}'
```

| Status | Response |
|--------|----------|
| 201 | `{"status": "success"}` |
| 402 | `{"detail": "Username already exists"}` |

##### GET `/users/auth`

Verify credentials are valid.

```bash
curl http://localhost:8080/users/auth \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
```

| Status | Response |
|--------|----------|
| 200 | `{"status": "authenticated"}` |
| 401 | `{"detail": "Unauthorized"}` |

---

#### Progress Sync

##### PUT `/syncs/progress`

Update reading progress for a document.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document` | string | Yes | MD5 hash of the document file |
| `progress` | string | Yes | Reading position (XPath or page) |
| `percentage` | float | Yes | Progress 0.0–1.0 |
| `device` | string | Yes | Device name |
| `device_id` | string | Yes | Unique device identifier |
| `filename` | string | No | Book filename (used for auto-linking) |

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

| Status | Response |
|--------|----------|
| 200 | `{"status": "success"}` |

##### GET `/syncs/progress/{document}`

Retrieve the latest progress for a document.

| Parameter | Type | Description |
|-----------|------|-------------|
| `document` | string | MD5 hash of the document |

```bash
curl http://localhost:8080/syncs/progress/0b229176d4e8db7f6d2b5a4952368d7a \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
```

**Response (200):**
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

| Status | Response |
|--------|----------|
| 200 | Progress object |
| 404 | `{"detail": "Progress not found"}` |

---

#### Document Linking

Link multiple document hashes together (e.g., same book in different formats like EPUB and MOBI).

##### POST `/documents/link`

Link multiple document hashes to a canonical hash.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hashes` | string[] | Yes | Array of document hashes (min 2) |

```bash
curl -X POST http://localhost:8080/documents/link \
  -H "Content-Type: application/json" \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5" \
  -d '{"hashes": ["hash1abc", "hash2def", "hash3ghi"]}'
```

**Response (201):**
```json
{
  "canonical": "hash1abc",
  "linked": ["hash1abc", "hash2def", "hash3ghi"]
}
```

##### GET `/documents/links`

List all document links for the authenticated user.

```bash
curl http://localhost:8080/documents/links \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
```

**Response (200):**
```json
[
  {"document_hash": "hash2def", "canonical_hash": "hash1abc"},
  {"document_hash": "hash3ghi", "canonical_hash": "hash1abc"}
]
```

##### DELETE `/documents/link/{document_hash}`

Remove a document link.

```bash
curl -X DELETE http://localhost:8080/documents/link/hash2def \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
```

| Status | Response |
|--------|----------|
| 200 | `{"status": "success"}` |
| 404 | `{"detail": "Link not found"}` |

---

#### Book Management

##### GET `/books`

List all books with progress information.

```bash
curl http://localhost:8080/books \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
```

**Response (200):**
```json
{
  "books": [
    {
      "canonical_hash": "0b229176d4e8db7f6d2b5a4952368d7a",
      "linked_hashes": ["hash2def"],
      "label": "The Great Gatsby",
      "filename": "gatsby.epub",
      "progress": "/body/p[42]",
      "percentage": 0.75,
      "device": "Kindle Paperwhite",
      "device_id": "A1B2C3D4",
      "timestamp": 1706123456
    }
  ]
}
```

##### PUT `/books/label`

Set a custom label/name for a book.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `canonical_hash` | string | Yes | The book's canonical document hash |
| `label` | string | Yes | Custom display name |

```bash
curl -X PUT http://localhost:8080/books/label \
  -H "Content-Type: application/json" \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5" \
  -d '{"canonical_hash": "0b229176d4e8db7f6d2b5a4952368d7a", "label": "The Great Gatsby"}'
```

**Response (200):**
```json
{
  "canonical_hash": "0b229176d4e8db7f6d2b5a4952368d7a",
  "label": "The Great Gatsby"
}
```

##### DELETE `/books/label/{canonical_hash}`

Remove a book's custom label.

```bash
curl -X DELETE http://localhost:8080/books/label/0b229176d4e8db7f6d2b5a4952368d7a \
  -H "x-auth-user: myuser" \
  -H "x-auth-key: a029d0df84eb5549c641e04a9ef389e5"
```

| Status | Response |
|--------|----------|
| 200 | `{"status": "success"}` |
| 404 | `{"detail": "Label not found"}` |

---

#### Progress Card (Public)

##### GET `/card/{username}`

Generate an embeddable SVG progress card showing reading activity.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `username` | string | — | Username (path parameter) |
| `limit` | int | 5 | Number of books to display (query param) |

```bash
curl http://localhost:8080/card/myuser?limit=3
```

**Response:** SVG image (`image/svg+xml`)

**Embed in GitHub README:**
```markdown
![Reading Progress](https://your-server.com/reader/card/myuser)
```

## References

- [calibre](https://calibre-ebook.com/) - calibre is a powerful and easy to use e-book manager. It’s also completely free and open source and great for both casual users and computer experts.

- [koreader/koreader](https://github.com/koreader/koreader) - KOReader ebook reader application

- [koreader-calibre-plugin](https://github.com/harmtemolder/koreader-calibre-plugin) - A calibre plugin to synchronize metadata from KOReader to calibre.

- [readest](https://github.com/readest/readest) - Readest is a modern, open-source ebook reader for immersive reading. Seamlessly sync your progress, notes, highlights, and library across macOS, Windows, Linux, Android, iOS, and the Web.

Other Sync server implementations:

- [koreader/koreader-sync-server](https://github.com/koreader/koreader-sync-server) - Official Lua/OpenResty implementation
- [nperez0111/koreader-sync](https://github.com/nperez0111/koreader-sync) - TypeScript/Bun implementation
- [myelsukov/koreader-sync](https://github.com/myelsukov/koreader-sync) - Go implementation
