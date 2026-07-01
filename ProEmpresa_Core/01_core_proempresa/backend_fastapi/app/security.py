import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
from .db import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "PROEMPRESA_DEV_SECRET_CHANGE")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("plain:"):
        return plain_password == stored.replace("plain:", "", 1)
    return pwd_context.verify(plain_password, stored)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def rowdict(row):
    if row is None:
        return None
    return dict(row._mapping)

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        tipo = payload.get("tipo")
        if not sub:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if tipo == "cliente":
        row = db.execute(text("SELECT id, numero_documento AS username, 'cliente' AS rol, estado FROM clientes WHERE id = CAST(:id AS uuid)"), {"id": sub}).first()
    else:
        row = db.execute(text("SELECT id, username, rol, estado FROM usuarios WHERE id = CAST(:id AS uuid)"), {"id": sub}).first()
    user = rowdict(row)
    if not user or user.get("estado") != "activo":
        raise credentials_exception
    user["tipo"] = tipo or user.get("rol")
    return user

def audit(db: Session, user: dict, accion: str, entidad: str, entidad_id: str = None, detalle: str = ""):
    db.execute(text("""
        INSERT INTO auditoria (usuario_id, accion, entidad, entidad_id, detalle)
        VALUES (CAST(:usuario AS uuid), :accion, :entidad, CAST(:entidad_id AS uuid), :detalle)
    """), {"usuario": user.get("id"), "accion": accion, "entidad": entidad, "entidad_id": entidad_id, "detalle": detalle})
