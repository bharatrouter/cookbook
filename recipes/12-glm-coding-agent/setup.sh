#!/usr/bin/env bash
# One-shot: OpenCode coding agent on GLM via BharatRouter.  (macOS + Linux; for
# Windows use setup.ps1).  Idempotent — safe to re-run.  Handles the known snags:
#   1. opencode-ai postinstall fails  -> install platform binary + shim onto PATH
#   2. ~/.cache may be root-owned      -> redirect XDG_CACHE_HOME
#   3. PATH dir not writable on Linux  -> fall back to ~/.local/bin (no sudo)
#   4. first-time key                  -> prompt (hidden), store 600, smoke-test
set -euo pipefail

PROJ="$HOME/projects/opencode-glm"
CACHE="$HOME/.local/cache"
KEYFILE="$HOME/.config/bharatrouter/env"
API="https://api.bharatrouter.com"

# --- pick a writable PATH dir, no sudo ---
choose_bindir() {
  for d in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do
    if [ -d "$d" ] && [ -w "$d" ]; then echo "$d"; return; fi
  done
  mkdir -p "$HOME/.local/bin"; echo "$HOME/.local/bin"
}

# --- 1. install opencode (platform binary; meta package postinstall is broken) ---
if ! command -v opencode >/dev/null 2>&1; then
  case "$(uname -s)-$(uname -m)" in
    Darwin-arm64)   PKG=opencode-darwin-arm64 ;;
    Darwin-x86_64)  PKG=opencode-darwin-x64 ;;
    Linux-x86_64)   PKG=opencode-linux-x64 ;;
    Linux-aarch64|Linux-arm64) PKG=opencode-linux-arm64 ;;
    *) echo "unsupported platform $(uname -s)-$(uname -m); see opencode.ai/docs"; exit 1 ;;
  esac
  echo "installing $PKG ..."
  npm install -g "$PKG" >/dev/null 2>&1 || true
  BIN="$(npm root -g)/$PKG/bin/opencode"
  [ -x "$BIN" ] || { echo "binary not found at $BIN — try: npm i -g $PKG"; exit 1; }
  BINDIR="$(choose_bindir)"
  ln -sf "$BIN" "$BINDIR/opencode"
  echo "linked opencode -> $BINDIR/opencode"
  PATH="$BINDIR:$PATH"
else
  echo "opencode already on PATH ($(command -v opencode))"
fi

# --- 2. writable cache (works around root-owned ~/.cache) ---
mkdir -p "$CACHE"
export XDG_CACHE_HOME="$CACHE"

# --- 3. project + provider config ---
mkdir -p "$PROJ"
cat > "$PROJ/opencode.json" <<'JSON'
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
JSON

# --- 4. first-time key: env > keyfile > interactive prompt ---
mkdir -p "$(dirname "$KEYFILE")"
KEY="${BHARATROUTER_API_KEY:-}"
[ -z "$KEY" ] && [ -f "$KEYFILE" ] && KEY="$(sed -n 's/.*BHARATROUTER_API_KEY="\(.*\)".*/\1/p' "$KEYFILE")"
if [ -z "$KEY" ]; then
  if [ -t 0 ]; then
    printf "Enter your BharatRouter API key (starts br-): "
    read -rs KEY; echo
  else
    echo "NOTE: no key found; set one later:  echo 'export BHARATROUTER_API_KEY=\"br-...\"' > $KEYFILE"
  fi
fi
if [ -n "$KEY" ]; then
  case "$KEY" in br-*) ;; *) echo "warning: key does not start with 'br-' — continuing anyway";; esac
  printf 'export BHARATROUTER_API_KEY="%s"\n' "$KEY" > "$KEYFILE"
  chmod 600 "$KEYFILE"
  echo "key stored (600) at $KEYFILE"
  # smoke-test the BR key (auth)
  printf "verifying key against %s ... " "$API"
  code="$(curl -s -o /dev/null -w '%{http_code}' "$API/v1/models" -H "Authorization: Bearer $KEY" || echo 000)"
  case "$code" in
    200) echo "OK" ;;
    401|403) echo "REJECTED ($code) — check the key / rotate it" ;;
    *) echo "got HTTP $code (network/zscaler?) — key stored, verify later" ;;
  esac
