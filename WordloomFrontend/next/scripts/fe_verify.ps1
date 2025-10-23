
param(
  [string]$SrcRoot = "src"
)

Write-Host "=== 二次校验 ==="

# 1) 页面位置
if (Test-Path (Join-Path $SrcRoot "app\orbit\page.tsx")) {
  Write-Host "✔ 页面存在：src/app/orbit/page.tsx"
} else {
  Write-Host "✖ 缺少页面：src/app/orbit/page.tsx" -ForegroundColor Red
}

# 2) Orbit queryKeys.ts
if (Test-Path (Join-Path $SrcRoot "modules\orbit\state\queryKeys.ts")) {
  Write-Host "✔ Orbit queryKeys.ts 存在"
} else {
  Write-Host "✖ 缺少 Orbit queryKeys.ts" -ForegroundColor Red
}

# 3) API base 常量检查（简单字符串搜索）
$apiBaseFiles = Get-ChildItem -Recurse $SrcRoot -Include apiBase.ts,map-api.ts -File
if ($apiBaseFiles.Count -gt 0) {
  $ok = $false
  foreach ($f in $apiBaseFiles) {
    $text = Get-Content $f.FullName -Raw
    if ($text -match "/api/common" -and $text -match "/api/orbit") { $ok = $true }
  }
  if ($ok) { Write-Host "✔ apiBase / map-api 中包含 /api/common 与 /api/orbit" }
  else { Write-Host "✖ apiBase / map-api 未声明两个前缀" -ForegroundColor Yellow }
} else {
  Write-Host "✖ 未找到 apiBase.ts / map-api.ts" -ForegroundColor Yellow
}

Write-Host "校验完成。"
