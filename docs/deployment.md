# Deployment Guide (AWS EC2)

> **Note:** The `.kiro/` directory (agent skills) is intentionally **not** pushed to the repo — it is local-only and gitignored. It will not be present on the server after a `git pull`, and a fresh checkout won't include it.

## Infrastructure

| Resource | Details |
|----------|---------|
| Instance | t3.micro (free tier eligible) |
| OS | Ubuntu 24.04 LTS |
| Region | eu-north-1 (Stockholm) |
| Storage | 20GB gp3 EBS |
| Public IP | (hidden — access via vaibing.org) |
| Key pair | `linkedin-job-hunter` (stored at `~/.ssh/linkedin-job-hunter.pem`) |
| Security group | `linkedin-job-hunter-sg` — ports 22, 80, 443 open |

## Architecture on Server

```
Internet → Nginx (port 80)
              ├── /api/*  → proxy to uvicorn (port 8000)
              └── /*      → serve frontend/dist/ (React static files)
```

## Server Setup (already done)

### 1. Launch EC2

```bash
aws ec2 run-instances \
  --image-id ami-0930f12db303154e9 \
  --instance-type t3.micro \
  --key-name linkedin-job-hunter \
  --security-group-ids sg-0b35b11d65407e6e7 \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=linkedin-job-hunter}]' \
  --region eu-north-1
```

### 2. SSH In

```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip>
```

### 3. Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nodejs npm git nginx
```

### 4. Clone & Setup

```bash
git clone https://github.com/vaibhavmittal98/linkedin-job-hunter.git ~/app
cd ~/app
chmod +x setup.sh run.sh
./setup.sh
```

### 5. Configure Environment

```bash
# Copy .env from local machine:
scp -i ~/.ssh/linkedin-job-hunter.pem /path/to/.env ubuntu@<ec2-ip>:~/app/.env

# Or edit directly:
nano ~/app/.env
```

### 6. Build Frontend for Production

```bash
cd ~/app/frontend
npm run build
```

### 7. Nginx Configuration

File: `/etc/nginx/sites-available/linkedin-job-hunter`

```nginx
# Block direct IP access
server {
    listen 80 default_server;
    listen 443 ssl default_server;
    ssl_certificate /etc/ssl/certs/vaibing.crt;
    ssl_certificate_key /etc/ssl/private/vaibing.key;
    server_name _;
    return 444;
}

# Serve app only via domain (Cloudflare)
server {
    listen 80;
    listen 443 ssl;
    server_name vaibing.org www.vaibing.org;

    ssl_certificate /etc/ssl/certs/vaibing.crt;
    ssl_certificate_key /etc/ssl/private/vaibing.key;

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

Enable it:
```bash
sudo ln -sf /etc/nginx/sites-available/linkedin-job-hunter /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Fix Permissions

```bash
chmod 755 /home/ubuntu
chmod -R 755 /home/ubuntu/app/frontend/dist
```

### 9. Systemd Service

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
Environment=PATH=/home/ubuntu/app/venv/bin:/usr/bin

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linkedin-job-hunter
sudo systemctl start linkedin-job-hunter
```

## Deploying Updates

### Backend changes only:
```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> \
  "cd ~/app && git pull && sudo systemctl restart linkedin-job-hunter"
```

### Frontend + backend changes:
```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> \
  "cd ~/app && git pull && cd frontend && npm run build && cd .. && sudo systemctl restart linkedin-job-hunter"
```

## Useful Commands

```bash
# SSH into server
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip>

# Check service status
sudo systemctl status linkedin-job-hunter

# View backend logs
sudo journalctl -u linkedin-job-hunter -f

# Restart backend
sudo systemctl restart linkedin-job-hunter

# Restart nginx
sudo systemctl restart nginx

# Check nginx errors
sudo tail -f /var/log/nginx/error.log
```

## HTTPS (Cloudflare)

Domain: `vaibing.org` (Cloudflare Registrar)

### DNS Setup (already done)
- A record: `@` → `<ec2-ip>` (Proxied)

### How it works
```
User → HTTPS → Cloudflare (valid SSL) → HTTPS → EC2 (self-signed cert) → Nginx → App
```

- Cloudflare handles the public SSL certificate for visitors
- Server has a self-signed cert (10-year validity) for Cloudflare-to-origin connection
- Cloudflare SSL mode: Full (default)

### Self-signed cert (already on server)
```bash
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/ssl/private/vaibing.key \
  -out /etc/ssl/certs/vaibing.crt \
  -subj "/CN=vaibing.org"
```

### Nginx listens on both 80 and 443
No Certbot needed — Cloudflare handles public SSL.

## Cost

| Resource | Free tier (12 months) | After free tier |
|----------|----------------------|-----------------|
| t3.micro (750h/mo) | $0 | ~$7.60/month |
| 20GB EBS | $0 (30GB free) | ~$1.60/month |
| Data transfer | $0 (100GB free) | Minimal |
| **Total** | **$0/month** | **~$9-10/month** |
