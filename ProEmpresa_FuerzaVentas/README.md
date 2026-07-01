# App Fuerza de Ventas ProEmpresa

Crear plataforma Android si no existe:

```powershell
flutter create . --platforms=android
.\configurar_android.ps1
flutter pub get
```

Ejecutar con nube:

```powershell
flutter run --dart-define=API_BASE_URL=https://proempresa-api.onrender.com
```

APK:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://proempresa-api.onrender.com
```