fi

# --- 4b. ensure glm-4.6 actually routes; if not, save a GLM BYOK key ---
glm_ok=false
glm_test() {  # echoes the HTTP code of a 1-token glm-4.6 call
  curl -s -o /dev/null -w '%{http_code}' "$API/v1/chat/completions" \
    -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
    -d '{"model":"glm-4.6","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}' || echo 000
}
if [ -n "$KEY" ] && [ "${code:-}" = "200" ]; then
  printf "checking glm-4.6 routing ... "
  if [ "$(glm_test)" = "200" ]; then
    echo "routes already (platform/BYOK present)"; glm_ok=true
  else
    echo "needs your own GLM key (BYOK)"
    if [ -t 0 ]; then
      printf "GLM provider [zhipu/openrouter] (default zhipu): "; read -r PROV; PROV="${PROV:-zhipu}"
      if [ "$PROV" = "zhipu" ]; then echo "  (a Zhipu key from z.ai looks like <id>.<secret> — works as a raw bearer)"; fi
      printf "Enter your %s API key: " "$PROV"; read -rs PKEY; echo
      if [ -n "$PKEY" ]; then
        printf "saving BYOK to BharatRouter ... "
        bc="$(curl -s -o /dev/null -w '%{http_code}' -X PUT "$API/me/byok/$PROV" \
              -H "Content-Type: application/json" -H "Authorization: Bearer $KEY" \
              -d "{\"key\":\"$PKEY\",\"label\":\"glm\"}" || echo 000)"
        echo "HTTP $bc"
        printf "re-checking glm-4.6 ... "
        if [ "$(glm_test)" = "200" ]; then echo "OK"; glm_ok=true; else echo "still not routing — check the provider key"; fi
      fi
    else
      echo "  -> save one later:  curl -X PUT $API/me/byok/zhipu -H 'Authorization: Bearer \$BHARATROUTER_API_KEY' -H 'Content-Type: application/json' -d '{\"key\":\"<id>.<secret>\",\"label\":\"glm\"}'"
    fi
  fi
fi

# --- 5. shell wiring (idempotent block in the right rc) ---
case "${SHELL:-}" in *zsh) RC="$HOME/.zshrc";; *) RC="$HOME/.bashrc";; esac
MARK="# >>> opencode-glm (bharatrouter) >>>"
if ! grep -qF "$MARK" "$RC" 2>/dev/null; then
  BINDIR="$(choose_bindir)"
  cat >> "$RC" <<RC
$MARK
export XDG_CACHE_HOME="\$HOME/.local/cache"
[ -f "$KEYFILE" ] && . "$KEYFILE"
case ":\$PATH:" in *":$BINDIR:"*) ;; *) export PATH="$BINDIR:\$PATH";; esac
oc-glm() { ( cd "$PROJ" && opencode "\$@" ); }
# <<< opencode-glm (bharatrouter) <<<
RC
  echo "wired oc-glm into $RC"
else
  echo "shell block already present in $RC"
fi

# --- 6. auto-run the first query so the user sees it working immediately ---
if [ "$glm_ok" = true ]; then
  export BHARATROUTER_API_KEY="$KEY"
  echo
  echo "=== first query: how much cost can we save with GLM? ==="
  ( cd "$PROJ" && opencode run --model bharatrouter/glm-4.6 \
      "In about 6 lines: roughly how much can a team save on coding-agent token costs by using GLM-4.6 instead of a frontier model (e.g. Claude Opus / GPT-4-class)? Use approximate public per-million-token input/output prices, show the comparison, and give a ballpark % saving." \
  ) || echo "(first query skipped — run 'oc-glm run ...' manually)"
fi

echo
echo "DONE.  ->  source $RC   then:   oc-glm run --model bharatrouter/glm-4.6 \"<task>\""
