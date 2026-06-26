# 知识沉淀系统 (Knowledge Archive)

> 群星体系 v1.0 | 2026-06-22

## 沉淀流程

蜂群结束后，自动执行知识沉淀：

```
蜂群结束
  ↓
1. 提取最优方案 → 写入对应殿堂
  ↓
2. 记录失败方案及原因 → 写入经验教训
  ↓
3. 提炼涌现模式 → 转化为可复用规则
  ↓
4. 更新 Agent 信任度 → 调整后续权重
  ↓
5. 生成蜂群报告 → 写入白泽记忆
```

## 沉淀数据结构

### 最优方案
```json
{
  "type": "solution",
  "topic": "议题",
  "solution": "最优方案内容",
  "agents_involved": ["AgentA", "AgentB"],
  "confidence": 0.95,
  "timestamp": "2026-06-22T13:00:00+08:00",
  "storage_location": "技术殿/蜂群方案/2026-06-22-topic.md"
}
```

### 失败方案
```json
{
  "type": "lesson",
  "topic": "议题",
  "failed_approach": "方案内容",
  "failure_reason": "为什么不行",
  "severity": "low|medium|high",
  "timestamp": "2026-06-22T13:00:00+08:00"
}
```

### 涌现模式
```json
{
  "type": "pattern",
  "description": "新发现的协作模式",
  "applicability": "适用场景",
  "agents_discovered": ["AgentA", "AgentB"],
  "confidence": 0.8,
  "reuse_rule": "未来遇到类似议题时直接应用此规则"
}
```

## 信任度更新

蜂群结束后，根据贡献质量更新 Agent 的信任度：

```
trust_delta = quality_score × participation_ratio

quality_score: 方案被采纳的质量评分 (0-10)
participation_ratio: 参与轮次 / 总轮次
```

连续 3 次高质量输出 → 信任度 +0.1
连续 3 次低质量输出 → 信任度 -0.1
单次重大失误 → 信任度 -0.3

## 可复用规则库

```json
{
  "rules": [
    {
      "id": "RULE-001",
      "trigger": "当遇到 X 类型议题",
      "action": "直接使用 Y 方案（来自蜂群涌现）",
      "confidence": 0.9,
      "last_validated": "2026-06-22"
    }
  ]
}
```

## 存储位置

所有沉淀数据写入：
- 最优方案 → 对应殿堂/蜂群方案/
- 失败教训 → 经验教训/
- 涌现模式 → 蜂群模式/
- 信任度更新 → profiles/agent-index.json
