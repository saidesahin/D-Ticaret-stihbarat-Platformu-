from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.modules.m0_altyapi.models import User
from app.modules.m0_altyapi.schemas import UserCreate


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        company_name=data.company_name,
        is_admin=data.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
