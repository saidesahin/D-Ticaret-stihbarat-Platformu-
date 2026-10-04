from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    password: str
    company_name: str | None = None
    is_admin: bool = False


class UserOut(BaseModel):
    id: int
    username: str
    company_name: str | None
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True
