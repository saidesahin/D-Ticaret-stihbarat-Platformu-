"""
ORTAK ALTYAPI - deps.py
Modul 1, 2, 3... bir endpoint'i "sadece giris yapmis kullanici gorsun"
demek istediginde tek satirla bunu ekler:

    from app.core.deps import get_current_user

    @router.get("/ornek")
    def ornek(user = Depends(get_current_user)):
        ...

Boylece her modul kendi login kontrolunu yeniden yazmaz.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.m0_altyapi.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Gecersiz veya suresi dolmus oturum",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
