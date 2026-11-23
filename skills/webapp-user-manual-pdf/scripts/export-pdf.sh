#!/usr/bin/env bash
# ==============================================================================
# Web Application User Manual - Headless PDF Exporter (Bash / POSIX)
# Compatible with macOS and Linux (Google Chrome, Chromium, Brave, Microsoft Edge)
# ==============================================================================

set -euo pipefail

INPUT_HTML=""
OUTPUT_PDF="output_manual.pdf"

print_usage() {
  echo "การใช้งาน: $0 --input <ไฟล์ HTML> [--output <ไฟล์ PDF>]"
  echo "ตัวอย่าง:   $0 --input manual-pdf.html --output User_Manual.pdf"
  exit 1
}

# ประมวลผล Flag Arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)
      INPUT_HTML="$2"
      shift 2
      ;;
    -o|--output)
      OUTPUT_PDF="$2"
      shift 2
      ;;
    -h|--help)
      print_usage
      ;;
    *)
      if [[ -z "$INPUT_HTML" ]]; then
        INPUT_HTML="$1"
        shift
      else
        echo "❌ Argument ไม่ถูกต้อง: $1"
        print_usage
      fi
      ;;
  esac
done

if [[ -z "$INPUT_HTML" ]]; then
  echo "❌ กรุณาระบุไฟล์ HTML ต้นทาง (--input <file>)"
  print_usage
fi

if [[ ! -f "$INPUT_HTML" ]]; then
  echo "❌ ไม่พบไฟล์ HTML: $INPUT_HTML"
  exit 1
fi

# ค้นหา Browser Executable บนระบบ
BROWSER_BIN=""
CANDIDATES=(
  # Linux binaries
  "google-chrome"
  "google-chrome-stable"
  "chromium"
  "chromium-browser"
  "microsoft-edge"
  "microsoft-edge-stable"
  "brave-browser"
  # macOS binaries
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  "/Applications/Chromium.app/Contents/MacOS/Chromium"
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
)

for candidate in "${CANDIDATES[@]}"; do
  if command -v "$candidate" >/dev/null 2>&1; then
    BROWSER_BIN="$candidate"
    break
  elif [[ -x "$candidate" ]]; then
    BROWSER_BIN="$candidate"
    break
  fi
done

if [[ -z "$BROWSER_BIN" ]]; then
  echo "❌ ไม่พบ Google Chrome หรือ Chromium ในระบบ กรุณาติดตั้งเบราว์เซอร์ หรือเปิดไฟล์ในเบราว์เซอร์แล้วสั่งพิมพ์ด้วย Cmd+P / Ctrl+P"
  exit 1
fi

# แปลงเป็น Absolute Path
if command -v realpath >/dev/null 2>&1; then
  FULL_INPUT="$(realpath "$INPUT_HTML")"
  OUTPUT_DIR="$(dirname "$OUTPUT_PDF")"
  OUTPUT_BASE="$(basename "$OUTPUT_PDF")"
  FULL_OUTPUT="$(realpath "$OUTPUT_DIR")/$OUTPUT_BASE"
else
  FULL_INPUT="$(cd "$(dirname "$INPUT_HTML")" && pwd)/$(basename "$INPUT_HTML")"
  FULL_OUTPUT="$(cd "$(dirname "$OUTPUT_PDF")" && pwd)/$(basename "$OUTPUT_PDF")"
fi

echo "🚀 กำลังแปลงไฟล์ HTML เป็น PDF..."
echo "   ต้นทาง: $FULL_INPUT"
echo "   ปลายทาง: $FULL_OUTPUT"
echo "   ใช้เบราว์เซอร์: $BROWSER_BIN"

"$BROWSER_BIN" \
  --headless \
  --disable-gpu \
  --run-all-compositor-stages-before-draw \
  --no-pdf-header-footer \
  --print-to-pdf-no-header \
  --print-to-pdf="$FULL_OUTPUT" \
  "file://$FULL_INPUT"

if [[ -f "$FULL_OUTPUT" ]]; then
  echo "✅ ส่งออกเป็นไฟล์ PDF สำเร็จเรียบร้อย: $FULL_OUTPUT"
else
  echo "❌ แปลงไฟล์ไม่สำเร็จ ตรวจสอบสิทธิ์การเขียนไฟล์"
  exit 1
fi
