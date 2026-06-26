# 蜂群模式调度器 (Swarm Scheduler)

> 群星体系 v1.0 | 2026-06-22

## 调度器职责

麒麟在收到任务时，自动判断使用哪种调度模式。

## 模式选择逻辑

```
收到任务
  ↓
评估任务复杂度 (1-4)
  ↓
评估任务类型
  ↓
选择调度模式
```

### 复杂度评估

| 复杂度 | 特征 | 模式 |
|--------|------|------|
| 1 - 简单 | 单一目标、明确需求、独立任务 | 常规模式 |
| 2 - 中等 | 多步骤、有一定依赖 | 常规模式 或 混合模式 |
| 3 - 复杂 | 多方案可选、需要创意、跨域 | 蜂群模式 |
| 4 - 极复杂 | 战略级决策、高风险、多维度 | 递归蜂群 |

### 类型分类

- **执行类**: 写代码、部署、运维 → 常规模式
- **创意类**: 方案设计、头脑风暴 → 蜂群模式
- **决策类**: 战略选择、风险评估 → 混合/递归蜂群
- **分析类**: 市场调研、竞品分析 → 常规或蜂群（视复杂度）

## 蜂群执行流程

```python
def dispatch_swarm(topic, complexity):
    # 1. 选择 Agent 池
    agents = select_agents_by_topic(topic, complexity)
    
    # 2. 初始化蜂群
    swarm = init_swarm(
        topic=topic,
        agents=agents,
        max_rounds=get_max_rounds(complexity),
        timeout=get_timeout(complexity)
    )
    
    # 3. 启动蜂群对话
    results = run_swarm(swarm)
    
    # 4. 质量加权投票
    winner = weighted_vote(results)
    
    # 5. 安全审查
    xuanwu_audit(winner)
    
    # 6. 知识沉淀
    archive_swarm(swarm, winner)
    
    # 7. 返回结果
    return winner
```

## Agent 选择算法

```
select_agents_by_topic(topic, complexity):
    1. 从 agent-index.json 查找 capabilities 匹配的 Agent
    2. 从 agent-status.json 过滤掉 load > 3 的 Agent
    3. 按 skill_level 降序排列
    4. 取前 N 个 (N 由复杂度决定)
    5. 冷启动 Agent 权重减半
```

## 超时与终止

- 达到 max_rounds 自动终止
- 达到 timeout 时间自动终止
- 玄武检测到安全问题立即终止
- 达成共识提前终止
