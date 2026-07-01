# Ecosistema ProEmpresa

Contiene:

- `ProEmpresa_Core`: backend FastAPI, portal React y scripts SQL.
- `ProEmpresa_AppCliente`: aplicación móvil Flutter para clientes.
- `ProEmpresa_FuerzaVentas`: aplicación móvil Flutter para asesores.

## Credenciales de validación

- Portal Core: `admin` / `admin123`
- Fuerza de Ventas: `0001` / `1234`
- App Cliente: DNI `12345678` / `1234`

## Flujo principal

La solicitud de préstamo creada por el cliente se registra en el Core y se refleja automáticamente en la cartera de Fuerza de Ventas. Luego, el asesor realiza visita/entrevista, y cuando el Core aprueba la solicitud se desembolsa el importe en la cuenta del cliente.
