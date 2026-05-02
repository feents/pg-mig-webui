# Third-Party Licenses

이 프로젝트는 아래 오픈소스 및 source-available 소프트웨어를 사용합니다.

---

## Frontend (Runtime)

| 패키지 | 버전 | 라이센스 | 홈페이지 |
|---|---|---|---|
| react | 19.2.5 | MIT | https://react.dev |
| react-dom | 19.2.5 | MIT | https://react.dev |
| react-router-dom | 7.14.2 | MIT | https://github.com/remix-run/react-router |
| axios | 1.15.2 | MIT | https://axios-http.com |
| lucide-react | 1.14.0 | ISC | https://lucide.dev |
| clsx | 2.1.1 | MIT | https://github.com/lukeed/clsx |
| tailwind-merge | 3.5.0 | MIT | https://github.com/dcastil/tailwind-merge |
| @radix-ui/react-checkbox | 1.3.3 | MIT | https://radix-ui.com/primitives |
| @radix-ui/react-dialog | 1.1.15 | MIT | https://radix-ui.com/primitives |
| @radix-ui/react-label | 2.1.8 | MIT | https://radix-ui.com/primitives |
| @radix-ui/react-select | 2.2.6 | MIT | https://radix-ui.com/primitives |
| i18next | 26.0.8 | MIT | https://www.i18next.com |
| i18next-browser-languagedetector | 8.2.1 | MIT | https://github.com/i18next/i18next-browser-languageDetector |
| react-i18next | 17.0.6 | MIT | https://react.i18next.com |

---

## Backend (Runtime)

| 패키지 | 버전 | 라이센스 | 홈페이지 |
|---|---|---|---|
| fastapi | 0.115.5 | MIT | https://fastapi.tiangolo.com |
| uvicorn | 0.32.1 | BSD-3-Clause | https://www.uvicorn.org |
| SQLAlchemy | 2.0.36 | MIT | https://www.sqlalchemy.org |
| aiosqlite | 0.20.0 | MIT | https://github.com/omnilib/aiosqlite |
| python-jose | 3.3.0 | MIT | https://github.com/mpdavis/python-jose |
| bcrypt | 4.2.1 | Apache-2.0 | https://github.com/pyca/bcrypt |
| python-multipart | 0.0.12 | Apache-2.0 | https://github.com/Kludex/python-multipart |
| cryptography | 43.0.3 | Apache-2.0 OR BSD-3-Clause | https://cryptography.io |
| celery | 5.4.0 | BSD-3-Clause | https://docs.celeryq.dev |
| redis (py) | 5.2.0 | MIT | https://github.com/redis/redis-py |
| websockets | 13.1 | BSD-3-Clause | https://websockets.readthedocs.io |
| httpx | 0.27.2 | BSD-3-Clause | https://www.python-httpx.org |
| pydantic | 2.10.1 | MIT | https://docs.pydantic.dev |
| pydantic-settings | 2.6.1 | MIT | https://docs.pydantic.dev/latest/concepts/pydantic_settings |
| psycopg2-binary | 2.9.10 | LGPL with exceptions | https://www.psycopg.org |

> **psycopg2-binary** 는 LGPL with exceptions 라이센스입니다. binary wheel은 libpq를 정적으로 번들하며, 이 프로젝트는 라이브러리를 수정하지 않습니다.

---

## Infrastructure (Docker base images)

| 이미지 | 라이센스 | 비고 |
|---|---|---|
| redis:7-alpine (7.4.x) | RSALv2 OR SSPLv1 (Redis), MIT (Alpine Linux) | https://redis.io |
| nginx:alpine | 2-clause BSD (Nginx), MIT (Alpine Linux) | https://nginx.org |

> **redis:7-alpine** 의 Redis 서버는 RSALv2/SSPLv1 라이센스입니다. 이 서비스를 외부에 SaaS 형태로 제공하는 경우 해당 라이센스 조건을 검토해야 합니다.

---

## Fonts (CDN)

| 폰트 | 버전 | 라이센스 | 홈페이지 |
|---|---|---|---|
| Pretendard Variable | 1.3.9 | SIL Open Font License 1.1 | https://github.com/orioncactus/pretendard |
| JetBrains Mono | latest (Google Fonts) | SIL Open Font License 1.1 | https://www.jetbrains.com/legalforms/mono |

---

## 라이센스 전문

라이센스 전문은 각 패키지의 공식 저장소에서 확인할 수 있습니다.

LGPL: https://www.gnu.org/licenses/lgpl.html  
RSALv2: https://redis.com/legal/rsalv2-agreement  
SSPLv1: https://www.mongodb.com/licensing/server-side-public-license  
SIL OFL 1.1: https://scripts.sil.org/OFL
