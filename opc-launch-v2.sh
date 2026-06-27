#!/bin/bash
# opc-launch-v2.sh — Start OPC Gateway v2 + All Agent Runtimes
set -e

OPC_DIR="/root/.opc"
LOG_DIR="$OPC_DIR/logs"
mkdir -p "$LOG_DIR"

# ── Colors ──────────────────────────────────────────────
G='\e[32m' Y='\e[33m' R='\e[31m' N='\e[0m'

AGENTS=(main baihu baize bifang bixi bixie chiwen chongming dangkang diting
        jinwu pixiu qinglong qingniao qiongqi shangyang taotie taowu
        xiezhi xuanwu yinglong zhulong zhuque)

# ── Commands ────────────────────────────────────────────
start_all() {
    echo -e "${G}╔══════════════════════════════════╗${N}"
    echo -e "${G}║   OPC v2.0 Cluster Bootstrap    ║${N}"
    echo -e "${G}╚══════════════════════════════════╝${N}"

    # Kill old instances
    pkill -f opc-gateway-v2 2>/dev/null || true
    pkill -f agent-runtime 2>/dev/null || true
    sleep 1

    # Start Gateway
    echo -n "Gateway... "
    setsid python3 /root/opc-gateway-v2.py > "$LOG_DIR/gateway.log" 2>&1 & disown
    sleep 2

    # Verify
    if curl -sf http://127.0.0.1:8820/health > /dev/null 2>&1; then
        echo -e "${G}OK${N} (port 8820)"
    else
        echo -e "${R}FAILED${N}"
        exit 1
    fi

    # Start Agent Runtimes
    echo "Agents:"
    local ok=0
    for aid in "${AGENTS[@]}"; do
        OPC_AGENT_ID="$aid" setsid python3 /root/agent-runtime.py > /dev/null 2>&1 & disown
        sleep 0.3
        ok=$((ok+1))
        echo -e "  ${G}✓${N} $aid"
    done
    echo -e "\n${G}All $ok/23 agents launched${N}"

    sleep 3
    status
}

stop_all() {
    echo "Stopping OPC cluster..."
    pkill -f opc-gateway-v2 2>/dev/null || true
    pkill -f agent-runtime 2>/dev/null || true
    sleep 1
    echo "Done"
}

status() {
    echo ""
    echo -e "${Y}═══ OPC Cluster Status ═══${N}"
    local resp
    resp=$(curl -sf http://127.0.0.1:8820/opc/v1/cluster/status 2>/dev/null || echo '{"error":"gateway down"}')
    echo "$resp" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"  Gateway:    {d.get('gateway','?')}\")
    print(f\"  Uptime:     {d.get('uptime_seconds',0)}s\")
    print(f\"  Agents:     {d.get('agents_online',0)}/{d.get('agents_total',0)} online\")
    print(f\"  Completed:  {d.get('tasks_completed',0)} tasks\")
    print(f\"  Active:     {d.get('tasks_active',0)} tasks\")
    print(f\"  Load avg:   {d.get('load_avg',0)}\")
    print(f\"  DB:         {d.get('db_size_kb',0)} KB\")
    h = d.get('hermes',{})
    o = d.get('openclaw',{})
    print(f\"  Hermes:     {'connected' if h.get('connected') else 'offline'}\")
    print(f\"  OpenClaw:   {'connected' if o.get('connected') else 'offline'}\")
except: print(sys.stdin.read())
"
}

# ── Dispatch ────────────────────────────────────────────
case "${1:-start}" in
    start)  start_all ;;
    stop)   stop_all ;;
    restart) stop_all; start_all ;;
    status) status ;;
    *) echo "Usage: $0 {start|stop|restart|status}" ;;
esac
