-- Core ProEmpresa - Datos iniciales
-- Claves de validacion:
-- admin / admin123
-- 0001 / 1234
-- cliente DNI 12345678 / 1234

INSERT INTO agencias (id, codigo, nombre, ciudad, direccion)
VALUES ('10000000-0000-0000-0000-000000000001','AG001','Agencia Principal Huancayo','Huancayo','Av. Principal 123')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO usuarios (id, username, password_hash, nombre, rol, estado)
VALUES
('20000000-0000-0000-0000-000000000001','admin','plain:admin123','Administrador ProEmpresa','admin','activo'),
('20000000-0000-0000-0000-000000000002','asesor01','plain:1234','Asesor Comercial 01','asesor','activo')
ON CONFLICT (username) DO UPDATE SET password_hash=EXCLUDED.password_hash, nombre=EXCLUDED.nombre, rol=EXCLUDED.rol, estado='activo';

INSERT INTO asesores (id, usuario_id, agencia_id, codigo_empleado, nombres, telefono, estado)
VALUES ('30000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000001','0001','Carlos Ramos', '987654321','activo')
ON CONFLICT (codigo_empleado) DO UPDATE SET usuario_id=EXCLUDED.usuario_id, nombres=EXCLUDED.nombres, estado='activo';

INSERT INTO clientes (id, numero_documento, password_hash, nombres, apellidos, telefono, email, direccion, referencia_direccion, latitud_domicilio, longitud_domicilio, estado)
VALUES
('40000000-0000-0000-0000-000000000001','12345678','plain:1234','María Elena','Quispe Rojas','987111222','maria.quispe@email.com','Jr. Real 450, Huancayo','Frente a parque',-12.065312,-75.204532,'activo'),
('40000000-0000-0000-0000-000000000002','45678912','plain:1234','Luis Alberto','Mendoza Soto','987222333','luis.mendoza@email.com','Av. Ferrocarril 820, Huancayo','Galería comercial',-12.063912,-75.207931,'activo'),
('40000000-0000-0000-0000-000000000003','78912345','plain:1234','Rosa','Huamán Torres','987333444','rosa.huaman@email.com','Jr. Ica 315, El Tambo','Mercado cercano',-12.055982,-75.219883,'activo')
ON CONFLICT (numero_documento) DO UPDATE SET nombres=EXCLUDED.nombres, apellidos=EXCLUDED.apellidos, telefono=EXCLUDED.telefono, direccion=EXCLUDED.direccion, estado='activo';

INSERT INTO cliente_negocios (cliente_id, nombre_negocio, giro_negocio, direccion_negocio, referencia_negocio, lat_negocio, lng_negocio, ubicacion_verificada, fuente_ubicacion)
VALUES
('40000000-0000-0000-0000-000000000001','Bodega Virgen del Carmen','Abarrotes','Jr. Real 452, Huancayo','A media cuadra del parque',-12.065410,-75.204680,true,'seed'),
('40000000-0000-0000-0000-000000000002','Confecciones Mendoza','Textil','Av. Ferrocarril 825, Huancayo','Segundo piso galería',-12.063710,-75.207750,true,'seed'),
('40000000-0000-0000-0000-000000000003','Juguería Rosita','Alimentos','Jr. Ica 318, El Tambo','Frente al mercado',-12.055830,-75.219710,true,'seed')
ON CONFLICT (cliente_id) DO UPDATE SET nombre_negocio=EXCLUDED.nombre_negocio, giro_negocio=EXCLUDED.giro_negocio, direccion_negocio=EXCLUDED.direccion_negocio, lat_negocio=EXCLUDED.lat_negocio, lng_negocio=EXCLUDED.lng_negocio;

INSERT INTO cuentas (id, cliente_id, numero_cuenta, tipo_cuenta, moneda, saldo_disponible, saldo_contable, estado)
VALUES
('50000000-0000-0000-0000-000000000001','40000000-0000-0000-0000-000000000001','001-110-000123456','Ahorro Emprendedor','PEN',2500.00,2500.00,'activa'),
('50000000-0000-0000-0000-000000000002','40000000-0000-0000-0000-000000000002','001-110-000223456','Ahorro Simple','PEN',1800.00,1800.00,'activa'),
('50000000-0000-0000-0000-000000000003','40000000-0000-0000-0000-000000000003','001-110-000323456','Ahorro Emprendedor','PEN',3200.00,3200.00,'activa')
ON CONFLICT (numero_cuenta) DO UPDATE SET saldo_disponible=EXCLUDED.saldo_disponible, saldo_contable=EXCLUDED.saldo_contable, estado='activa';

INSERT INTO solicitudes_credito (id, cliente_id, asesor_id, numero_expediente, monto_solicitado, plazo_meses, destino_credito, cuota_estimada, tea_referencial, estado, canal)
VALUES
('60000000-0000-0000-0000-000000000001','40000000-0000-0000-0000-000000000002','30000000-0000-0000-0000-000000000001','PE-SEED-0001',8000,12,'Capital de trabajo',786.67,38.50,'pendiente_visita','seed'),
('60000000-0000-0000-0000-000000000002','40000000-0000-0000-0000-000000000003','30000000-0000-0000-0000-000000000001','PE-SEED-0002',5000,10,'Compra de insumos',590.00,38.50,'pendiente_visita','seed')
ON CONFLICT (numero_expediente) DO UPDATE SET estado='pendiente_visita', monto_solicitado=EXCLUDED.monto_solicitado;

INSERT INTO cartera_comercial (id, asesor_id, cliente_id, solicitud_id, fecha_asignacion, tipo_gestion, prioridad, score_prioridad, monto_referencial, estado_visita, orden_manual)
VALUES
('70000000-0000-0000-0000-000000000001','30000000-0000-0000-0000-000000000001','40000000-0000-0000-0000-000000000002','60000000-0000-0000-0000-000000000001',(now() AT TIME ZONE 'America/Lima')::date,'SOLICITUD_CREDITO','alta',85,8000,'pendiente',1),
('70000000-0000-0000-0000-000000000002','30000000-0000-0000-0000-000000000001','40000000-0000-0000-0000-000000000003','60000000-0000-0000-0000-000000000002',(now() AT TIME ZONE 'America/Lima')::date,'SOLICITUD_CREDITO','media',65,5000,'pendiente',2)
ON CONFLICT (id) DO UPDATE SET estado_visita='pendiente', monto_referencial=EXCLUDED.monto_referencial, updated_at=now();
