---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: d9bd63fb95daf4f45cedf90df782023d_bcc5f619721711f1897e5254002afed2
    ReservedCode1: mS6KRz434rFCdUoJoIFzRVYkAw/Rj9EhV1HEx4BGy7FXau4LgAKSeYn4Lj1fuNhRUCR6WA3TTh46IwUFn7Zhec2jA89H7K3hLMrWycYxZkwf9bWLQj68TXV1iWrk5U0mzWSw/2EWygHjrqHbxzSaHXBHPnYQTPgEQX0DB710bcD7pB/kseiuwfY1G60=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: d9bd63fb95daf4f45cedf90df782023d_bcc5f619721711f1897e5254002afed2
    ReservedCode2: mS6KRz434rFCdUoJoIFzRVYkAw/Rj9EhV1HEx4BGy7FXau4LgAKSeYn4Lj1fuNhRUCR6WA3TTh46IwUFn7Zhec2jA89H7K3hLMrWycYxZkwf9bWLQj68TXV1iWrk5U0mzWSw/2EWygHjrqHbxzSaHXBHPnYQTPgEQX0DB710bcD7pB/kseiuwfY1G60=
---

# OPC Protocol v3.0 — 开放协作协议
> 协议优先于实现。凡是遵循本协议的 Agent，不论语言/运行时/模型，自动加入 OPC 集群。

## 一、核心原则

### 1.1 三个"不绑定"
- **不绑定语言**：Agent 可以是 Python 进程、Go 二进制、Node 服务、甚至 Bash 脚本。只要走 HTTP/JSON 协议。
- **不绑定模型**：Agent 背后的模型可以是任何 LLM（GPT/Claude/混元/本地模型）、视觉模型、音频模型、专用小模型。
- **不绑定能力**：不预先定义能力列表。Agent 上线时自我描述 "我能做什么"，Gateway 动态构建路由。

### 1.2 自描述 (Self-Describing)
每个 Agent 注册时必须携带完整的能力描述，而不是依赖 Gateway 的硬编码映射：

```json
POST /opc/v3/agents/register
{
  "agent_id": "baize",
  "name": "白泽",
  "version": "1.2.0",
  "runtime": "python3.11",
  "model": {
    "provider": "openai-api",
    "model": "gpt-4o",
    "modalities": ["text"]
  },
  "capabilities": [
    {
      "id": "memory-query",
      "description": "查询记忆总线中的历史上下文",
      "input_modalities": ["text"],
      "output_modalities": ["text"],
      "confidence": 0.95,
      "max_tokens": 4096,
      "priority": "high"
    },
    {
      "id": "image-search",
      "description": "基于视觉特征搜索图片",
      "input_modalities": ["image", "text"],
      "output_modalities": ["image", "text"],
      "confidence": 0.82,
      "model_required": ["vision"],
      "priority": "normal"
    }
  ],
  "health_check": "/health",
  "heartbeat_interval": 30
}
```

### 1.3 能力发现 (Capability Discovery)
Agent 启动后，Gateway 自动广播新能力列表给所有在线的 Agent。任何 Agent 都能查询集群的完整能力矩阵：

```json
GET /opc/v3/capabilities/matrix
{
  "matrix": {
    "image-search": {
      "agents": ["baize", "chongming"],
      "min_confidence": 0.82,
      "max_confidence": 0.95,
      "routing": "best_confidence"
    },
    "text-generation": {
      "agents": ["zhulong", "main", "qinglong"],
      "min_confidence": 0.85,
      "routing": "round_robin"
    }
  },
  "total_capabilities": 46,
  "total_agents": 23,
  "updated_at": "2026-06-27T18:50:00Z"
}
```

不再需要手动维护 `CAPABILITY_MAP` 字典。新 Agent 上线 → 自动注册能力 → 路由即时生效。

## 二、多模态任务协议

### 2.1 内嵌多模态
任务载荷不限定纯文本。`payload` 中可以携带任意模态的数据：

```json
POST /opc/v3/tasks/dispatch
{
  "capability": "image-analysis",
  "modality": "image+text",
  "payload": {
    "text_query": "这张截图里有什么异常？",
    "images": [
      {
        "encoding": "base64",
        "mime": "image/png",
        "data": "iVBORw0KGgo..."
      }
    ]
  }
}
```

对于音频/视频，payload 传文件路径或流 URL，由 Agent 自行获取处理。

### 2.2 流式结果 (Streaming)
大模型推理可能耗时长，支持 SSE 流式回传：

```http
GET /opc/v3/tasks/{task_id}/stream
Accept: text/event-stream

data: {"chunk": "根据分析...", "progress": 0.3}
data: {"chunk": "发现3处异常...", "progress": 0.7}
data: {"status": "completed", "result": {...}}
```

### 2.3 模态路由
Gateway 根据任务携带的 `modality` 字段匹配具备对应 `input_modalities` 的 Agent。例如携带 `image` 的任务不会被路由到纯文本 Agent。

## 三、大模型接入层

