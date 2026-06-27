#!/usr/bin/env python3
"""
OPC Gateway v2.0 — Multithreaded with SQLite persistence, OpenClaw sync, Hermes bridge.
"""

import json, time, uuid, threading, logging, signal, sys, os, sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
import urllib.request

# ── Config ──────────────────────────────────────────────
PORT = int(os.environ.get("OPC_PORT", 8820))
OC_CONFIG = "/root/.openclaw/openclaw.json"
AGENT_INDEX = "/root/linjiao-tech/memory/profiles/agent-index.json"
DB_PATH = "/root/.opc/state.db"
HERMES_URL = os.environ.get("HERMES_URL", "http://127.0.0.1:8765")
OPENCLAW_URL = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")
OPC_TOKEN = os.environ.get("OPC_TOKEN", "opc-local-token-2026")
HEARTBEAT_TIMEOUT = 60

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [OPC] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
log = logging.getLogger("opc-gateway")

# ── SQLite ──────────────────────────────────────────────
os.makedirs("/root/.opc", exist_ok=True)
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.execute("PRAGMA journal_mode=WAL")
db.execute("""CREATE TABLE IF NOT EXISTS registry (
    agent_id TEXT PRIMARY KEY, name TEXT, role TEXT,
    capabilities TEXT, lease_id TEXT, last_heartbeat REAL,
    load REAL, active_tasks INTEGER, endpoint TEXT
)""")
db.execute("""CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY, capability TEXT, agent TEXT,
    payload TEXT, status TEXT, result TEXT,
    created TEXT, completed TEXT, elapsed_ms INTEGER
)""")
db.execute("""CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT,
    type TEXT, agent_id TEXT, detail TEXT
)""")
db.commit()

# ── In-memory registry (for fast access) ────────────────
registry_lock = threading.Lock()
registry = {}
task_lock = threading.Lock()

def load_registry():
    """Load registry from SQLite on startup"""
    global registry
    with registry_lock:
        rows = db.execute("SELECT * FROM registry").fetchall()
        for r in rows:
            registry[r[0]] = {
                "name": r[1], "role": r[2],
                "capabilities": json.loads(r[3]),
                "lease_id": r[4], "last_heartbeat": r[5],
                "load": r[6], "active_tasks": r[7],
                "endpoint": r[8]
            }
    # Also sync from agent index
    try:
        with open(AGENT_INDEX) as f:
            agents = json.load(f)
        for a in agents:
            if a["id"] not in registry:
                registry[a["id"]] = {
                    "name": a.get("name", a["id"]),
                    "role": a.get("role", ""),
                    "capabilities": a.get("capabilities", []),
                    "lease_id": "", "last_heartbeat": 0,
                    "load": 0, "active_tasks": 0,
                    "endpoint": ""
                }
    except: pass
    log.info(f"Loaded {len(registry)} agents from DB/index")

def persist_registry(aid):
    """Persist one agent to SQLite"""
    info = registry.get(aid, {})
    db.execute("""INSERT OR REPLACE INTO registry VALUES (?,?,?,?,?,?,?,?,?)""",
        (aid, info.get("name",""), info.get("role",""),
         json.dumps(info.get("capabilities",[]), ensure_ascii=False),
         info.get("lease_id",""), info.get("last_heartbeat",0),
         info.get("load",0), info.get("active_tasks",0),
         info.get("endpoint","")))
    db.commit()

