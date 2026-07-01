# App Cliente ProEmpresa

Crear plataforma Android si no existe:

```powershell
flutter create . --platforms=android
.\configurar_android.ps1
flutter pub get
```

Ejecutar local:

```powershell
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8003
```

Ejecutar con nube:

```powershell
flutter run --dart-define=API_BASE_URL=https://proempresa-api.onrender.com
```

APK:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://proempresa-api.onrender.com
```