### 3.1 模型注册
Agent 注册时声明自己背后的模型：

```json
"model": {
  "provider": "openai-api | anthropic | local | custom",
  "model": "gpt-4o | claude-sonnet-4 | hunyuan-pro | llama-3-70b",
  "modalities": ["text", "image", "audio"],
  "context_window": 128000,
  "max_output_tokens": 4096,
  "cost_per_1k_input": 0.0025,
  "cost_per_1k_output": 0.01,
  "endpoint": "http://127.0.0.1:11434/v1"  // 本地模型地址
}
```

Gateway 构建**模型路由矩阵**——根据任务需求自动选择最合适的模型：
- 图片任务 → 优先选用带 `vision` 模态的 Agent
- 长文本 → 优先选用 `context_window` 大的 Agent
- 成本敏感 → 优先本地模型

### 3.2 模型热切换
同一 Agent 可以动态切换模型，无需重新注册：

```json
POST /opc/v3/agents/{agent_id}/model
{
  "model": "claude-opus-4",
  "reason": "upgrading for complex task"
}
```

Gateway 实时更新路由表，后续任务自动路由到新模型。

## 四、自进化机制

### 4.1 能力版本化
Agent 的能力不是静态的。每次能力变更自动触发版本更新：

```json
POST /opc/v3/agents/{agent_id}/capabilities/update
{
  "version": "1.3.0",
  "added": ["video-analysis"],
  "removed": [],
  "updated": {
    "image-search": {"confidence": 0.91, "note": "fine-tuned model"}
  }
}
```

Gateway 广播能力变更事件给所有 Agent，确保集群感知实时更新。

### 4.2 能力继承
新 Agent 可以声明"继承"已有 Agent 的能力，无需重复声明：

```json
{
  "agent_id": "baize-v2",
  "inherit_from": "baize",
  "capabilities": [
    {"id": "memory-query", "confidence": 0.97}  // 覆盖父级
  ]
}
```

### 4.3 模型市场 (Model Marketplace)
Gateway 维护全局模型注册表。Agent 可以动态调用其他 Agent 的模型能力：

```json
POST /opc/v3/model/request
{
  "agent_id": "zhulong",
  "capability": "image-generation",
  "prompt": "生成一张 OPC 架构图",
  "preferred_model": "dall-e-3"
}
```

## 五、协议层实现

### 5.1 协议升级路径
```
v1.0 → 固定路由表 + 本地注册
v2.0 → 多线程 + SQLite + OpenClaw/Hermes bridge
v3.0 → 自描述能力 + 多模态 + 模型路由 + 进化
v4.0 → 跨集群联邦 + 分布式共识 + 能力交易市场
```

### 5.2 兼容性保证
- v2.0 Agent 可以通过适配器自动升级到 v3.0 协议
- v3.0 Gateway 向下兼容 v2.0 的注册格式
- `capabilities` 字段从 `string[]` 扩展为 `object[]` 时自动转换旧格式

### 5.3 最小实现
一个符合 OPC v3.0 的 Agent 只需要实现 3 个端点：
```
POST /opc/v3/agents/register    — 注册 + 自描述
POST /opc/v3/agents/heartbeat   — 保活
POST /opc/v3/tasks/callback     — 回调结果
```

再加 1 个可选的消费端点（或主动轮询）：
```
GET  /opc/v3/tasks/pending       — 拉取待处理任务
```

5 行代码的 Bash Agent 也能接入。不限语言、不限框架、不限模型。

## 六、Gateway v3 架构

```
┌─────────────────────────────────────────────────┐
│                  OPC Gateway v3                  │
│                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ Registry │  │ Capability │  │ Model Router │ │
│  │ (SQLite) │  │  Matrix    │  │ (cost/模态)  │ │
│  └──────────┘  └───────────┘  └──────────────┘ │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │         Event Bus (能力变更广播)           │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ REST API │  │   SSE     │  │  WebSocket   │ │
│  │  (HTTP)  │  │ (stream)  │  │ (实时双向)    │ │
│  └──────────┘  └───────────┘  └──────────────┘ │
└─────────────────────────────────────────────────┘
```

### 6.1 关键升级点 vs v2.0

| 维度 | v2.0 | v3.0 |
|------|------|------|
| 能力定义 | 硬编码 `CAPABILITY_MAP` | Agent 自描述，动态构建 |
| 多模态 | 不支持 | `input/output_modalities` |
| 模型感知 | 无 | 模型注册 + 模态路由 + 成本路由 |
| 能力变更 | 需重启 Gateway | Agent 热更新，广播通知 |
| 路由策略 | 固定 1:1 | 置信度排序 / 轮询 / 成本优先 |
| 流式输出 | 无 | SSE + WebSocket |
| 协议版本 | 单体 | 版本化 + 向后兼容 |
| 跨语言 | Python only | 协议优先，任何语言 |

这就是 OPC 该有的地基——不是写死的代码，而是一套活的协议。
*（内容由AI生成，仅供参考）*
