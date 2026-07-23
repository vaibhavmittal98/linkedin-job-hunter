---
name: deployment
description: AWS EC2 deployment, Nginx config, systemd service, and deploy workflow. Load when deploying changes, debugging server issues, or modifying infrastructure.
---

# Deployment

## Server
- **Instance:** EC2 t3.micro, eu-north-1
- **IP:** <ec2-ip>
- **Domain:** vaibing.org
- **OS:** Ubuntu 24.04
- **SSH:** `ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip>`

> **Reaching the app by raw IP won't work.** Nginx only serves the
> `vaibing.org` host; requests to the bare IP get an empty reply (connection
> accepted, no response) by design — this is **not** an outage. Always browse
> and health-check via the domain, e.g. `https://vaibing.org`.
>
> To verify a deploy from the shell, hit the backend directly on the box
> instead of going through Nginx:
> ```bash
> ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> \
>   'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/jobs'
> # 401 = up and auth-protected (expected without a token)
> ```

> The real IP and AWS account ID are **not** stored in this repo (scrubbed to
> `<ec2-ip>` / `<aws-account-id>`). Look up the live IP with the AWS CLI command
> below; keep the account ID in your local/private notes.

### Look up the current IP (if the instance restarted)
The instance is tagged `Name=linkedin-job-hunter`. On stop/start the public IP changes unless an Elastic IP is attached, so verify it live:
```bash
aws ec2 describe-instances --region eu-north-1 \
  --filters "Name=tag:Name,Values=linkedin-job-hunter" "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].PublicIpAddress" --output text
```

## Architecture
```
Internet → Nginx (port 80)
              ├── /api/*  → proxy to uvicorn (127.0.0.1:8000)
              └── /*      → serve frontend/dist/ (React SPA)
```

## Deploy Commands

### Backend only:
```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> \
  "cd ~/app && git pull && sudo systemctl restart linkedin-job-hunter"
```

### Frontend + backend:
```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> \
  "cd ~/app && git pull && cd frontend && npm run build && cd .. && sudo systemctl restart linkedin-job-hunter"
```

### Add DB column (without reset):
```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> "cd ~/app && source venv/bin/activate && python3 -c \"
from sqlalchemy import text
from app.db import engine
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE tablename ADD COLUMN colname TYPE'))
    conn.commit()
\""
```

## NEVER delete jobs.db without explicit permission.

## Database Backups (nightly → S3)
- Script `/usr/local/bin/backup-jobs-db.sh` (root), cron daily **07:00** (TZ `Europe/Berlin`), log `/var/log/jobs-db-backup.log`.
- Uses `sqlite3 .backup` (safe on live DB). Keeps newest 7 local copies in `/home/ubuntu/backups/`.
- Uploads to `s3://linkedin-job-hunter-backups-<aws-account-id>/jobs.db/` (`eu-north-1`); bucket lifecycle expires objects after 7 days. Block Public Access ON, SSE-S3.
- EC2 uses instance role `linkedin-job-hunter-backup`, scoped to **`s3:PutObject` only** on `.../jobs.db/*` (cannot list/read/delete — that's why ls/cp-down from the box is denied; use admin creds).
- Full details + restore steps: `docs/database.md`.

## Nginx Config
File: `/etc/nginx/sites-available/linkedin-job-hunter`
```nginx
server {
    listen 80;
    server_name vaibing.org;  # domain-only; raw IP access returns an empty reply by design
    root /home/ubuntu/app/frontend/dist;
    index index.html;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Systemd Service
File: `/etc/systemd/system/linkedin-job-hunter.service`
```ini
[Unit]
Description=LinkedIn Job Hunter Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/app
ExecStart=/home/ubuntu/app/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Useful Commands
```bash
# Service status
sudo systemctl status linkedin-job-hunter

# Logs (live)
sudo journalctl -u linkedin-job-hunter -f

# Restart
sudo systemctl restart linkedin-job-hunter

# Nginx errors
sudo tail -f /var/log/nginx/error.log
```

## HTTPS (pending domain)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Important Notes
- Don't restart server during active scrapes (kills background tasks)
- Schedules reload from DB on startup
- `uploads/` dir must exist (auto-created by auth.py)
- Permissions: `chmod 755 /home/ubuntu` for Nginx to read frontend
