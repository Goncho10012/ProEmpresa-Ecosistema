import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..schemas import SolicitudIn, EstadoSolicitudIn, VisitaIn, ClienteUbicacionIn
from ..security import current_user, rowdict, audit

router = APIRouter(tags=["Operaciones internas"] )

def asesor_id(db, user):
    row = db.execute(text("SELECT id FROM asesores WHERE usuario_id=CAST(:id AS uuid) LIMIT 1"), {"id": user["id"]}).first()
    return str(row._mapping["id"]) if row else None

@router.get("/clientes")
def clientes(q: str | None = None, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    sql = "SELECT c.*, n.nombre_negocio, n.direccion_negocio, n.lat_negocio, n.lng_negocio FROM clientes c LEFT JOIN cliente_negocios n ON n.cliente_id=c.id WHERE 1=1"
    params = {}
    if q:
        sql += " AND (c.numero_documento ILIKE :q OR c.nombres ILIKE :q OR c.apellidos ILIKE :q)"; params["q"] = f"%{q}%"
    sql += " ORDER BY c.created_at DESC LIMIT 100"
    return [dict(r._mapping) for r in db.execute(text(sql), params).all()]

@router.get("/clientes/{cliente_id}/ficha")
def ficha(cliente_id: str, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    c = rowdict(db.execute(text("SELECT * FROM clientes WHERE id=CAST(:id AS uuid)"), {"id": cliente_id}).first())
    if not c: raise HTTPException(404, "Cliente no encontrado")
    negocio = rowdict(db.execute(text("SELECT * FROM cliente_negocios WHERE cliente_id=CAST(:id AS uuid) LIMIT 1"), {"id": cliente_id}).first())
    cuentas = [dict(r._mapping) for r in db.execute(text("SELECT * FROM cuentas WHERE cliente_id=CAST(:id AS uuid)"), {"id": cliente_id}).all()]
    solicitudes = [dict(r._mapping) for r in db.execute(text("SELECT * FROM solicitudes_credito WHERE cliente_id=CAST(:id AS uuid) ORDER BY created_at DESC"), {"id": cliente_id}).all()]
    return {"cliente": c, "negocio": negocio, "cuentas": cuentas, "solicitudes": solicitudes}

@router.patch("/clientes/{cliente_id}/ubicacion")
def actualizar_ubicacion(cliente_id: str, data: ClienteUbicacionIn, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(text("UPDATE clientes SET direccion=COALESCE(:direccion,direccion), latitud_domicilio=COALESCE(:lat,latitud_domicilio), longitud_domicilio=COALESCE(:lng,longitud_domicilio), updated_at=now() WHERE id=CAST(:id AS uuid)"), {"id": cliente_id, "direccion": data.direccion, "lat": data.latitud_domicilio, "lng": data.longitud_domicilio})
    db.execute(text("""
        INSERT INTO cliente_negocios (cliente_id, nombre_negocio, direccion_negocio, referencia_negocio, lat_negocio, lng_negocio, ubicacion_verificada, fuente_ubicacion)
        VALUES (CAST(:cliente AS uuid), :nombre, :direccion, :ref, :lat, :lng, COALESCE(:verif,true), 'asesor')
        ON CONFLICT (cliente_id) DO UPDATE SET nombre_negocio=COALESCE(EXCLUDED.nombre_negocio, cliente_negocios.nombre_negocio), direccion_negocio=COALESCE(EXCLUDED.direccion_negocio, cliente_negocios.direccion_negocio), referencia_negocio=COALESCE(EXCLUDED.referencia_negocio, cliente_negocios.referencia_negocio), lat_negocio=COALESCE(EXCLUDED.lat_negocio, cliente_negocios.lat_negocio), lng_negocio=COALESCE(EXCLUDED.lng_negocio, cliente_negocios.lng_negocio), ubicacion_verificada=COALESCE(EXCLUDED.ubicacion_verificada, cliente_negocios.ubicacion_verificada), updated_at=now()
    """), {"cliente": cliente_id, "nombre": data.nombre_negocio, "direccion": data.direccion_negocio, "ref": data.referencia_negocio, "lat": data.lat_negocio, "lng": data.lng_negocio, "verif": data.ubicacion_verificada})
    audit(db, user, 'ACTUALIZAR_UBICACION', 'clientes', cliente_id, 'Ubicacion actualizada')
    db.commit()
    return {"ok": True}

@router.get("/cartera")
def listar_cartera(fecha: str | None = None, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    aid = asesor_id(db, user)
    params = {"asesor": aid} if aid else {}
    where = "WHERE 1=1"
    if aid and user.get('rol') == 'asesor':
        where += " AND car.asesor_id=CAST(:asesor AS uuid)"
    if fecha:
        where += " AND car.fecha_asignacion=:fecha"; params['fecha'] = fecha
    sql = f"""
        SELECT car.*, c.numero_documento, c.nombres, c.apellidos, c.telefono, n.nombre_negocio, n.direccion_negocio, n.lat_negocio, n.lng_negocio, s.numero_expediente, s.estado AS estado_solicitud, s.monto_solicitado, s.plazo_meses
        FROM cartera_comercial car
        JOIN clientes c ON c.id=car.cliente_id
        LEFT JOIN cliente_negocios n ON n.cliente_id=c.id
        LEFT JOIN solicitudes_credito s ON s.id=car.solicitud_id
        {where}
        ORDER BY car.fecha_asignacion DESC, car.prioridad, car.created_at DESC
    """
    return [dict(r._mapping) for r in db.execute(text(sql), params).all()]

@router.post("/cartera/{cartera_id}/visita")
def registrar_visita(cartera_id: str, data: VisitaIn, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM cartera_comercial WHERE id=CAST(:id AS uuid)"), {"id": cartera_id}).first()
    car = rowdict(row)
    if not car: raise HTTPException(404, "Cartera no encontrada")
    visita_id=str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO visitas (id, cartera_id, asesor_id, cliente_id, solicitud_id, resultado, observacion, tipo_visita, lat, lng, precision_gps)
        VALUES (CAST(:id AS uuid), CAST(:car AS uuid), CAST(:asesor AS uuid), CAST(:cliente AS uuid), CAST(:sol AS uuid), :resultado, :obs, :tipo, :lat, :lng, :precision)
    """), {"id": visita_id, "car": cartera_id, "asesor": car["asesor_id"], "cliente": car["cliente_id"], "sol": car.get("solicitud_id"), "resultado": data.resultado, "obs": data.observacion, "tipo": data.tipo_visita, "lat": data.lat, "lng": data.lng, "precision": data.precision_gps})
    db.execute(text("UPDATE cartera_comercial SET estado_visita='visitado', resultado_visita=:res, observacion_visita=:obs, lat_visita=:lat, lng_visita=:lng, precision_gps=:precision, timestamp_visita=now(), updated_at=now() WHERE id=CAST(:id AS uuid)"), {"id": cartera_id, "res": data.resultado, "obs": data.observacion, "lat": data.lat, "lng": data.lng, "precision": data.precision_gps})
    if car.get("solicitud_id"):
        db.execute(text("UPDATE solicitudes_credito SET estado='visitada', updated_at=now() WHERE id=CAST(:id AS uuid) AND estado IN ('pendiente_visita','en_visita')"), {"id": car["solicitud_id"]})
    audit(db, user, 'REGISTRAR_VISITA', 'cartera_comercial', cartera_id, data.resultado)
    db.commit()
    return {"id": visita_id, "estado": "registrada"}

@router.get("/solicitudes")
def solicitudes(estado: str | None = None, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    params={} ; where='WHERE 1=1'
    if estado:
        where += ' AND s.estado=:estado'; params['estado']=estado
    sql=f"""SELECT s.*, c.numero_documento, c.nombres, c.apellidos, a.codigo_empleado FROM solicitudes_credito s JOIN clientes c ON c.id=s.cliente_id LEFT JOIN asesores a ON a.id=s.asesor_id {where} ORDER BY s.created_at DESC"""
    return [dict(r._mapping) for r in db.execute(text(sql), params).all()]

@router.post("/solicitudes")
def crear_solicitud(data: SolicitudIn, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    cliente_id = data.cliente_id
    if not cliente_id and data.numero_documento:
        row = db.execute(text("SELECT id FROM clientes WHERE numero_documento=:dni"), {"dni": data.numero_documento}).first()
        if row: cliente_id = str(row._mapping['id'])
    if not cliente_id: raise HTTPException(404, "Cliente requerido")
    sol_id=str(uuid.uuid4()); exp='PE-'+sol_id.replace('-','')[:10].upper(); aid=asesor_id(db,user)
    cuota=data.cuota_estimada or round((data.monto_solicitado*1.18)/data.plazo_meses,2)
    db.execute(text("INSERT INTO solicitudes_credito (id, cliente_id, asesor_id, numero_expediente, monto_solicitado, plazo_meses, destino_credito, cuota_estimada, tea_referencial, estado, canal) VALUES (CAST(:id AS uuid), CAST(:cliente AS uuid), CAST(:asesor AS uuid), :exp, :monto, :plazo, :destino, :cuota, COALESCE(:tea,38.50), 'pendiente_visita', :canal)"), {"id": sol_id, "cliente": cliente_id, "asesor": aid, "exp": exp, "monto": data.monto_solicitado, "plazo": data.plazo_meses, "destino": data.destino_credito, "cuota": cuota, "tea": data.tea_referencial, "canal": data.canal})
    if aid:
        db.execute(text("INSERT INTO cartera_comercial (asesor_id, cliente_id, solicitud_id, fecha_asignacion, tipo_gestion, prioridad, score_prioridad, monto_referencial, estado_visita) VALUES (CAST(:asesor AS uuid), CAST(:cliente AS uuid), CAST(:sol AS uuid), (now() AT TIME ZONE 'America/Lima')::date, 'SOLICITUD_CREDITO', 'alta', 80, :monto, 'pendiente')"), {"asesor": aid, "cliente": cliente_id, "sol": sol_id, "monto": data.monto_solicitado})
    db.commit(); return {"id": sol_id, "numero_expediente": exp, "estado": "pendiente_visita"}

@router.patch("/solicitudes/{solicitud_id}/estado")
def cambiar_estado(solicitud_id: str, data: EstadoSolicitudIn, user: dict = Depends(current_user), db: Session = Depends(get_db)):
    sol = rowdict(db.execute(text("SELECT * FROM solicitudes_credito WHERE id=CAST(:id AS uuid) FOR UPDATE"), {"id": solicitud_id}).first())
    if not sol: raise HTTPException(404, "Solicitud no encontrada")
    estado = data.estado.lower()
    if estado in ['aprobar','aprobada','desembolsar','desembolsada']:
        monto = data.monto_aprobado or sol['monto_solicitado']
        cuenta = rowdict(db.execute(text("SELECT * FROM cuentas WHERE cliente_id=CAST(:cliente AS uuid) ORDER BY created_at LIMIT 1 FOR UPDATE"), {"cliente": sol['cliente_id']}).first())
        if not cuenta: raise HTTPException(400, "Cliente sin cuenta para desembolso")
        cred_id=str(uuid.uuid4()); num='CR-'+cred_id.replace('-','')[:10].upper(); nuevo_saldo=float(cuenta['saldo_disponible'] or 0)+float(monto)
        db.execute(text("UPDATE solicitudes_credito SET estado='desembolsada', monto_aprobado=:monto, comentario=:comentario, updated_at=now() WHERE id=CAST(:id AS uuid)"), {"id": solicitud_id, "monto": monto, "comentario": data.comentario})
        db.execute(text("INSERT INTO creditos (id, cliente_id, solicitud_id, numero_credito, producto, monto_desembolsado, saldo_total, plazo_meses, tea, estado, fecha_desembolso) VALUES (CAST(:id AS uuid), CAST(:cliente AS uuid), CAST(:sol AS uuid), :num, 'Credito Capital de Trabajo', :monto, :monto, :plazo, COALESCE(:tea,38.50), 'vigente', now())"), {"id": cred_id, "cliente": sol['cliente_id'], "sol": solicitud_id, "num": num, "monto": monto, "plazo": sol['plazo_meses'], "tea": sol.get('tea_referencial')})
        db.execute(text("UPDATE cuentas SET saldo_disponible=:saldo, saldo_contable=:saldo, updated_at=now() WHERE id=CAST(:id AS uuid)"), {"saldo": nuevo_saldo, "id": cuenta['id']})
        db.execute(text("INSERT INTO movimientos_cuenta (cuenta_id, cliente_id, tipo_movimiento, concepto, canal, monto, moneda, saldo_resultante) VALUES (CAST(:cuenta AS uuid), CAST(:cliente AS uuid), 'DESEMBOLSO_CREDITO', :concepto, 'CORE', :monto, 'PEN', :saldo)"), {"cuenta": cuenta['id'], "cliente": sol['cliente_id'], "concepto": f"Desembolso {num}", "monto": monto, "saldo": nuevo_saldo})
        db.execute(text("INSERT INTO operaciones (cliente_id, cuenta_origen_id, tipo_operacion, monto, moneda, estado, canal, codigo_operacion, descripcion) VALUES (CAST(:cliente AS uuid), CAST(:cuenta AS uuid), 'DESEMBOLSO_CREDITO', :monto, 'PEN', 'procesada', 'CORE', :codigo, :desc)"), {"cliente": sol['cliente_id'], "cuenta": cuenta['id'], "monto": monto, "codigo": 'OP-'+cred_id.replace('-','')[:10].upper(), "desc": f"Desembolso de credito {num}"})
        db.execute(text("INSERT INTO notificaciones (cliente_id, titulo, mensaje, tipo, canal) VALUES (CAST(:cliente AS uuid), 'Credito desembolsado', :msg, 'credito', 'CORE')"), {"cliente": sol['cliente_id'], "msg": f"Tu credito {num} fue desembolsado por S/ {float(monto):.2f}."})
        audit(db, user, 'DESEMBOLSAR_CREDITO', 'solicitudes_credito', solicitud_id, num)
        db.commit(); return {"estado": "desembolsada", "numero_credito": num, "monto_desembolsado": monto, "saldo_resultante": nuevo_saldo}
    if estado in ['rechazar','rechazada']:
        db.execute(text("UPDATE solicitudes_credito SET estado='rechazada', motivo_rechazo=:motivo, comentario=:comentario, updated_at=now() WHERE id=CAST(:id AS uuid)"), {"id": solicitud_id, "motivo": data.motivo_rechazo, "comentario": data.comentario})
    else:
        db.execute(text("UPDATE solicitudes_credito SET estado=:estado, comentario=:comentario, updated_at=now() WHERE id=CAST(:id AS uuid)"), {"id": solicitud_id, "estado": estado, "comentario": data.comentario})
    audit(db, user, 'CAMBIAR_ESTADO_SOLICITUD', 'solicitudes_credito', solicitud_id, estado)
    db.commit(); return {"estado": estado}

@router.get("/operaciones")
def operaciones(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    return [dict(r._mapping) for r in db.execute(text("""SELECT o.*, c.nombres || ' ' || c.apellidos AS cliente_nombre FROM operaciones o LEFT JOIN clientes c ON c.id=o.cliente_id ORDER BY o.created_at DESC LIMIT 100""")).all()]

@router.get("/reportes/dashboard")
def dashboard(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    return {
        "clientes": db.execute(text("SELECT count(*) FROM clientes")).scalar(),
        "solicitudes": db.execute(text("SELECT count(*) FROM solicitudes_credito")).scalar(),
        "cartera_pendiente": db.execute(text("SELECT count(*) FROM cartera_comercial WHERE estado_visita='pendiente'")).scalar(),
        "operaciones": db.execute(text("SELECT count(*) FROM operaciones")).scalar(),
        "monto_solicitado": float(db.execute(text("SELECT COALESCE(sum(monto_solicitado),0) FROM solicitudes_credito")).scalar() or 0)
    }

@router.get("/auditoria")
def auditoria(user: dict = Depends(current_user), db: Session = Depends(get_db)):
    return [dict(r._mapping) for r in db.execute(text("SELECT * FROM auditoria ORDER BY created_at DESC LIMIT 100")).all()]
