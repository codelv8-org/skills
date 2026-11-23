<#
.SYNOPSIS
    ส่งออกไฟล์ HTML คู่มือเป็นไฟล์ PDF ขนาด A4 ผ่าน Headless Browser (Microsoft Edge หรือ Google Chrome)
.DESCRIPTION
    สคริปต์นี้จะค้นหาเบราว์เซอร์ Chromium ในระบบ (Edge หรือ Chrome) และสั่งพิมพ์ไฟล์ HTML เป็น PDF
    โดยปิดการแสดง Header/Footer อัตโนมัติของบราวเซอร์ เพื่อให้แสดงผลตาม CSS Paged Media (@page) อย่างสมบูรณ์
.PARAMETER InputHtml
    ที่อยู่ไฟล์ HTML ต้นทาง (เช่น .\manual-pdf.html)
.PARAMETER OutputPdf
    ที่อยู่ไฟล์ PDF ปลายทาง (เช่น .\manual.pdf)
.EXAMPLE
    .\export-pdf.ps1 -InputHtml "manual-pdf.html" -OutputPdf "manual.pdf"
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$InputHtml,

    [Parameter(Mandatory=$false)]
    [string]$OutputPdf = "output_manual.pdf"
)

# ตรวจสอบว่าไฟล์ HTML มีอยู่จริงหรือไม่
if (-not (Test-Path $InputHtml)) {
    Write-Error "ไม่พบไฟล์ HTML ต้นทาง: $InputHtml"
    exit 1
}

# แปลงเป็น Full Path สำหรับเบราว์เซอร์
$fullInputPath = (Resolve-Path $InputHtml).Path
$fullOutputPath = [System.IO.Path]::GetFullPath($OutputPdf)

# ค้นหา Browser Executable
$browserPaths = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)

$browserExe = $null
foreach ($path in $browserPaths) {
    if (Test-Path $path) {
        $browserExe = $path
        break
    }
}

if (-not $browserExe) {
    Write-Error "ไม่พบโปรแกรม Microsoft Edge หรือ Google Chrome ในตำแหน่งมาตรฐาน กรุณาเปิดไฟล์ HTML ในเบราว์เซอร์แล้วสั่งพิมพ์ด้วย Ctrl+P แทน"
    exit 1
}

Write-Host "🚀 กำลังแปลงไฟล์ HTML เป็น PDF..." -ForegroundColor Cyan
Write-Host "   ต้นทาง: $fullInputPath" -ForegroundColor Gray
Write-Host "   ปลายทาง: $fullOutputPath" -ForegroundColor Gray
Write-Host "   ใช้เบราว์เซอร์: $browserExe" -ForegroundColor Gray

# สั่งพิมพ์ Headless พร้อมตัด Header/Footer บราวเซอร์
$args = @(
    "--headless",
    "--disable-gpu",
    "--run-all-compositor-stages-before-draw",
    "--no-pdf-header-footer",
    "--print-to-pdf-no-header",
    "--print-to-pdf=`"$fullOutputPath`"",
    "`"$fullInputPath`""
)

$process = Start-Process -FilePath $browserExe -ArgumentList $args -Wait -PassThru

if ($process.ExitCode -eq 0 -and (Test-Path $fullOutputPath)) {
    $fileSize = (Get-Item $fullOutputPath).Length / 1KB
    Write-Host "✅ ส่งออกเป็นไฟล์ PDF สำเร็จเรียบร้อย!" -ForegroundColor Green
    Write-Host "   ขนาดไฟล์: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Green
    Write-Host "   ที่อยู่ไฟล์: $fullOutputPath" -ForegroundColor Yellow
} else {
    Write-Error "❌ เกิดข้อผิดพลาดในการแปลงไฟล์เป็น PDF (ExitCode: $($process.ExitCode))"
}
