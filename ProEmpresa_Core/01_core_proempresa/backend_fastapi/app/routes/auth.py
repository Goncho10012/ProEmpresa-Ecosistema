from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import timedelta
from ..db import get_db
from ..schemas import LoginPersonalIn, TokenOut
from ..security import verify_password, create_access_token, current_user, rowdict

router = APIRouter(prefix="/auth", tags=["Auth personal"] )

@router.post("/login", response_model=TokenOut)
def login(data: LoginPersonalIn, db: Session = Depends(get_db)):
    usuario = (data.username or data.codigo_empleado or "").strip()
    if not usuario:
        raise HTTPException(status_code=422, detail="Ingrese usuario o codigo")
    row = db.execute(text("""
        SELECT u.*, a.codigo_empleado, a.nombres AS asesor_nombres
        FROM usuarios u
        LEFT JOIN asesores a ON a.usuario_id = u.id
        WHERE (u.username = :u OR a.codigo_empleado = :u) AND u.estado='activo'
        LIMIT 1
    """), {"u": usuario}).first()
    user = rowdict(row)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    token = create_access_token({"sub": str(user["id"]), "tipo": "personal", "rol": user["rol"]})
    return {"access_token": token, "user": {"id": str(user["id"]), "username": user["username"], "rol": user["rol"], "nombre": user["nombre"], "codigo_empleado": user.get("codigo_empleado")}}

@router.get("/me")
def me(user: dict = Depends(current_user)):
    return user

@router.post("/logout")
def logout():
    return {"ok": True}