def log_event(etype, agent_id, detail=""):
    db.execute("INSERT INTO events (ts,type,agent_id,detail) VALUES (?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), etype, agent_id, detail[:500]))
    db.commit()

# ── Capability Map ──────────────────────────────────────
CAPABILITY_MAP = {
    "context-search": "baize", "memory-query": "baize", "knowledge-graph": "baize",
    "security-audit": "xuanwu", "permission-review": "xuanwu", "key-management": "xuanwu",
    "workflow-orchestration": "qinglong", "pipeline-scheduling": "qinglong",
    "ui-interaction": "zhuque", "page-rendering": "zhuque",
    "attack-defense": "baihu", "penetration-test": "baihu",
    "alerting": "bifang", "anomaly-detection": "bifang",
    "infrastructure": "bixi", "container-orchestration": "bixi",
    "code-review": "bixie", "dependency-audit": "bixie",
    "circuit-breaker": "chiwen", "rate-limiting": "chiwen",
    "data-collection": "dangkang", "etl-pipeline": "dangkang",
    "log-analysis": "diting", "root-cause-analysis": "diting",
    "cron-scheduling": "jinwu", "periodic-task": "jinwu",
    "cost-optimization": "pixiu", "resource-reclaim": "pixiu",
    "messaging": "qingniao", "event-bus": "qingniao",
    "chaos-testing": "qiongqi", "fault-injection": "qiongqi",
    "big-data": "taotie", "batch-processing": "taotie",
    "storage": "taowu", "database-management": "taowu",
    "vision": "chongming", "image-recognition": "chongming",
    "forecasting": "shangyang", "trend-prediction": "shangyang",
    "compliance": "xiezhi", "license-audit": "xiezhi",
    "deployment": "yinglong", "ci-cd": "yinglong",
    "documentation": "zhulong", "api-docs": "zhulong",
}

def route_task(capability, payload):
    target_id = CAPABILITY_MAP.get(capability, "main")
    with registry_lock:
        if target_id in registry and registry[target_id].get("last_heartbeat", 0) > time.time() - HEARTBEAT_TIMEOUT:
            return target_id
        for aid, info in registry.items():
            if capability in info.get("capabilities", []):
                if info.get("last_heartbeat", 0) > time.time() - HEARTBEAT_TIMEOUT:
                    return aid
        if "main" in registry:
            return "main"
    return None

# ── Hermes Bridge ───────────────────────────────────────
def hermes_dispatch(task_id, capability, payload, target):
    """Forward task to Hermes for execution"""
    try:
        url = f"{HERMES_URL}/api/v0/agents/{target}/execute"
        data = json.dumps({
            "task_id": task_id, "capability": capability,
            "payload": payload, "source": "opc-gateway"
        }).encode()
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPC_TOKEN}"
        }, method="POST")
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        log.info(f"Hermes dispatch {task_id} → {target}: {result.get('status','?')}")
        return result
    except Exception as e:
        log.warning(f"Hermes dispatch failed for {task_id}: {e}")
        return {"status": "hermes_unreachable", "error": str(e)}

# ── OpenClaw Sync ───────────────────────────────────────
def sync_from_openclaw():
    """Pull agent registry from OpenClaw"""
    try:
        url = f"{OPENCLAW_URL}/v1/agents"
        req = urllib.request.Request(url, headers={"X-OPC-Token": OPC_TOKEN})
        resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
        agents = resp.get("agents", {})
        with registry_lock:
            for aid, info in agents.items():
                if aid not in registry:
                    registry[aid] = {
                        "name": info.get("name", aid),
                        "role": info.get("role", ""),
                        "capabilities": info.get("capabilities", []),
                        "lease_id": "", "last_heartbeat": time.time(),
                        "load": 0, "active_tasks": 0,
                        "endpoint": info.get("endpoint", "")
                    }
                    persist_registry(aid)
        log.info(f"OpenClaw sync: merged {len(agents)} agents")
        return len(agents)
    except Exception as e:
        log.debug(f"OpenClaw sync skipped: {e}")
        return 0

# ── Heartbeat Checker ───────────────────────────────────
def heartbeat_checker():
    while True:
        with registry_lock:
            now = time.time()
            dead = [aid for aid, info in registry.items()
                    if info.get("last_heartbeat", 0) > 0
                    and now - info["last_heartbeat"] > HEARTBEAT_TIMEOUT]
        for aid in dead:
            log.warning(f"Agent {aid} timed out, evicting")
            log_event("evict", aid)
        time.sleep(10)

