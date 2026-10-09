<#
    Biên dịch app ra file APK — chạy hoàn toàn bằng dòng lệnh, không cần mở Android Studio.

    Cách dùng:
        .\build-apk.ps1              # build bản debug
        .\build-apk.ps1 -Sach        # xoá cache rồi build lại từ đầu

    Lần đầu chạy sẽ lâu (Gradle tải thư viện). Các lần sau nhanh hơn nhiều.
#>
param([switch]$Sach)

$ErrorActionPreference = "Stop"
$Duan = Join-Path (Split-Path -Parent $PSScriptRoot) "android"

function Buoc($n, $t) { Write-Host "`n[$n] $t" -ForegroundColor Cyan }
function Xong($t)     { Write-Host "  OK  $t" -ForegroundColor Green }
function Loi($t)      { Write-Host "  LOI $t" -ForegroundColor Red }

# ── JDK 17 ──────────────────────────────────────────────────
Buoc 1 "Tim JDK 17"
$jdk = Get-ChildItem "C:\Program Files\Microsoft\jdk-17*" -Directory -EA SilentlyContinue |
       Select-Object -First 1
if (-not $jdk) {
    Loi "Chua co JDK 17. Cai bang lenh:  winget install Microsoft.OpenJDK.17"
    exit 1
}
$env:JAVA_HOME = $jdk.FullName
Xong $env:JAVA_HOME

# Vi sao khong dung JDK di kem Android Studio: ban do la OpenJDK 25,
# Gradle 8.7 chi ho tro toi JDK 21 nen se bao loi.

# ── Android SDK ─────────────────────────────────────────────
Buoc 2 "Kiem tra Android SDK"
# SDK đã dời sang ổ D (10/2026) — thử chỗ mới trước, rồi chỗ mặc định cũ
$sdk = @("D:\Android\Sdk", "$env:LOCALAPPDATA\Android\Sdk") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $sdk) { Loi "Khong thay Android SDK"; exit 1 }
$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
foreach ($c in @("platforms\android-34", "build-tools", "platform-tools")) {
    if (Test-Path "$sdk\$c") { Xong $c } else { Loi "thieu $c" }
}

# local.properties tro toi SDK (Gradle can file nay)
$lp = Join-Path $Duan "local.properties"
$duongDan = $sdk -replace '\\', '\\'
# KHÔNG dùng Set-Content -Encoding utf8: PS 5.1 ghi BOM, Gradle đọc khoá thành BOM+"sdk.dir" rồi báo SDK location not found
[System.IO.File]::WriteAllText($lp, "sdk.dir=$duongDan", (New-Object System.Text.UTF8Encoding($false)))
Xong "Da ghi local.properties"

# ── Build ───────────────────────────────────────────────────
Buoc 3 "Bien dich"
Push-Location $Duan
try {
    if ($Sach) { & .\gradlew.bat clean --no-daemon }
    & .\gradlew.bat assembleDebug --no-daemon
    $ma = $LASTEXITCODE
} finally { Pop-Location }

# ── Ket qua ─────────────────────────────────────────────────
$apk = Join-Path $Duan "app\build\outputs\apk\debug\app-debug.apk"
if ($ma -eq 0 -and (Test-Path $apk)) {
    $mb = [math]::Round((Get-Item $apk).Length / 1MB, 2)
    Write-Host "`n────────────────────────────────────────" -ForegroundColor Green
    Write-Host " BUILD THANH CONG — $mb MB" -ForegroundColor Green
    Write-Host " $apk"
    Write-Host "────────────────────────────────────────" -ForegroundColor Green
    Write-Host "`nCai len robot:"
    Write-Host "  python tools\day-web.py --cai      (cap USB o DAU robot; qua Wi-Fi thi them --ip <IP-robot>)"
} else {
    Write-Host "`nBUILD HONG (ma loi $ma)" -ForegroundColor Red
    Write-Host "Doc thong bao loi o tren. Cac loi hay gap:"
    Write-Host "  - 'Unsupported class file major version' -> sai phien ban JDK"
    Write-Host "  - 'Failed to resolve com.github.orionagent' -> mang chan jitpack.io"
    Write-Host "  - 'SDK location not found' -> thieu Android SDK, xem buoc 2"
    exit 1
}
