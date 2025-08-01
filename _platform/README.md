# Trade System Platform

이 디렉토리는 Trade System의 모든 플랫폼 관련 리소스를 포함합니다.

## 디렉토리 구조

```
_platform/
├── infra/          # 인프라스트럭처 및 운영
│   ├── docker/     # Docker 관련 설정
│   ├── configs/    # 시스템 설정 파일
│   ├── scripts/    # 운영 스크립트
│   └── volumes/    # 데이터 볼륨 (Git 제외)
│
├── docs/           # 프로젝트 문서
│   ├── API_DOCUMENTATION.md
│   ├── INFRASTRUCTURE.md
│   ├── OPERATIONS.md
│   └── ...
│
├── schemas/        # 공통 스키마 정의
│   ├── database/   # DB 스키마
│   ├── api/        # API 스펙
│   └── events/     # 이벤트 스키마
│
├── templates/      # 프로젝트 템플릿
│   ├── api-spec/   # API 명세 템플릿
│   └── docs/       # 문서 템플릿
│
└── tools/          # 개발 도구
    ├── git-hooks/  # Git 훅
    └── linters/    # 코드 검사 도구
```

## 주요 구성 요소

### 1. Infrastructure (infra/)
- Docker Compose 설정
- PostgreSQL, Redis 설정
- 백업/복원 스크립트
- 모니터링 설정

### 2. Documentation (docs/)
- 시스템 아키텍처 문서
- API 문서
- 운영 가이드
- 개발 가이드

### 3. Schemas (schemas/)
- 데이터베이스 스키마 정의
- API 인터페이스 정의
- 이벤트 스키마 정의

### 4. Templates (templates/)
- 새 서비스 추가 시 사용할 템플릿
- 문서 작성 템플릿

### 5. Tools (tools/)
- 개발 생산성 도구
- 코드 품질 관리 도구

## 사용 방법

### 인프라 관리
```bash
# 인프라 시작
make start-infra

# 인프라 중지
make stop-infra

# 데이터베이스 백업
make db-backup

# 데이터베이스 복원
make db-restore BACKUP_FILE=backup.sql
```

### 문서 접근
모든 프로젝트 문서는 `docs/` 디렉토리에서 찾을 수 있습니다.

### 스키마 사용
공통 스키마는 각 서비스에서 import하여 사용합니다:
```python
from _platform.schemas.database import UserSchema
```

## 관리 지침

1. **인프라 변경**: infra/ 하위의 설정 변경 시 모든 서비스에 영향을 줄 수 있으므로 주의
2. **스키마 변경**: schemas/ 변경 시 관련된 모든 서비스 업데이트 필요
3. **문서 업데이트**: 시스템 변경 시 관련 문서도 함께 업데이트

## 기여 방법

1. 새로운 도구나 템플릿 추가 시 적절한 디렉토리에 배치
2. 문서는 Markdown 형식으로 작성
3. 스크립트는 실행 권한 설정 (`chmod +x`)
4. 변경사항은 PR을 통해 리뷰 후 병합