# ── OpenClaw Periodic Sync ──────────────────────────────
def openclaw_syncer():
    while True:
        try:
            sync_from_openclaw()
        except:
            pass
        time.sleep(300)  # every 5 min

# ── Multithreaded Server ────────────────────────────────
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class OPCHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(f"{self.client_address[0]} {args[0]}")

    def _check_auth(self):
        return self.headers.get("X-OPC-Token", "") == OPC_TOKEN

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,X-OPC-Token")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/opc/v1/cluster/status":
            with registry_lock:
                online = sum(1 for i in registry.values() if i.get("last_heartbeat",0) > time.time() - HEARTBEAT_TIMEOUT)
            rows = db.execute("SELECT status FROM tasks").fetchall()
            completed = sum(1 for r in rows if r[0] == "completed")
            active = sum(1 for r in rows if r[0] == "dispatched")
            self._send_json({
                "gateway": "OPC Gateway v2.0",
                "uptime_seconds": int(time.time() - start_time),
                "agents_online": online,
                "agents_total": len(registry),
                "tasks_completed": completed,
                "tasks_active": active,
                "load_avg": round(sum(i.get("load",0) for i in registry.values()) / max(len(registry),1), 2),
                "db_size_kb": os.path.getsize(DB_PATH) // 1024,
                "hermes": self._hermes_status(),
                "openclaw": self._openclaw_status(),
            })

        elif path == "/opc/v1/agents":
            self._send_json({
                "agents": {
                    aid: {
                        "name": info.get("name", aid),
                        "role": info.get("role", ""),
                        "load": info.get("load", 0),
                        "active_tasks": info.get("active_tasks", 0),
                        "last_heartbeat_ago": int(time.time() - info.get("last_heartbeat", 0)),
                        "endpoint": info.get("endpoint", "")
                    } for aid, info in registry.items()
                },
                "count": len(registry)
            })

        elif path == "/opc/v1/tasks":
            rows = db.execute("SELECT * FROM tasks ORDER BY created DESC LIMIT 50").fetchall()
            self._send_json({
                "tasks": [{
                    "task_id": r[0], "capability": r[1], "agent": r[2],
                    "status": r[4], "created": r[6], "completed": r[7]
                } for r in rows],
                "count": len(rows)
            })

        elif path == "/opc/v1/capabilities":
            self._send_json({"capabilities": CAPABILITY_MAP, "total": len(CAPABILITY_MAP)})

        elif path == "/health":
            self._send_json({"ok": True, "status": "live", "service": "OPC Gateway v2.0"})

        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path == "/opc/v1/agents/register":
            aid = body.get("agent_id")
            if not aid:
                return self._send_json({"error": "agent_id required"}, 400)
            lease_id = f"lease_{uuid.uuid4().hex[:12]}"
            with registry_lock:
                registry[aid] = {
                    "name": body.get("name", aid),
                    "role": body.get("role", ""),
                    "capabilities": body.get("capabilities", []),
                    "lease_id": lease_id,
                    "last_heartbeat": time.time(),
                    "load": 0,
                    "active_tasks": 0,
                    "endpoint": body.get("endpoint", "")
                }
            persist_registry(aid)
            log_event("register", aid, body.get("name", ""))
            log.info(f"Agent registered: {aid} ({body.get('name','')})")
            self._send_json({
                "status": "registered", "agent_id": aid, "lease_id": lease_id,
                "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=HEARTBEAT_TIMEOUT)).isoformat()
            })

        elif path == "/opc/v1/agents/heartbeat":
            aid = body.get("agent_id")
            lease = body.get("lease_id")
            with registry_lock:
                if aid not in registry:
                    return self._send_json({"error": "agent not registered"}, 404)
                if registry[aid]["lease_id"] != lease:
                    return self._send_json({"error": "invalid lease"}, 403)
                registry[aid].update({
                    "last_heartbeat": time.time(),
                    "load": body.get("load", 0),
                    "active_tasks": body.get("active_tasks", 0)
                })
            self._send_json({"status": "alive", "lease_renewed": True})

        elif path == "/opc/v1/tasks/dispatch":
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            capability = body.get("capability", "general")
            payload = body.get("payload", {})
            target = route_task(capability, payload)
            if not target:
                return self._send_json({"error": "no online agent", "capability": capability}, 503)

            now_iso = datetime.now(timezone.utc).isoformat()
            db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
                (task_id, capability, target, json.dumps(payload, ensure_ascii=False),
                 "dispatched", None, now_iso, None, 0))
            db.commit()
            log_event("dispatch", target, f"{task_id}:{capability}")
            log.info(f"Task {task_id} → {target} [{capability}]")

            # Try Hermes execution
            hermes_result = hermes_dispatch(task_id, capability, payload, target)
            hermes_status = hermes_result.get("status", "unreachable")

            self._send_json({
                "status": "dispatched", "task_id": task_id,
                "assigned_agent": target, "hermes": hermes_status,
                "estimated_ms": 5000
            })

        elif path == "/opc/v1/tasks/callback":
            task_id = body.get("task_id")
            now_iso = datetime.now(timezone.utc).isoformat()
            db.execute("UPDATE tasks SET status=?, result=?, completed=?, elapsed_ms=? WHERE task_id=?",
                (body.get("status","unknown"),
                 json.dumps(body.get("result"), ensure_ascii=False) if body.get("result") else None,
                 now_iso, body.get("elapsed_ms", 0), task_id))
            db.commit()
            log_event("callback", body.get("agent_id",""), task_id)
            log.info(f"Task {task_id} {body.get('status')} by {body.get('agent_id')}")
            self._send_json({"status": "acknowledged"})

        elif path == "/opc/v1/agents/deregister":
            aid = body.get("agent_id")
            with registry_lock:
                if aid in registry:
                    del registry[aid]
            db.execute("DELETE FROM registry WHERE agent_id=?", (aid,))
            db.commit()
            log_event("deregister", aid)
            self._send_json({"status": "deregistered", "agent_id": aid})

        elif path == "/opc/v1/openclaw/sync":
            count = sync_from_openclaw()
            self._send_json({"status": "synced", "merged": count})

        elif path == "/opc/v1/hermes/status":
            self._send_json(self._hermes_status())

        else:
            self._send_json({"error": "not found"}, 404)

    def _hermes_status(self):
        try:
            req = urllib.request.Request(f"{HERMES_URL}/health", headers={"Authorization": f"Bearer {OPC_TOKEN}"})
            resp = json.loads(urllib.request.urlopen(req, timeout=2).read())
            return {"connected": True, "health": resp}
        except:
            return {"connected": False}

    def _openclaw_status(self):
        try:
            req = urllib.request.Request(f"{OPENCLAW_URL}/health", headers={"X-OPC-Token": OPC_TOKEN})
            resp = json.loads(urllib.request.urlopen(req, timeout=2).read())
            return {"connected": True, "health": resp}
        except:
            return {"connected": False}

# ── Main ────────────────────────────────────────────────
start_time = time.time()

def main():
    load_registry()
    threading.Thread(target=heartbeat_checker, daemon=True).start()
    threading.Thread(target=openclaw_syncer, daemon=True).start()

    # Initial OpenClaw sync
    try:
        n = sync_from_openclaw()
        if n: log.info(f"Initial OpenClaw sync: {n} agents merged")
    except: pass

    server = ThreadingHTTPServer(("127.0.0.1", PORT), OPCHandler)
    log.info(f"OPC Gateway v2.0 listening on 127.0.0.1:{PORT} (multithreaded)")

    def shutdown(sig, frame):
        log.info("Shutting down...")
        server.shutdown()
        db.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
