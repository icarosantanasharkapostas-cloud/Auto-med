import json
from pydantic import BaseModel, field_validator
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

    # ===============================================================
    # ✅ CORREÇÃO DO ERRO "ResponseValidationError / Input should be a
    #    valid dictionary" no endpoint /api/clients.
    #
    # No banco antigo, o config_json às vezes vinha como TEXTO
    # (ex.: '{"prefix": "!"}') em vez de dicionário. O Pydantic
    # esperava um dict e quebrava com erro 500.
    #
    # Este validador aceita string (converte com json.loads), None
    # (vira {}) ou dict (mantém), nunca mais deixando o endpoint
    # quebrar. 🛡️
    # ===============================================================
    @field_validator("config_json", mode="before")
    @classmethod
    def _coerce_config_json(cls, v):
        if v is None or v == "":
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    class Config:
        from_attributes = True


class LoginSchema(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
