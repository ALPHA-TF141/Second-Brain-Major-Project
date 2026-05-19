from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    device_name: str = "desktop"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class LogoutResponse(BaseModel):
    message: str
