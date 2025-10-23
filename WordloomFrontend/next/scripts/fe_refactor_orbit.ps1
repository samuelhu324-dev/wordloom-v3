
param(
  [string]$SrcRoot = "src"
)

$ErrorActionPreference = "Stop"

# 1) 确保 app/orbit 目录存在
$orbitAppDir = Join-Path $SrcRoot "app\orbit"
New-Item -ItemType Directory -Force -Path $orbitAppDir | Out-Null

# 2) 移动 modules/orbit/page.tsx -> app/orbit/page.tsx （存在才移动）
$oldPage = Join-Path $SrcRoot "modules\orbit\page.tsx"
$newPage = Join-Path $SrcRoot "app\orbit\page.tsx"
if (Test-Path $oldPage) {
  Move-Item $oldPage $newPage -Force
  Write-Host "已移动: $oldPage -> $newPage"
} else {
  Write-Host "未找到 $oldPage（可能已手动移动），跳过"
}

# 3) 确保 Orbit 有自己的 queryKeys.ts（若不存在则从 Loom 复制一份模板）
$orbitKeys = Join-Path $SrcRoot "modules\orbit\state\queryKeys.ts"
$loomKeys  = Join-Path $SrcRoot "modules\loom\state\queryKeys.ts"
$orbitKeysDir = Split-Path $orbitKeys -Parent
New-Item -ItemType Directory -Force -Path $orbitKeysDir | Out-Null

if (-not (Test-Path $orbitKeys)) {
  if (Test-Path $loomKeys) {
    Copy-Item $loomKeys $orbitKeys -Force
    (Get-Content $orbitKeys) -replace "loom", "orbit" | Set-Content $orbitKeys -Encoding utf8
    Write-Host "已从 Loom 复制 queryKeys.ts -> Orbit，并替换命名空间为 'orbit'"
  } else {
    # 生成一个极简模板
    $template = @"
export const orbitKeys = {
  all: ['orbit'] as const,
  tasks: () => [...orbitKeys.all, 'tasks'] as const,
  memos: () => [...orbitKeys.all, 'memos'] as const,
  stats: () => [...orbitKeys.all, 'stats'] as const,
};
"@
    $template | Set-Content $orbitKeys -Encoding utf8
    Write-Host "已生成 Orbit 的最小 queryKeys.ts 模板"
  }
} else {
  Write-Host "检测到已有 Orbit 的 queryKeys.ts，跳过复制"
}

# 4) 输出硬编码 '/api/' 的扫描结果（排除 apiBase.ts / map-api.ts）
Write-Host "`n=== 扫描硬编码 '/api/' 的文件（请手动改为使用 apiBase 常量） ==="
$files = Get-ChildItem -Recurse $SrcRoot -Include *.ts,*.tsx -File |
  Where-Object { $_.FullName -notmatch "apiBase\.ts|map-api\.ts|node_modules" }

$hits = @()
foreach ($f in $files) {
  $content = Get-Content $f.FullName -Raw
  if ($content -match "/api/") { $hits += $f.FullName }
}
if ($hits.Count -gt 0) {
  $hits | %{ Write-Host "发现硬编码: $_" -ForegroundColor Yellow }
} else {
  Write-Host "未发现硬编码 /api/，良好。" -ForegroundColor Green
}

Write-Host "`n完成。请继续执行 .\scripts\fe_verify.ps1 进行二次校验。"
