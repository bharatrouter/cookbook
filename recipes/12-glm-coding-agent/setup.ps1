# One-shot: OpenCode coding agent on GLM via BharatRouter — Windows (PowerShell 5+).
# Mirrors setup.sh.  Run:  powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = 'Stop'

$Proj    = Join-Path $HOME 'projects\opencode-glm'
$KeyFile = Join-Path $HOME '.config\bharatrouter\env.ps1'
$Api     = 'https://api.bharatrouter.com'

# --- 1. install opencode (platform binary; meta package postinstall is broken) ---
if (-not (Get-Command opencode -ErrorAction SilentlyContinue)) {
  $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'x64' }
  $pkg  = "opencode-windows-$arch"
  Write-Host "installing $pkg ..."
  npm install -g $pkg 2>$null | Out-Null
  $root = (npm root -g).Trim()
  $bin  = Join-Path $root "$pkg\bin\opencode.exe"
  if (-not (Test-Path $bin)) { throw "binary not found at $bin — try: npm i -g $pkg (or install via 'scoop install opencode')" }
  # shim onto PATH via the npm global dir (already on PATH)
  $npmBin = Split-Path (Get-Command npm).Source
  Set-Content -Path (Join-Path $npmBin 'opencode.cmd') -Value "@`"$bin`" %*" -Encoding Ascii
  Write-Host "shimmed opencode -> $npmBin\opencode.cmd"
} else {
  Write-Host "opencode already on PATH ($((Get-Command opencode).Source))"
}

# --- 2. project + provider config ---
New-Item -ItemType Directory -Force -Path $Proj | Out-Null
@'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "bharatrouter": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "BharatRouter",
      "options": {
        "baseURL": "https://api.bharatrouter.com/v1",
        "apiKey": "{env:BHARATROUTER_API_KEY}"
      },
      "models": {
        "glm-4.6": { "name": "GLM-4.6" },
        "glm-4.5-air": { "name": "GLM-4.5 Air" },
        "glm-4.7-flash": { "name": "GLM-4.7 Flash" }
      }
    }
  },
  "model": "bharatrouter/glm-4.6"
}
'@ | Set-Content -Path (Join-Path $Proj 'opencode.json') -Encoding UTF8

# --- 3. first-time key: env > keyfile > interactive prompt ---
New-Item -ItemType Directory -Force -Path (Split-Path $KeyFile) | Out-Null
$key = $env:BHARATROUTER_API_KEY
if (-not $key -and (Test-Path $KeyFile)) { . $KeyFile; $key = $env:BHARATROUTER_API_KEY }
if (-not $key) {
  $sec = Read-Host -AsSecureString "Enter your BharatRouter API key (starts br-)"
  $key = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
           [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}
$verified = $false
if ($key) {
  if ($key -notlike 'br-*') { Write-Host "warning: key does not start with 'br-'" }
  "`$env:BHARATROUTER_API_KEY = '$key'" | Set-Content -Path $KeyFile -Encoding Ascii
  [Environment]::SetEnvironmentVariable('BHARATROUTER_API_KEY', $key, 'User')  # persist for new shells
  $env:BHARATROUTER_API_KEY = $key
  Write-Host "key stored at $KeyFile and in user env"
  Write-Host "verifying key against $Api ..." -NoNewline
  try {
    $r = Invoke-WebRequest -Uri "$Api/v1/models" -Headers @{ Authorization = "Bearer $key" } -UseBasicParsing -TimeoutSec 20
    if ($r.StatusCode -eq 200) { Write-Host " OK" ; $verified = $true } else { Write-Host " HTTP $($r.StatusCode)" }
  } catch { Write-Host " could not verify (network/zscaler?) — key stored, try later" }
}

# --- 3b. ensure glm-4.6 routes; if not, save a GLM BYOK key ---
$glmOk = $false
function Test-Glm {
  $body = '{"model":"glm-4.6","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}'
  try {
    $r = Invoke-WebRequest -Uri "$Api/v1/chat/completions" -Method Post -ContentType 'application/json' `
           -Headers @{ Authorization = "Bearer $key" } -Body $body -UseBasicParsing -TimeoutSec 30
    return ($r.StatusCode -eq 200)
  } catch { return $false }
}
if ($verified) {
  Write-Host "checking glm-4.6 routing ..." -NoNewline
  if (Test-Glm) { Write-Host " routes already"; $glmOk = $true }
  else {
    Write-Host " needs your own GLM key (BYOK)"
    $prov = Read-Host "GLM provider [zhipu/openrouter] (default zhipu)"; if (-not $prov) { $prov = 'zhipu' }
    if ($prov -eq 'zhipu') { Write-Host "  (a Zhipu key from z.ai looks like <id>.<secret>)" }
    $psec = Read-Host -AsSecureString "Enter your $prov API key"
    $pkey = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($psec))
    if ($pkey) {
      Write-Host "saving BYOK to BharatRouter ..." -NoNewline
      try {
        Invoke-WebRequest -Uri "$Api/me/byok/$prov" -Method Put -ContentType 'application/json' `
          -Headers @{ Authorization = "Bearer $key" } -Body (@{ key = $pkey; label = 'glm' } | ConvertTo-Json) `
          -UseBasicParsing -TimeoutSec 20 | Out-Null
        Write-Host " done"
      } catch { Write-Host " failed: $($_.Exception.Message)" }
      Write-Host "re-checking glm-4.6 ..." -NoNewline
      if (Test-Glm) { Write-Host " OK"; $glmOk = $true } else { Write-Host " still not routing — check the provider key" }
    }
  }
}

# --- 4. shell wiring (PowerShell profile, idempotent) ---
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
$mark = '# >>> opencode-glm (bharatrouter) >>>'
if (-not (Select-String -Path $PROFILE -SimpleMatch $mark -Quiet)) {
@"
$mark
if (Test-Path '$KeyFile') { . '$KeyFile' }
function oc-glm { Push-Location '$Proj'; try { opencode @args } finally { Pop-Location } }
# <<< opencode-glm (bharatrouter) <<<
"@ | Add-Content -Path $PROFILE -Encoding UTF8
  Write-Host "wired oc-glm into $PROFILE"
} else { Write-Host "shell block already present in $PROFILE" }

# --- 5. auto-run the first query so the user sees it working immediately ---
if ($glmOk) {
  Write-Host "`n=== first query: how much cost can we save with GLM? ==="
  Push-Location $Proj
  try {
    opencode run --model bharatrouter/glm-4.6 "In about 6 lines: roughly how much can a team save on coding-agent token costs by using GLM-4.6 instead of a frontier model (e.g. Claude Opus / GPT-4-class)? Use approximate public per-million-token input/output prices, show the comparison, and give a ballpark % saving."
  } finally { Pop-Location }
}

Write-Host "`nDONE.  Open a new terminal (or . `$PROFILE), then:  oc-glm run --model bharatrouter/glm-4.6 ""<task>"""
