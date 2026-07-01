import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..schemas import LoginClienteIn, ClienteSolicitudIn, OperacionIn
from ..security import verify_password, create_access_token, current_user, rowdict, audit

router = APIRouter(prefix="/cliente", tags=["App cliente"] )

def cliente_actual(db: Session, user: dict):
    if user.get("tipo") != "cliente":
        raise HTTPException(status_code=403, detail="Acceso solo cliente")
    row = db.execute(text("SELECT * FROM clientes WHERE id=CAST(:id AS uuid)"), {"id": user["id"]}).first()
    cliente = rowdict(row)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

def asesor_default(db: Session):
    row = db.execute(text("SELECT id FROM asesores WHERE codigo_empleado='0001' LIMIT 1")).first()
    if not row:
        raise HTTPException(status_code=500, detail="No existe asesor por defecto 0001")
    return str(row._mapping["id"])

def crear_cartera_para_solicitud(db, asesor_id, cliente_id, solicitud_id, monto):
    cartera_id = str(uuid.uuid4())
    prioridad = 'alta' if float(monto) >= 8000 else 'media'
    db.execute(text("""
        INSERT INTO cartera_comercial (id, asesor_id, cliente_id, solicitud_id, fecha_asignacion, tipo_gestion, prioridad, score_prioridad, monto_referencial, estado_visita, orden_manual)
        VALUES (CAST(:id AS uuid), CAST(:asesor AS uuid), CAST(:cliente AS uuid), CAST(:sol AS uuid), (now() AT TIME ZONE 'America/Lima')::date, 'SOLICITUD_CREDITO', :prioridad, :score, :monto, 'pendiente', 1)
    """), {"id": cartera_id, "asesor": asesor_id, "cliente": cliente_id, "sol": solicitud_id, "prioridad": prioridad, "score": 85 if prioridad=='alta' else 65, "monto": monto})
    return cartera_id

