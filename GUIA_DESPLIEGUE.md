# Guía de despliegue ProEmpresa

## 1. Supabase

Crear proyecto y ejecutar los SQL:

```text
ProEmpresa_Core/01_core_proempresa/database/01_schema.sql
ProEmpresa_Core/01_core_proempresa/database/02_seed_inicial.sql
ProEmpresa_Core/01_core_proempresa/database/03_indexes.sql
```

## 2. Render

Servicio Web con:

```text
Root Directory: ProEmpresa_Core/01_core_proempresa/backend_fastapi
Build Command: python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Variables:

```env
APP_ENV=production
DATABASE_URL=URL_DE_SUPABASE
SECRET_KEY=CLAVE_LARGA
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=https://URL_DE_VERCEL,http://localhost:5173
PYTHON_VERSION=3.11.9
```

## 3. Vercel

Proyecto Vite:

```text
Root Directory: ProEmpresa_Core/01_core_proempresa/frontend_react
Install Command: npm install --legacy-peer-deps --no-audit --no-fund
Build Command: npm run build
Output Directory: dist
```

Variable:

```env
VITE_API_BASE_URL=https://URL_RENDER
```

## 4. Apps móviles

Dentro de cada app:

```powershell
flutter create . --platforms=android
.\configurar_android.ps1
flutter pub get
flutter run --dart-define=API_BASE_URL=https://URL_RENDER
```

APK:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://URL_RENDER
```
