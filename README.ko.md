[English](README.md) | **한국어**

# pg-mig-webui

PostgreSQL(PostGIS / pgRouting 포함) 데이터베이스를 웹 UI에서 클릭 한 번으로 이관하는 도구입니다.
OpenVPN을 통해서만 접근 가능한 서버도 지원합니다.

## 실행 방법

### 1. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 `ENCRYPTION_KEY`와 `JWT_SECRET`을 채웁니다. 생성 명령어는 파일 내 주석에 포함되어 있습니다.

### 2. 서비스 시작

```bash
docker compose up -d
```

### 3. 브라우저 접속

`http://localhost` 에 접속합니다.

1. 회원가입 후 로그인 — 가장 먼저 가입한 계정이 자동으로 관리자(admin)가 됩니다
2. DB 접속 정보 추가 — VPN이 필요한 서버는 `.ovpn` 파일을 함께 업로드합니다
3. 이관 실행 페이지에서 소스와 대상을 선택한 뒤 **이관 시작**을 클릭합니다

## 서비스 구성

| 서비스   | 설명 |
|----------|------|
| nginx    | 리버스 프록시 (포트 80) |
| backend  | FastAPI REST API + WebSocket |
| worker   | Celery 워커 (pg_dump / pg_restore, OpenVPN) |
| redis    | 태스크 큐 및 진행률 pub/sub |
| frontend | React SPA — nginx에서 정적 파일로 서빙 |

## 주요 환경변수

| 변수             | 설명 |
|------------------|------|
| `ENCRYPTION_KEY` | DB 비밀번호 및 `.ovpn` 파일 암호화에 사용되는 Fernet 키 |
| `JWT_SECRET`     | JWT 토큰 서명에 사용되는 비밀키 |
| `REDIS_URL`      | Redis 연결 URL |
| `DATABASE_URL`   | SQLite 데이터베이스 파일 경로 |

## 라이센스

MIT License로 배포됩니다 — [LICENSE.md](LICENSE.md) 참고.  
서드파티 컴포넌트의 라이센스는 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)를 참고하세요.

---

© 2026 FEENTS