@router.post("/login")
def login_cliente(data: LoginClienteIn, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM clientes WHERE numero_documento=:dni AND estado='activo'"), {"dni": data.numero_documento.strip()}).first()
    c = rowdict(row)
    if not c or not verify_password(data.password, c["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    token = create_access_token({"sub": str(c["id"]), "tipo": "cliente"})
    return {"access_token": token, "user": {"id": str(c["id"]), "numero_documento": c["numero_documento"], "nombre": f"{c['nombres']} {c['apellidos']}", "rol": "cliente"}, "cliente": c}

@router.get("/perfil")
def perfil(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    return cliente_actual(db, user)

@router.get("/cuentas")
def cuentas(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = cliente_actual(db, user)
    return [dict(r._mapping) for r in db.execute(text("SELECT * FROM cuentas WHERE cliente_id=CAST(:id AS uuid) ORDER BY created_at"), {"id": c["id"]}).all()]

@router.get("/creditos")
def creditos(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = cliente_actual(db, user)
    return [dict(r._mapping) for r in db.execute(text("SELECT * FROM creditos WHERE cliente_id=CAST(:id AS uuid) ORDER BY created_at DESC"), {"id": c["id"]}).all()]

@router.get("/movimientos")
def movimientos(limit: int = 20, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = cliente_actual(db, user)
    return [dict(r._mapping) for r in db.execute(text("""
        SELECT * FROM movimientos_cuenta WHERE cliente_id=CAST(:id AS uuid) ORDER BY created_at DESC LIMIT :limit
    """), {"id": c["id"], "limit": limit}).all()]

@router.get("/solicitudes")
def mis_solicitudes(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = cliente_actual(db, user)
    return [dict(r._mapping) for r in db.execute(text("SELECT * FROM solicitudes_credito WHERE cliente_id=CAST(:id AS uuid) ORDER BY created_at DESC"), {"id": c["id"]}).all()]

@router.post("/solicitudes")
def crear_solicitud(data: ClienteSolicitudIn, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = cliente_actual(db, user)
    sol_id = str(uuid.uuid4())
    expediente = 'PE-' + sol_id.replace('-', '')[:10].upper()
    cuota = data.cuota_estimada or round((data.monto_solicitado * 1.18) / data.plazo_meses, 2)
    tea = data.tea_referencial or 38.50
    asesor_id = asesor_default(db)
    db.execute(text("""
        INSERT INTO solicitudes_credito (id, cliente_id, asesor_id, numero_expediente, monto_solicitado, plazo_meses, destino_credito, cuota_estimada, tea_referencial, estado, canal)
        VALUES (CAST(:id AS uuid), CAST(:cliente AS uuid), CAST(:asesor AS uuid), :exp, :monto, :plazo, :destino, :cuota, :tea, 'pendiente_visita', 'app_cliente')
    """), {"id": sol_id, "cliente": c["id"], "asesor": asesor_id, "exp": expediente, "monto": data.monto_solicitado, "plazo": data.plazo_meses, "destino": data.destino_credito, "cuota": cuota, "tea": tea})
    cartera_id = crear_cartera_para_solicitud(db, asesor_id, str(c["id"]), sol_id, data.monto_solicitado)
    db.execute(text("INSERT INTO notificaciones (cliente_id, titulo, mensaje, tipo, canal) VALUES (CAST(:cliente AS uuid), 'Solicitud registrada', :msg, 'solicitud', 'APP_CLIENTE')"), {"cliente": c["id"], "msg": f"Tu solicitud {expediente} fue registrada y asignada a un asesor."})
    audit(db, user, 'CREAR_SOLICITUD_CLIENTE', 'solicitudes_credito', sol_id, expediente)
    db.commit()
    return {"id": sol_id, "numero_expediente": expediente, "estado": "pendiente_visita", "cartera_id": cartera_id, "monto_solicitado": data.monto_solicitado, "plazo_meses": data.plazo_meses, "cuota_estimada": cuota}

@router.post("/operaciones")
def crear_operacion(data: OperacionIn, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = cliente_actual(db, user)
    row = db.execute(text("SELECT * FROM cuentas WHERE id=CAST(:id AS uuid) AND cliente_id=CAST(:cliente AS uuid) FOR UPDATE"), {"id": data.cuenta_origen_id, "cliente": c["id"]}).first()
    cuenta = rowdict(row)
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    saldo = float(cuenta["saldo_disponible"] or 0)
    if saldo < data.monto:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    nuevo = round(saldo - data.monto, 2)
    op_id = str(uuid.uuid4()); codigo = 'OP-' + op_id.replace('-', '')[:10].upper()
    desc = data.descripcion or data.tipo_operacion
    db.execute(text("UPDATE cuentas SET saldo_disponible=:s, saldo_contable=:s, updated_at=now() WHERE id=CAST(:id AS uuid)"), {"s": nuevo, "id": cuenta["id"]})
    db.execute(text("INSERT INTO operaciones (id, cliente_id, cuenta_origen_id, tipo_operacion, monto, moneda, estado, canal, codigo_operacion, descripcion) VALUES (CAST(:id AS uuid), CAST(:cliente AS uuid), CAST(:cuenta AS uuid), :tipo, :monto, :moneda, 'procesada', 'APP_CLIENTE', :codigo, :desc)"), {"id": op_id, "cliente": c["id"], "cuenta": cuenta["id"], "tipo": data.tipo_operacion.upper(), "monto": data.monto, "moneda": data.moneda, "codigo": codigo, "desc": desc})
    db.execute(text("INSERT INTO movimientos_cuenta (cuenta_id, cliente_id, tipo_movimiento, concepto, canal, monto, moneda, saldo_resultante) VALUES (CAST(:cuenta AS uuid), CAST(:cliente AS uuid), :tipo, :concepto, 'APP_CLIENTE', :monto, :moneda, :saldo)"), {"cuenta": cuenta["id"], "cliente": c["id"], "tipo": data.tipo_operacion.upper(), "concepto": desc, "monto": -data.monto, "moneda": data.moneda, "saldo": nuevo})
    db.commit()
    return {"id": op_id, "codigo_operacion": codigo, "estado": "procesada", "monto": data.monto, "saldo_resultante": nuevo, "descripcion": desc}

@router.get("/notificaciones")
def notificaciones(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = cliente_actual(db, user)
    return [dict(r._mapping) for r in db.execute(text("SELECT * FROM notificaciones WHERE cliente_id=CAST(:id AS uuid) ORDER BY created_at DESC LIMIT 20"), {"id": c["id"]}).all()]
