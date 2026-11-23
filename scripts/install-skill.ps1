<#
.SYNOPSIS
    Universal Multi-Agent Skill Installer (PowerShell)
    รองรับการติดตั้ง Skill ไปยัง Google Antigravity, Anthropic Claude Code, และ OpenAI Codex
.DESCRIPTION
    สคริปต์นี้ช่วยคัดลอกโฟลเดอร์ Skill จากคลังส่วนตัวไปยังตำแหน่งของ AI Agent ที่ต้องการ
    รองรับทั้งการติดตั้งระดับเครื่อง (Global Scope) และระดับโปรเจกต์ (Workspace Scope)
.PARAMETER Skill
    ชื่อ Skill ที่ต้องการติดตั้ง เช่น 'webapp-user-manual' หรือระบุ 'all' เพื่อติดตั้งทุก Skill (ค่าเริ่มต้น: 'all')
.PARAMETER Agent
    AI Agent เป้าหมาย: 'antigravity', 'claude', 'codex' หรือ 'all' (ค่าเริ่มต้น: 'all')
.PARAMETER Scope
    ขอบเขตการติดตั้ง: 'global' หรือ 'workspace' (ค่าเริ่มต้น: 'global')
.PARAMETER WorkspacePath
    ที่อยู่โฟลเดอร์โปรเจกต์ (จำเป็นเมื่อ -Scope workspace และไม่ต้องการใช้ไดเรกทอรีปัจจุบัน)
.EXAMPLE
    .\scripts\install-skill.ps1 -Skill webapp-user-manual -Agent claude
.EXAMPLE
    .\scripts\install-skill.ps1 -Skill all -Agent all -Scope global
.EXAMPLE
    .\scripts\install-skill.ps1 -Skill webapp-user-manual-pdf -Agent codex -Scope workspace -WorkspacePath "D:\Projects\my-app"
#>

param (
    [Parameter(Mandatory=$false)]
    [string]$Skill = "all",

    [Parameter(Mandatory=$false)]
    [ValidateSet("antigravity", "claude", "claude-code", "codex", "all")]
    [string]$Agent = "all",

    [Parameter(Mandatory=$false)]
    [ValidateSet("global", "workspace")]
    [string]$Scope = "global",

    [Parameter(Mandatory=$false)]
    [string]$WorkspacePath = "."
)

# ค้นหาไดเรกทอรีรากของคลัง Skills
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$skillsDir = Join-Path $repoRoot "skills"

if (-not (Test-Path $skillsDir)) {
    Write-Error "❌ ไม่พบไดเรกทอรี skills ที่: $skillsDir"
    exit 1
}

# รวบรวมรายชื่อ Skill ที่จะติดตั้ง
$availableSkills = Get-ChildItem -Path $skillsDir -Directory | Select-Object -ExpandProperty Name
$skillsToInstall = @()

if ($Skill -eq "all") {
    $skillsToInstall = $availableSkills
} else {
    if ($availableSkills -contains $Skill) {
        $skillsToInstall = @($Skill)
    } else {
        Write-Error "❌ ไม่พบ Skill ชื่อ '$Skill' ในคลัง (Skills ที่มี: $($availableSkills -join ', '))"
        exit 1
    }
}

# กำหนดรายชื่อ Agent ที่ต้องติดตั้ง
$agentsToTarget = @()
switch -Regex ($Agent) {
    "all" { $agentsToTarget = @("antigravity", "claude", "codex") }
    "claude.*" { $agentsToTarget = @("claude") }
    "antigravity" { $agentsToTarget = @("antigravity") }
    "codex" { $agentsToTarget = @("codex") }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🧠 Universal Multi-Agent Skill Installer (Phase 1)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "📦 Skills ที่จะติดตั้ง: $($skillsToInstall -join ', ')" -ForegroundColor White
Write-Host "🤖 AI Agents เป้าหมาย: $($agentsToTarget -join ', ')" -ForegroundColor White
Write-Host "🎯 Scope การติดตั้ง: $Scope" -ForegroundColor White
if ($Scope -eq "workspace") {
    $resolvedWorkspace = (Resolve-Path $WorkspacePath).Path
    Write-Host "📁 Workspace ปลายทาง: $resolvedWorkspace" -ForegroundColor White
}
Write-Host ""

$userProfile = $env:USERPROFILE
$successCount = 0

foreach ($targetAgent in $agentsToTarget) {
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "🔧 กำลังประมวลผลสำหรับ: $targetAgent" -ForegroundColor Yellow

    $destinationBase = ""
    if ($Scope -eq "global") {
        switch ($targetAgent) {
            "antigravity" {
                $destinationBase = Join-Path $userProfile ".gemini\config\skills"
            }
            "claude" {
                $destinationBase = Join-Path $userProfile ".claude\skills"
            }
            "codex" {
                $destinationBase = Join-Path $userProfile ".codex\skills"
            }
        }
    } else {
        $resolvedWorkspace = (Resolve-Path $WorkspacePath).Path
        switch ($targetAgent) {
            "antigravity" {
                $destinationBase = Join-Path $resolvedWorkspace ".agent\skills"
            }
            "claude" {
                $destinationBase = Join-Path $resolvedWorkspace ".claude\skills"
            }
            "codex" {
                $destinationBase = Join-Path $resolvedWorkspace ".codex\skills"
            }
        }
    }

    if (-not (Test-Path $destinationBase)) {
        New-Item -ItemType Directory -Path $destinationBase -Force | Out-Null
        Write-Host "   📁 สร้างไดเรกทอรี: $destinationBase" -ForegroundColor DarkCyan
    }

    foreach ($skillName in $skillsToInstall) {
        $srcPath = Join-Path $skillsDir $skillName
        $destPath = Join-Path $destinationBase $skillName

        try {
            if (Test-Path $destPath) {
                Remove-Item -Path $destPath -Recurse -Force
            }
            Copy-Item -Path $srcPath -Destination $destPath -Recurse -Force
            Write-Host "   ✅ ติดตั้ง '$skillName' -> $destPath" -ForegroundColor Green
            $successCount++
        } catch {
            Write-Host "   ❌ ล้มเหลวในการติดตั้ง '$skillName': $_" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🎉 การติดตั้งเสร็จสิ้นเรียบร้อย (สำเร็จ: $successCount รายการ)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
