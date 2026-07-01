# ProEmpresa Core

Ecosistema digital compuesto por Core, Portal Web, App Cliente y App Fuerza de Ventas.

## Base de datos en Supabase

Ejecutar en SQL Editor:

1. `database/01_schema.sql`
2. `database/02_seed_inicial.sql`
3. `database/03_indexes.sql`

## Backend en Render

Root Directory:

```text
01_core_proempresa/backend_fastapi
```

Build Command:

```text
python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

Start Command:

```text
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Variables en Render:

```env
APP_ENV=production
DATABASE_URL=postgresql://postgres.xxxxx:PASSWORD@aws-xxxx.pooler.supabase.com:5432/postgres?sslmode=require
SECRET_KEY=CAMBIAR_POR_UNA_CLAVE_LARGA
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=https://proempresa-core.vercel.app,http://localhost:5173
PYTHON_VERSION=3.11.9
```

## Portal en Vercel

Root Directory:

```text
01_core_proempresa/frontend_react
```

Variable en Vercel:

```env
VITE_API_BASE_URL=https://proempresa-api.onrender.com
```

## Flujo de crédito

1. Cliente registra solicitud desde App Cliente.
2. Core crea solicitud y la asigna automáticamente a cartera comercial del asesor `0001`.
3. Fuerza de Ventas muestra la solicitud en cartera para visita/entrevista.
4. Asesor registra visita con GPS.
5. Core permite aprobar y desembolsar la solicitud.
6. Al aprobar, el Core crea crédito, deposita en la cuenta del cliente, registra movimiento y operación.
