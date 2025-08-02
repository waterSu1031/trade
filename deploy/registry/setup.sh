#!/bin/bash

# Docker Registry 설치 스크립트
# Hetzner 서버에서 실행

set -e

echo "=== Docker Registry Setup Script ==="
echo

# 1. 디렉토리 생성
echo "Creating directories..."
mkdir -p /opt/docker-registry/{data,auth,certs}
cd /opt/docker-registry

# 2. docker-compose.yml 복사
echo "Copying docker-compose.yml..."
cp /path/to/this/docker-compose.yml .

# 3. 인증 설정
echo "Setting up authentication..."
read -p "Enter registry username: " REGISTRY_USER
docker run --rm --entrypoint htpasswd registry:2 -Bbn "$REGISTRY_USER" | tee auth/htpasswd

# 4. SSL 인증서 설정
echo "Setting up SSL certificates..."
read -p "Enter your domain (e.g., registry.example.com): " DOMAIN

# Let's Encrypt 인증서 생성
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot
fi

# 인증서 생성
certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"

# 심볼릭 링크 생성
ln -sf /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem certs/cert.pem
ln -sf /etc/letsencrypt/live/"$DOMAIN"/privkey.pem certs/key.pem

# 5. 방화벽 설정
echo "Setting up firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 5000/tcp comment "Docker Registry"
    ufw allow 5001/tcp comment "Registry UI"
fi

# 6. 자동 인증서 갱신 설정
echo "Setting up auto-renewal..."
cat > /etc/cron.d/certbot-registry << EOF
0 2 * * * root certbot renew --quiet && docker-compose -f /opt/docker-registry/docker-compose.yml restart registry
EOF

# 7. Registry 시작
echo "Starting Docker Registry..."
docker-compose up -d

# 8. 테스트
echo
echo "Testing registry..."
sleep 5
if curl -k https://localhost:5000/v2/ -u "$REGISTRY_USER"; then
    echo "Registry is working!"
else
    echo "Registry test failed!"
    exit 1
fi

echo
echo "=== Setup Complete ==="
echo "Registry URL: https://$DOMAIN:5000"
echo "Registry UI: http://$DOMAIN:5001"
echo
echo "To test from remote:"
echo "docker login $DOMAIN:5000"
echo
echo "GitHub Secrets to add:"
echo "HETZNER_REGISTRY_URL=$DOMAIN:5000"
echo "HETZNER_REGISTRY_USER=$REGISTRY_USER"
echo "HETZNER_REGISTRY_PASSWORD=<your-password>"