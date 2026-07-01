$manifestPath = "android\app\src\main\AndroidManifest.xml"
if (!(Test-Path $manifestPath)) {
    Write-Host "No se encontro AndroidManifest.xml. Ejecuta primero: flutter create . --platforms=android"
    exit 1
}
$content = Get-Content $manifestPath -Raw
if ($content -notmatch "android.permission.INTERNET") {
    $content = $content -replace "<application", "    <uses-permission android:name=`"android.permission.INTERNET`" />`r`n`r`n    <application"
}
if ($content -notmatch "android.permission.ACCESS_FINE_LOCATION") {
    $content = $content -replace "<application", "    <uses-permission android:name=`"android.permission.ACCESS_FINE_LOCATION`" />`r`n    <uses-permission android:name=`"android.permission.ACCESS_COARSE_LOCATION`" />`r`n`r`n    <application"
}
Set-Content -Path $manifestPath -Value $content -Encoding UTF8
Write-Host "Permisos configurados."
