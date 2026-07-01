from pydantic import BaseModel, Field
from typing import Optional

class LoginPersonalIn(BaseModel):
    username: Optional[str] = None
    codigo_empleado: Optional[str] = None
    password: str

class LoginClienteIn(BaseModel):
    numero_documento: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ClienteSolicitudIn(BaseModel):
    monto_solicitado: float = Field(gt=0)
    plazo_meses: int = Field(gt=0)
    destino_credito: Optional[str] = None
    cuota_estimada: Optional[float] = None
    tea_referencial: Optional[float] = None

class SolicitudIn(ClienteSolicitudIn):
    cliente_id: Optional[str] = None
    numero_documento: Optional[str] = None
    nombres: str = ""
    apellidos: str = ""
    telefono: Optional[str] = None
    canal: str = "asesor"
    lat_captura: Optional[float] = None
    lng_captura: Optional[float] = None

class EstadoSolicitudIn(BaseModel):
    estado: str
    monto_aprobado: Optional[float] = None
    comentario: str = ""
    motivo_rechazo: Optional[str] = None

class OperacionIn(BaseModel):
    cuenta_origen_id: str
    cuenta_destino_id: Optional[str] = None
    tipo_operacion: str
    monto: float = Field(gt=0)
    moneda: str = "PEN"
    descripcion: Optional[str] = None

class VisitaIn(BaseModel):
    resultado: str
    observacion: str = ""
    tipo_visita: Optional[str] = "campo"
    lat: Optional[float] = None
    lng: Optional[float] = None
    precision_gps: Optional[float] = None

class ClienteUbicacionIn(BaseModel):
    direccion: Optional[str] = None
    referencia_direccion: Optional[str] = None
    latitud_domicilio: Optional[float] = None
    longitud_domicilio: Optional[float] = None
    nombre_negocio: Optional[str] = None
    direccion_negocio: Optional[str] = None
    referencia_negocio: Optional[str] = None
    lat_negocio: Optional[float] = None
    lng_negocio: Optional[float] = None
    ubicacion_verificada: Optional[bool] = None
