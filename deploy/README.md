# Trade System Deployment Guide

## 구조

```
deploy/
├── registry/           # Docker Registry 설정
│   ├── docker-compose.yml
│   └── setup.sh
├── production/         # Production 배포 파일
│   ├── docker-compose.yml
│   ├── deploy.sh
│   ├── rollback.sh
│   └── .env.example
└── README.md
```

## 초기 설정 (Hetzner 서버)

### 1. Docker Registry 설치

```bash
# 서버에 SSH 접속
ssh user@your-hetzner-server

# Registry 설치
cd /opt
git clone https://github.com/yourusername/trade.git
cd trade/deploy/registry
sudo ./setup.sh
```

### 2. Production 환경 설정

```bash
# Production 디렉토리 생성
sudo mkdir -p /opt/trade
cd /opt/trade

# 파일 복사
sudo cp /path/to/deploy/production/* .

# 환경변수 설정
sudo cp .env.example .env
sudo nano .env  # 실제 값으로 수정
```

## CI/CD 워크플로우

### CI (자동)

1. 코드를 GitHub에 Push
2. GitHub Actions가 자동으로:
   - 테스트 실행
   - Docker 이미지 빌드
   - Registry에 이미지 Push

### CD (수동)

1. 서버에 SSH 접속
2. 배포 스크립트 실행:
   ```bash
   cd /opt/trade
   sudo ./deploy.sh
   ```

## GitHub Secrets 설정

GitHub 저장소 Settings > Secrets에 추가:

- `HETZNER_REGISTRY_URL`: registry.yourdomain.com:5000
- `HETZNER_REGISTRY_USER`: admin
- `HETZNER_REGISTRY_PASSWORD`: 비밀번호
- `VECTORBT_TOKEN`: VectorBT Pro 토큰

## 운영 명령어

### 서비스 상태 확인
```bash
docker-compose ps
docker-compose logs -f [service_name]
```

### 특정 서비스만 재시작
```bash
docker-compose restart trade_batch
```

### 롤백
```bash
./rollback.sh /opt/trade/backups/20240101_120000
```

### Registry 관리
```bash
# 이미지 목록
curl -X GET https://registry.yourdomain.com:5000/v2/_catalog -u admin

# 가비지 컬렉션
docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml
```

## 문제 해결

### Registry 연결 실패
1. 방화벽 확인: `sudo ufw status`
2. SSL 인증서 확인: `sudo certbot certificates`
3. Registry 로그 확인: `docker logs registry`

### 배포 실패
1. 디스크 공간 확인: `df -h`
2. Docker 이미지 정리: `docker system prune -a`
3. 이전 버전으로 롤백: `./rollback.sh [backup_dir]`

## 보안 권장사항

1. **SSH 보안**
   - 키 기반 인증만 사용
   - fail2ban 설치
   - 비표준 포트 사용

2. **Registry 보안**
   - HTTPS 필수
   - 강한 비밀번호 사용
   - IP 화이트리스트 설정

3. **정기 유지보수**
   - 주기적인 보안 업데이트
   - 로그 모니터링
   - 백업 확인