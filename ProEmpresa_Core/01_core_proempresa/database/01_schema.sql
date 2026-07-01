-- Core ProEmpresa - Esquema principal
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS usuarios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username text UNIQUE NOT NULL,
    password_hash text NOT NULL,
    nombre text NOT NULL,
    rol text NOT NULL CHECK (rol IN ('admin','supervisor','asesor')),
    estado text NOT NULL DEFAULT 'activo',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agencias (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo text UNIQUE NOT NULL,
    nombre text NOT NULL,
    ciudad text NOT NULL,
    direccion text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS asesores (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid REFERENCES usuarios(id),
    agencia_id uuid REFERENCES agencias(id),
    codigo_empleado text UNIQUE NOT NULL,
    nombres text NOT NULL,
    telefono text,
    estado text NOT NULL DEFAULT 'activo',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clientes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_documento text UNIQUE NOT NULL,
    password_hash text NOT NULL,
    nombres text NOT NULL,
    apellidos text NOT NULL,
    telefono text,
    email text,
    direccion text,
    referencia_direccion text,
    latitud_domicilio numeric(10,7),
    longitud_domicilio numeric(10,7),
    estado text NOT NULL DEFAULT 'activo',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cliente_negocios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id uuid UNIQUE REFERENCES clientes(id),
    nombre_negocio text,
    giro_negocio text,
    direccion_negocio text,
    referencia_negocio text,
    lat_negocio numeric(10,7),
    lng_negocio numeric(10,7),
    ubicacion_verificada boolean DEFAULT false,
    fuente_ubicacion text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cuentas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id uuid REFERENCES clientes(id),
    numero_cuenta text UNIQUE NOT NULL,
    tipo_cuenta text NOT NULL,
    moneda text NOT NULL DEFAULT 'PEN',
    saldo_disponible numeric(14,2) NOT NULL DEFAULT 0,
    saldo_contable numeric(14,2) NOT NULL DEFAULT 0,
    estado text NOT NULL DEFAULT 'activa',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS solicitudes_credito (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id uuid REFERENCES clientes(id),
    asesor_id uuid REFERENCES asesores(id),
    numero_expediente text UNIQUE NOT NULL,
    monto_solicitado numeric(14,2) NOT NULL,
    monto_aprobado numeric(14,2),
    plazo_meses integer NOT NULL,
    destino_credito text,
    cuota_estimada numeric(14,2),
    tea_referencial numeric(8,2),
    estado text NOT NULL DEFAULT 'pendiente_visita',
    canal text NOT NULL DEFAULT 'app_cliente',
    comentario text,
    motivo_rechazo text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS creditos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id uuid REFERENCES clientes(id),
    solicitud_id uuid REFERENCES solicitudes_credito(id),
    numero_credito text UNIQUE NOT NULL,
    producto text NOT NULL,
    monto_desembolsado numeric(14,2) NOT NULL,
    saldo_total numeric(14,2) NOT NULL,
    plazo_meses integer NOT NULL,
    tea numeric(8,2) NOT NULL,
    estado text NOT NULL DEFAULT 'vigente',
    fecha_desembolso timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cartera_comercial (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    asesor_id uuid REFERENCES asesores(id),
    cliente_id uuid REFERENCES clientes(id),
    solicitud_id uuid REFERENCES solicitudes_credito(id),
    fecha_asignacion date NOT NULL DEFAULT (now() AT TIME ZONE 'America/Lima')::date,
    tipo_gestion text NOT NULL DEFAULT 'SOLICITUD_CREDITO',
    prioridad text NOT NULL DEFAULT 'media',
    score_prioridad integer DEFAULT 50,
    monto_referencial numeric(14,2),
    estado_visita text NOT NULL DEFAULT 'pendiente',
    resultado_visita text,
    observacion_visita text,
    lat_visita numeric(10,7),
    lng_visita numeric(10,7),
    precision_gps numeric(10,2),
    timestamp_visita timestamptz,
    orden_manual integer DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS visitas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cartera_id uuid REFERENCES cartera_comercial(id),
    asesor_id uuid REFERENCES asesores(id),
    cliente_id uuid REFERENCES clientes(id),
    solicitud_id uuid REFERENCES solicitudes_credito(id),
    resultado text NOT NULL,
    observacion text,
    tipo_visita text DEFAULT 'campo',
    lat numeric(10,7),
    lng numeric(10,7),
    precision_gps numeric(10,2),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS movimientos_cuenta (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cuenta_id uuid REFERENCES cuentas(id),
    cliente_id uuid REFERENCES clientes(id),
    tipo_movimiento text NOT NULL,
    concepto text NOT NULL,
    canal text NOT NULL,
    monto numeric(14,2) NOT NULL,
    moneda text NOT NULL DEFAULT 'PEN',
    saldo_resultante numeric(14,2),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS operaciones (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id uuid REFERENCES clientes(id),
    cuenta_origen_id uuid REFERENCES cuentas(id),
    cuenta_destino_id uuid REFERENCES cuentas(id),
    tipo_operacion text NOT NULL,
    monto numeric(14,2) NOT NULL,
    moneda text NOT NULL DEFAULT 'PEN',
    estado text NOT NULL DEFAULT 'procesada',
    canal text NOT NULL,
    codigo_operacion text UNIQUE DEFAULT ('OP-' || upper(substr(replace(gen_random_uuid()::text,'-',''),1,10))),
    descripcion text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS comprobantes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    operacion_id uuid REFERENCES operaciones(id),
    numero_comprobante text UNIQUE DEFAULT ('CP-' || upper(substr(replace(gen_random_uuid()::text,'-',''),1,10))),
    cliente_id uuid REFERENCES clientes(id),
    monto numeric(14,2),
    descripcion text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notificaciones (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id uuid REFERENCES clientes(id),
    usuario_id uuid REFERENCES usuarios(id),
    titulo text NOT NULL,
    mensaje text NOT NULL,
    tipo text NOT NULL,
    canal text NOT NULL,
    leido boolean DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auditoria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid REFERENCES usuarios(id),
    accion text NOT NULL,
    entidad text NOT NULL,
    entidad_id uuid,
    detalle text,
    created_at timestamptz NOT NULL DEFAULT now()
);
