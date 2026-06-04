"""认证相关的 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, field_validator
import re


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    mimo_api_key: str = Field(..., min_length=1)
    deepseek_api_key: str = Field(..., min_length=1)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[一-龥a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含中文、字母、数字和下划线")
        return v.strip()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    token: str
    user_id: int
    username: str
    has_api_keys: bool


class ApiKeyUpdate(BaseModel):
    mimo_api_key: str = Field(default="")
    deepseek_api_key: str = Field(default="")
