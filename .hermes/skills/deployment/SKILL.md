---
name: linkedin-deployment
description: Use when deploying changes, debugging server issues, or modifying infrastructure for linkedin-job-hunter. Covers EC2, Nginx, systemd, backups, and the deploy workflow.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin-job-hunter, deployment, ec2, nginx, systemd, aws]
    related_skills: [linkedin-project-overview, linkedin-database]
---

# Deployment — LinkedIn Job Hunter

## Server
- **Instance:** EC2 t3.micro, eu-north-1
- **Domain:** vaibing.org
- **OS:** Ubuntu 24.04
- **SSH key:** `~/.ssh/linkedin-job-hunter.pem`

> The real EC2 IP and AWS account ID are **not** stored in this repo (scrubbed to `<ec2-ip>` / `<aws-account-id>`). Look up the live values in `infra.local.md` (gitignored).

### Look up the current IP (if the instance restarted)
The instance is tagged `Name=linkedin-job-hunter`. On stop/start the public IP changes unless an Elastic IP is attached:
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

> Reaching the app by raw IP won't work. Nginx only serves `vaibing.org`; requests to the bare IP get an empty reply by design. Always browse and health-check via the domain.

To verify a deploy from the shell, hit the backend directly on the box:
```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> \
  'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/jobs'
# 401 = up and auth-protected (expected without a token)
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

## Nginx Config
File: `/etc/nginx/sites-available/linkedin-job-hunter`
```nginx
server {
    listen 80;
    server_name vaibing.org;
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

## Useful Server Commands
```bash
# Service status
sudo systemctl status linkedin-job-hunter

# Live logs
sudo journalctl -u linkedin-job-hunter -f

# Restart
sudo systemctl restart linkedin-job-hunter

# Nginx errors
sudo tail -f /var/log/nginx/error.log
```

## Database Backups (nightly → S3)
- Script `/usr/local/bin/backup-jobs-db.sh` (root), cron daily **07:00** (TZ `Europe/Berlin`), log `/var/log/jobs-db-backup.log`.
- Uses `sqlite3 .backup` (safe on live DB). Keeps newest 7 local copies in `/home/ubuntu/backups/`.
- Uploads to `s3://linkedin-job-hunter-backups-<aws-account-id>/jobs.db/` (`eu-north-1`); bucket lifecycle expires objects after 7 days. Block Public Access ON, SSE-S3.
- EC2 uses instance role `linkedin-job-hunter-backup`, scoped to `s3:PutObject` only (cannot list/read/delete).
- Full details + restore steps: `docs/database.md`.

## HTTPS
If domain is set up:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d vaibing.org
```

## Important Notes
- Don't restart server during active scrapes (kills background tasks)
- Schedules reload from DB on startup
- `uploads/` dir must exist (auto-created by auth.py)
- Permissions: `chmod 755 /home/ubuntu` for Nginx to read frontend

## Common Pitfalls
1. **Restarting mid-scrape** — background tasks die. Check `sudo systemctl status` before restarting.
2. **Frontend changes not showing** — forgot to run `npm run build`. A backend-only restart doesn't rebuild the SPA.
3. **Hitting the raw IP** — Nginx returns empty reply for bare IP. Always use `vaibing.org`.
4. **Bright Data from local WSL** — Cloudflare Gateway blocks `api.brightdata.com`. Test from EC2.
5. **Instance IP changed after stop/start** — use the AWS CLI lookup command above to find the new IP.