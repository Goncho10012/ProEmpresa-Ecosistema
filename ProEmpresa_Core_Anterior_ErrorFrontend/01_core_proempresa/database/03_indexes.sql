CREATE INDEX IF NOT EXISTS idx_clientes_documento ON clientes(numero_documento);
CREATE INDEX IF NOT EXISTS idx_solicitudes_cliente ON solicitudes_credito(cliente_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes_credito(estado);
CREATE INDEX IF NOT EXISTS idx_cartera_asesor_fecha ON cartera_comercial(asesor_id, fecha_asignacion);
CREATE INDEX IF NOT EXISTS idx_movimientos_cliente ON movimientos_cuenta(cliente_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_operaciones_created ON operaciones(created_at DESC);
