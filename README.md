# 灵枢 · OPC Labs

> **Omni-Protocol Consortium** — 开放协作协议，多模态 Agent 集群平台

灵枢，取自《黄帝内经·灵枢篇》，专论经络气血调度，是全身运行的枢纽。
OPC 以此为名：一座 Agent 的经络中枢，23 神兽各司其职，任何智能体只要遵循 OPC 协议即可接入，不限语言、不限模型、不限形态。

---

## 架构总览

```
┌──────────────────────────────────────────────────┐
│              灵枢 · OPC Gateway                  │
│                                                  │
│  Registry ── Capability Matrix ── Model Router  │
│       │              │                  │         │
│  ┌────┴──────────────┴──────────────────┴─────┐ │
│  │          Event Bus (能力变更广播)            │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  REST API (HTTP) · SSE (stream) · WebSocket     │
└──────────────┬───────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ▼          ▼          ▼          ▼
  白泽       玄武       青龙       朱雀
 (记忆)    (安全)     (编排)     (UI)
    │          │          │          │
    └──────────┴──────────┴──────────┘
          23 Agent 编队 · 46+ 能力项
```

## 核心原则

| 原则 | 说明 |
|------|------|
| **协议优先** | Agent 只需实现 register / heartbeat / callback 三个端点 |
| **不绑定语言** | Python / Go / Node / Bash 均可，协议统一 |
| **不绑定模型** | GPT / Claude / 混元 / 本地模型，Agent 自描述 |
| **能力自发现** | 新 Agent 上线自动广播能力，路由即时生效 |
| **多模态原生** | text / image / audio / video 内嵌载荷 |
| **热进化** | 能力变更无需重启 Gateway，实时广播 |

## 文件结构

```
linjiao-tech/
├── README.md                 ← 本文件
├── OPC-Protocol-v3.md        ← OPC 协议规范 v3.0
├── AGENTS.md                 ← 23 神兽编制总览
├── IDENTITY.md               ← 麒麟（主控中枢）身份
│
├── opc-gateway-v2.py         ← 多线程网关 (已部署)
├── agent-runtime.py          ← Agent 运行时 (已部署)
├── opc-launch-v2.sh          ← 集群一键启动器
│
├── baihu/  baize/  bifang/   ← 各神兽工作目录
├── bixi/   bixie/  chiwen/
├── ...                                          (23 个)
└── avatars/                  ← 神兽头像
```

## 启动

```bash
wsl bash /root/opc-launch-v2.sh start    # 一键拉起 Gateway + 23 Agent
wsl bash /root/opc-launch-v2.sh status   # 集群状态
wsl bash /root/opc-launch-v2.sh stop     # 停止
```

## 协议版本演进

| 版本 | 状态 | 核心特性 |
|------|------|---------|
| v1.0 | 历史 | 固定路由表 + 本地注册 + JSON over HTTP |
| v2.0 | **运行中** | 多线程 Gateway + SQLite 持久化 + Agent Runtime |
| v3.0 | 设计完成 | 自描述能力 + 多模态 + 模型路由 + 热进化 |
| v4.0 | 规划中 | 跨集群联邦 + 分布式共识 + 能力市场 |

## 接入新 Agent

```python
# 三步加入 OPC 集群
POST /opc/v3/agents/register     # 声明身份 + 能力 + 模型
POST /opc/v3/agents/heartbeat    # 每 30s 保活
POST /opc/v3/tasks/callback      # 执行完成回调
```

5 行 Bash 脚本也能成为神兽。

---

**灵枢 · OPC Labs** — 活的中枢，不是死的代码。
