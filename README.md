# Email Hub API Backend - Microservice

Backend API berbasis FastAPI sebagai microservice untuk email hub multi-user dengan integrasi webhook. Dirancang untuk bekerja dengan aplikasi utama yang menangani autentikasi user.

## Fitur

- ✅ **Microservice Architecture** - Integrasi dengan main app melalui API
- ✅ **API Key Authentication** - Menggunakan API key dari main app
- ✅ **Dukungan Multi-user** - Setiap user dapat mengelola beberapa akun email
- ✅ **Integrasi IMAP/SMTP** - Hubungkan akun email apapun dengan IMAP/SMTP
- ✅ **Polling Email Otomatis** - Background worker memeriksa email setiap 2 menit
- ✅ **Integrasi Webhook** - Teruskan email yang diterima ke URL webhook custom
- ✅ **Kirim & Balas** - Kirim email baru dan balas email yang diterima
- ✅ **SQLite/PostgreSQL** - Mendukung database SQLite dan PostgreSQL

## Arsitektur Microservice

```
Main App                          Email Hub Microservice
├── User Registration      ──────> POST /users (buat user baru)
├── User Authentication           
├── API Key Generation     ──────> Header: X-API-Key
└── User Management        ──────> PUT /users/{id}/api-key
                                   DELETE /users/{id}

                                  Email Hub Features:
                                  ├── Email Account Management
                                  ├── Email Polling (Background)
                                  ├── Webhook Forwarding
                                  └── Send/Reply Operations
```

## Instalasi

### 1. Clone atau Buat Proyek

```bash
mkdir email-hub-api
cd email-hub-api
```

### 2. Buat Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Di Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment

```bash
cp .env.example .env
# Edit .env dan atur DATABASE_URL Anda
```

### 5. Jalankan Aplikasi

```bash
python main.py
```

API akan tersedia di `http://localhost:8000`

## Dokumentasi API

Setelah berjalan, kunjungi:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Integrasi dengan Main App

### 1. Buat User di Microservice (dari Main App)

Ketika user baru registrasi di main app, panggil endpoint ini:

```python
# Di main app setelah user register
import httpx

async def create_email_hub_user(user_id: str, email: str, api_key: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://email-hub-service:8000/users",
            json={
                "external_user_id": user_id,
                "email": email,
                "api_key": api_key,
                "full_name": "John Doe"
            }
        )
    return response.json()
```

### 2. Update API Key (ketika user generate API key baru)

```python
async def update_email_hub_api_key(user_id: str, new_api_key: str):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"http://email-hub-service:8000/users/{user_id}/api-key",
            params={"new_api_key": new_api_key}
        )
    return response.json()
```

### 3. Hapus User (ketika user dihapus dari main app)

```python
async def delete_email_hub_user(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"http://email-hub-service:8000/users/{user_id}"
        )
    return response.json()
```

## Panduan Penggunaan untuk End User

### 1. Tambahkan Akun Email

User menggunakan API key dari main app:

```bash
curl -X POST "http://localhost:8000/email-accounts" \
  -H "X-API-Key: USER_API_KEY_FROM_MAIN_APP" \
  -H "Content-Type: application/json" \
  -d '{
    "email_address": "myemail@gmail.com",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "password": "your-app-password",
    "webhook_url": "https://your-main-app.com/webhooks/email-received"
  }'
```

**Catatan untuk Gmail**: Anda perlu menggunakan App Password, bukan password biasa. Generate di: https://myaccount.google.com/apppasswords

### 2. Lihat Daftar Email yang Diterima

```bash
curl -X GET "http://localhost:8000/emails?limit=10" \
  -H "X-API-Key: USER_API_KEY_FROM_MAIN_APP"
```

### 3. Kirim Balasan

```bash
curl -X POST "http://localhost:8000/emails/reply" \
  -H "X-API-Key: USER_API_KEY_FROM_MAIN_APP" \
  -H "Content-Type: application/json" \
  -d '{
    "original_email_id": 1,
    "body": "Terima kasih atas emailnya. Saya akan segera merespons."
  }'
```

### 4. Kirim Email Baru

```bash
curl -X POST "http://localhost:8000/emails/send?account_id=1&to_addr=recipient@example.com&subject=Halo&body=Ini adalah email test" \
  -H "X-API-Key: USER_API_KEY_FROM_MAIN_APP"
```

