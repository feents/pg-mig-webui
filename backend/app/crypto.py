import os
from cryptography.fernet import Fernet

_key = os.getenv("ENCRYPTION_KEY", "")
if not _key:
    raise RuntimeError(
        "환경변수 ENCRYPTION_KEY가 설정되지 않았습니다. "
        "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" 로 생성 후 .env에 설정하세요."
    )

_fernet = Fernet(_key.encode())


def encrypt(text: str) -> str:
    return _fernet.encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet.decrypt(token.encode()).decode()
