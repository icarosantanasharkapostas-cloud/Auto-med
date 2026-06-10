from pydantic import BaseModel
from typing import Optional, Dict

class ClientBase(BaseModel):
    nome: str
    token: str
    email: Optional[str] = ""
    senha_email: Optional[str] = ""
    ativo: Optional[bool] = False
    config_json: Optional[Dict] = {}

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    nome: Optional[str] = None
    token: Optional[str] = None
    email: Optional[str] = None
    senha_email: Optional[str] = None
    ativo: Optional[bool] = None
    config_json: Optional[Dict] = None

class ClientOut(ClientBase):
    id: int

    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    username: str
    password: str

class TokenSchema(BaseModel):
    access_token: str
    token_type: str