## Pengaturan Provider Email

### Gmail
- **IMAP**: imap.gmail.com:993
- **SMTP**: smtp.gmail.com:587
- **Catatan**: Gunakan App Password

### Outlook/Hotmail
- **IMAP**: outlook.office365.com:993
- **SMTP**: smtp.office365.com:587

### Yahoo
- **IMAP**: imap.mail.yahoo.com:993
- **SMTP**: smtp.mail.yahoo.com:587

### IMAP/SMTP Custom
- Cek dokumentasi provider email Anda

## Integrasi Webhook

Ketika email diterima, microservice otomatis mengirim POST request ke webhook_url yang dikonfigurasi dengan payload ini:

```json
{
  "id": 123,
  "message_id": "<unique-message-id@server.com>",
  "sender": "sender@example.com",
  "recipient": "your-email@example.com",
  "subject": "Judul Email",
  "body": "Isi email plain text",
  "html_body": "<html>Isi email HTML</html>",
  "received_at": "2025-10-23T10:30:00"
}
```

Main app Anda dapat menangkap webhook ini dan memproses sesuai kebutuhan.

## Deployment

### Docker Compose (Recommended)

```yaml
version: '3.8'

services:
  email-hub:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/email_hub
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=email_hub
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: email-hub
spec:
  replicas: 2
  selector:
    matchLabels:
      app: email-hub
  template:
    metadata:
      labels:
        app: email-hub
    spec:
      containers:
      - name: email-hub
        image: your-registry/email-hub:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: email-hub-secrets
              key: database-url
```

## Struktur Proyek

```
email-hub-api/
├── main.py              # Aplikasi FastAPI dan endpoints
├── database.py          # Konfigurasi database
├── models.py            # Model SQLAlchemy
├── schemas.py           # Schema Pydantic
├── auth.py              # Logic autentikasi API key
├── email_service.py     # Operasi IMAP/SMTP
├── background_tasks.py  # Worker polling email
├── requirements.txt     # Dependencies Python
├── .env.example         # Template environment variables
└── README.md            # File ini
```

## Endpoint API

### User Management (Internal - untuk Main App)
- `POST /users` - Buat user baru
- `PUT /users/{external_user_id}/api-key` - Update API key
- `DELETE /users/{external_user_id}` - Hapus user

### Akun Email (untuk End User)
- `POST /email-accounts` - Tambah akun email
- `GET /email-accounts` - Lihat daftar akun email
- `DELETE /email-accounts/{id}` - Hapus akun email

### Operasi Email (untuk End User)
- `GET /emails` - Lihat daftar email yang diterima
- `POST /emails/send` - Kirim email baru
- `POST /emails/reply` - Balas email

### Webhooks
- `POST /webhooks/email-received` - Terima email dari layanan eksternal

### Health
- `GET /health` - Health check

## Keamanan

⚠️ **PENTING untuk Production:**

1. **Enkripsi password email** - Gunakan Fernet atau enkripsi serupa
2. **HTTPS only** - Selalu gunakan SSL/TLS
3. **Rate limiting** - Tambahkan rate limiting
4. **Network isolation** - Jalankan di private network
5. **Secret management** - Gunakan secret managers (Vault, AWS Secrets Manager)
6. **Backup database** - Backup rutin
7. **Monitoring** - Setup logging dan monitoring
8. **Input validation** - Validasi semua input

## Troubleshooting

### Error Gmail "Less secure app"
- Gunakan App Password
- Aktifkan 2FA terlebih dahulu
- Generate App Password di: https://myaccount.google.com/apppasswords

### Email tidak diterima
- Cek status akun: `GET /email-accounts`
- Verifikasi kredensial IMAP
- Cek logs aplikasi
- Background worker polling setiap 2 menit

### Webhook tidak terkirim
- Verifikasi webhook URL accessible
- Cek logs server webhook
- Test manual dengan curl

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# Lihat logs background worker
tail -f /var/log/email-hub.log
```

## Pengembangan Selanjutnya

- [ ] Dukungan attachment email
- [ ] Template email
- [ ] Filtering dan rules
- [ ] Pencarian email
- [ ] Manajemen folder
- [ ] OAuth2 untuk Gmail/Outlook