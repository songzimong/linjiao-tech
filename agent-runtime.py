#!/usr/bin/env python3
"""
OPC Agent Runtime — Consumes tasks from Gateway, executes, sends callbacks.
Each agent process: register → poll for tasks → execute → callback → repeat.
"""

import json, time, uuid, threading, logging, sys, os, signal
import urllib.request, urllib.error

# ── Config ──────────────────────────────────────────────
AGENT_ID = os.environ.get("OPC_AGENT_ID", sys.argv[1] if len(sys.argv) > 1 else "main")
GATEWAY_URL = os.environ.get("OPC_GATEWAY_URL", "http://127.0.0.1:8820")
TOKEN = os.environ.get("OPC_TOKEN", "opc-local-token-2026")
POLL_INTERVAL = int(os.environ.get("OPC_POLL_INTERVAL", 3))

# ── Logging ─────────────────────────────────────────────
os.makedirs("/root/.opc/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [{AGENT_ID}] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.FileHandler(f"/root/.opc/logs/agent_{AGENT_ID}.log"), logging.StreamHandler(sys.stderr)]
)
log = logging.getLogger(f"agent-{AGENT_ID}")

# ── Agent capabilities ──────────────────────────────────
AGENT_CAPABILITIES = {
    "main":       ["master-control", "task-orchestration"],
    "baize":      ["context-search", "memory-query", "knowledge-graph"],
    "xuanwu":     ["security-audit", "permission-review", "key-management"],
    "qinglong":   ["workflow-orchestration", "pipeline-scheduling"],
    "zhuque":     ["ui-interaction", "page-rendering"],
    "baihu":      ["attack-defense", "penetration-test"],
    "bifang":     ["alerting", "anomaly-detection"],
    "bixi":       ["infrastructure", "container-orchestration"],
    "bixie":      ["code-review", "dependency-audit"],
    "chiwen":     ["circuit-breaker", "rate-limiting"],
    "chongming":  ["vision", "image-recognition"],
    "dangkang":   ["data-collection", "etl-pipeline"],
    "diting":     ["log-analysis", "root-cause-analysis"],
    "jinwu":      ["cron-scheduling", "periodic-task"],
    "pixiu":      ["cost-optimization", "resource-reclaim"],
    "qingniao":   ["messaging", "event-bus"],
    "qiongqi":    ["chaos-testing", "fault-injection"],
    "shangyang":  ["forecasting", "trend-prediction"],
    "taotie":     ["big-data", "batch-processing"],
    "taowu":      ["storage", "database-management"],
    "xiezhi":     ["compliance", "license-audit"],
    "yinglong":   ["deployment", "ci-cd"],
    "zhulong":    ["documentation", "api-docs"],
}

NAMES = {
    "main":"麒麟","baize":"白泽","xuanwu":"玄武","qinglong":"青龙","zhuque":"朱雀",
    "baihu":"白虎","bifang":"毕方","bixi":"赑屃","bixie":"辟邪","chiwen":"螭吻",
    "chongming":"重明","dangkang":"当康","diting":"谛听","jinwu":"金乌","pixiu":"貔貅",
    "qingniao":"青鸟","qiongqi":"穷奇","shangyang":"商羊","taotie":"饕餮","taowu":"梼杌",
    "xiezhi":"獬豸","yinglong":"应龙","zhulong":"烛龙",
}

ROLES = {
    "main":"主控中枢","baize":"知识中枢","xuanwu":"安全审计","qinglong":"编排引擎","zhuque":"前端交互",
    "baihu":"攻防调度","bifang":"异常告警","bixi":"基础设施","bixie":"代码净化","chiwen":"熔断降级",
    "chongming":"图像视觉","dangkang":"数据采集","diting":"日志分析","jinwu":"定时调度","pixiu":"资源优化",
    "qingniao":"消息通信","qiongqi":"混沌测试","shangyang":"预测分析","taotie":"大数据处理","taowu":"持久化存储",
    "xiezhi":"合规审计","yinglong":"部署执行","zhulong":"文档生成",
}

