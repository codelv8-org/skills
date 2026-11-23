#!/usr/bin/env bash
# ==============================================================================
# Universal Multi-Agent Skill Installer (Bash / POSIX)
# Compatible with macOS, Linux, and WSL
# Target Agents: Antigravity (~/.gemini), Claude Code (~/.claude), Codex (~/.codex)
# ==============================================================================

set -euo pipefail

SKILL="all"
AGENT="all"
SCOPE="global"
WORKSPACE_PATH="."

print_usage() {
  echo "การใช้งาน: $0 [--skill <ชื่อ-skill|all>] [--agent <antigravity|claude|codex|all>] [--scope <global|workspace>] [--workspace <path>]"
  echo ""
  echo "ตัวอย่าง:"
  echo "  $0 --skill webapp-user-manual --agent claude"
  echo "  $0 --skill all --agent all --scope global"
  echo "  $0 --skill webapp-user-manual-pdf --agent codex --scope workspace --workspace /path/to/project"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill|-s)
      SKILL="$2"
      shift 2
      ;;
    --agent|-a)
      AGENT="$2"
      shift 2
      ;;
    --scope)
      SCOPE="$2"
      shift 2
      ;;
    --workspace|-w)
      WORKSPACE_PATH="$2"
      shift 2
      ;;
    --help|-h)
      print_usage
      ;;
    *)
      echo "❌ พารามิเตอร์ไม่ถูกต้อง: $1"
      print_usage
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"

if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "❌ ไม่พบไดเรกทอรี skills: $SKILLS_DIR"
  exit 1
fi

# ค้นหา Skills ที่มีอยู่
AVAILABLE_SKILLS=()
for dir in "$SKILLS_DIR"/*/; do
  if [[ -d "$dir" ]]; then
    AVAILABLE_SKILLS+=("$(basename "$dir")")
  fi
done

SKILLS_TO_INSTALL=()
if [[ "$SKILL" == "all" ]]; then
  SKILLS_TO_INSTALL=("${AVAILABLE_SKILLS[@]}")
else
  FOUND=false
  for item in "${AVAILABLE_SKILLS[@]}"; do
    if [[ "$item" == "$SKILL" ]]; then
      FOUND=true
      SKILLS_TO_INSTALL+=("$SKILL")
      break
    fi
  done
  if [[ "$FOUND" == false ]]; then
    echo "❌ ไม่พบ Skill ชื่อ '$SKILL' (มี: ${AVAILABLE_SKILLS[*]})"
    exit 1
  fi
fi

# กำหนดรายชื่อ Agent
AGENTS_TO_TARGET=()
case "$AGENT" in
  all)
    AGENTS_TO_TARGET=("antigravity" "claude" "codex")
    ;;
  claude|claude-code)
    AGENTS_TO_TARGET=("claude")
    ;;
  antigravity)
    AGENTS_TO_TARGET=("antigravity")
    ;;
  codex)
    AGENTS_TO_TARGET=("codex")
    ;;
  *)
    echo "❌ Agent ไม่ถูกต้อง: $AGENT (รองรับ: antigravity, claude, codex, all)"
    exit 1
    ;;
esac

echo "=========================================================="
echo "🧠 Universal Multi-Agent Skill Installer (Phase 1)"
echo "=========================================================="
echo "📦 Skills: ${SKILLS_TO_INSTALL[*]}"
echo "🤖 Agents: ${AGENTS_TO_TARGET[*]}"
echo "🎯 Scope:  $SCOPE"
echo ""

SUCCESS_COUNT=0

for target in "${AGENTS_TO_TARGET[@]}"; do
  echo "----------------------------------------------------------"
  echo "🔧 กำลังประมวลผลสำหรับ: $target"

  DEST_BASE=""
  if [[ "$SCOPE" == "global" ]]; then
    case "$target" in
      antigravity)
        DEST_BASE="$HOME/.gemini/config/skills"
        ;;
      claude)
        DEST_BASE="$HOME/.claude/skills"
        ;;
      codex)
        DEST_BASE="$HOME/.codex/skills"
        ;;
    esac
  else
    ABS_WORKSPACE="$(cd "$WORKSPACE_PATH" && pwd)"
    case "$target" in
      antigravity)
        DEST_BASE="$ABS_WORKSPACE/.agent/skills"
        ;;
      claude)
        DEST_BASE="$ABS_WORKSPACE/.claude/skills"
        ;;
      codex)
        DEST_BASE="$ABS_WORKSPACE/.codex/skills"
        ;;
    esac
  fi

  mkdir -p "$DEST_BASE"

  for s in "${SKILLS_TO_INSTALL[@]}"; do
    SRC="$SKILLS_DIR/$s"
    DEST="$DEST_BASE/$s"

    rm -rf "$DEST"
    cp -R "$SRC" "$DEST"
    echo "   ✅ ติดตั้ง '$s' -> $DEST"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  done
done

echo ""
echo "=========================================================="
echo "🎉 ติดตั้งเสร็จสิ้นเรียบร้อย (สำเร็จ: $SUCCESS_COUNT รายการ)"
echo "=========================================================="
