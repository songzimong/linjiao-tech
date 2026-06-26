# 麒麟体系 · Agent 协作协议 (Hermes Fusion)

> 版本：v1.0 | 日期：2026-06-22

## 一、消息传递规范

### 1.1 消息格式
所有 Agent 间通信使用统一消息格式：

```json
{
  "from": "<agent_id>",
  "to": "<agent_id>",
  "type": "task|query|result|alert|sync",
  "priority": "low|normal|high|urgent",
  "subject": "<简短标题>",
  "body": "<详细内容>",
  "context_refs": ["<相关记忆文件路径>"],
  "timestamp": "<ISO-8601>",
  "requires_response": true/false,
  "deadline": "<可选截止时间>"
}
```

### 1.2 传递方式
- **麒麟 → Agent**: `sessions_spawn` (一次性任务) / `sessions_send` (持续对话)
- **Agent → 麒麟**: 返回结果，麒麟汇总
- **Agent ↔ Agent**: 通过麒麟中转（星型拓扑），或 `sessions_send` 直接通信

## 二、任务协作模式

### 2.1 串行模式 (Sequential)
```
麒麟 → Agent A → 麒麟 → Agent B → 麒麟 → 用户
```
适用：有依赖关系的任务，B 需要 A 的输出

### 2.2 并行模式 (Parallel)
```
麒麟 → [Agent A, Agent B, Agent C] → 麒麟汇总 → 用户
```
适用：独立任务，可同时执行

### 2.3 管道模式 (Pipeline)
```
麒麟 → Agent A → Agent B → Agent C → 麒麟 → 用户
```
适用：数据处理流水线，Agent 间直接传递

## 三、共享记忆总线协议

### 3.1 读写规则
- 所有 Agent 可**读** `memory/bus/` 下的文件
- 只有麒麟可**写** `agent-status.json`
- 白泽可**写** `decisions.json`
- 玄武可**写** `audit-log.json`（新增）

### 3.2 上下文同步
每次任务完成后，执行任务的 Agent 必须：
1. 更新 `bus/agent-status.json` 中的负载状态
2. 将关键结果写入对应殿堂的记忆文件
3. 向白泽发送同步信号（通过麒麟）

## 四、冲突解决

### 4.1 优先级
urgent > high > normal > low

### 4.2 资源竞争
- 同一时刻一个 Agent 只能有一个 high/urgent 任务
- 多个 Agent 争抢同一资源时，麒麟按优先级调度
- 超过 30 分钟无响应的任务，麒麟重新路由

## 五、健康检查

### 5.1 心跳机制
- 麒麟每 30 分钟检查一次 Agent 状态
- Agent 超过 2 小时无活动，标记为 idle
- Agent 连续失败 3 次，标记为 degraded