caps = AGENT_CAPABILITIES.get(AGENT_ID, [])
name = NAMES.get(AGENT_ID, AGENT_ID)
role = ROLES.get(AGENT_ID, "general")

# ── API helpers ─────────────────────────────────────────
def api(method, path, data=None):
    url = f"{GATEWAY_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Content-Type": "application/json", "X-OPC-Token": TOKEN
    })
    try:
        return json.loads(urllib.request.urlopen(req, timeout=5).read())
    except Exception as e:
        return {"error": str(e)}

# ── Task execution stub ─────────────────────────────────
def execute_task(task):
    """Execute a task — stub that returns agent capability info.
    In production, this would dispatch to actual tools/skills."""
    task_id = task["task_id"]
    capability = task.get("capability", "general")
    payload = task.get("payload", {})

    log.info(f"EXEC {task_id} [{capability}]")

    result = {
        "agent": AGENT_ID,
        "agent_name": name,
        "agent_role": role,
        "capabilities": caps,
        "execution": "stub",
        "received_at": time.time(),
        "capability": capability,
        "message": f"Agent {name}({AGENT_ID}) received task [{capability}]",
        "acknowledges": f"我({name})已知晓同伴：玄武保安全，青龙管编排，朱雀通前端…共23神兽协同",
    }
    return result

# ── Main loop ───────────────────────────────────────────
def main():
    log.info(f"Starting {name}({AGENT_ID}) Runtime — capabilities: {caps}")

    # Register with Gateway
    lease_id = None
    for attempt in range(5):
        resp = api("POST", "/opc/v1/agents/register", {
            "agent_id": AGENT_ID, "name": name, "role": role,
            "capabilities": caps, "heartbeat_interval": 30,
            "endpoint": f"http://127.0.0.1:8820/agents/{AGENT_ID}"
        })
        if resp.get("status") == "registered":
            lease_id = resp["lease_id"]
            log.info(f"Registered (lease={lease_id[:20]}...)")
            break
        log.warning(f"Register attempt {attempt+1} failed: {resp.get('error','?')}")
        time.sleep(2)
    else:
        log.error("Failed to register after 5 attempts")
        sys.exit(1)

    # Heartbeat thread (uses mutable list to avoid closure issues)
    lease_container = [lease_id]
    def heartbeat():
        while True:
            resp = api("POST", "/opc/v1/agents/heartbeat", {
                "agent_id": AGENT_ID, "lease_id": lease_container[0],
                "load": 0.0, "active_tasks": 0
            })
            if resp.get("status") != "alive":
                log.warning("Heartbeat lost, re-registering...")
                r = api("POST", "/opc/v1/agents/register", {
                    "agent_id": AGENT_ID, "name": name, "role": role,
                    "capabilities": caps, "heartbeat_interval": 30,
                    "endpoint": f"http://127.0.0.1:8820/agents/{AGENT_ID}"
                })
                if r.get("status") == "registered":
                    lease_container[0] = r["lease_id"]
                    log.info("Re-registered")
            time.sleep(30)

    threading.Thread(target=heartbeat, daemon=True).start()

    # Task execution loop
    tasks_done = 0
    while True:
        # Check for tasks assigned to this agent
        resp = api("GET", "/opc/v1/tasks")
        for task in resp.get("tasks", []):
            if task["agent"] == AGENT_ID and task["status"] == "dispatched":
                # Execute and callback
                start = time.time()
                result = execute_task(task)
                elapsed = int((time.time() - start) * 1000)

                cb = api("POST", "/opc/v1/tasks/callback", {
                    "task_id": task["task_id"],
                    "agent_id": AGENT_ID,
                    "status": "completed",
                    "result": result,
                    "elapsed_ms": elapsed
                })
                if cb.get("status") == "acknowledged":
                    tasks_done += 1
                    log.info(f"  ✓ {task['task_id']} completed ({elapsed}ms) | total: {tasks_done}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
