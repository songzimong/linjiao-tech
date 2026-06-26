---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: d9bd63fb95daf4f45cedf90df782023d_9369a895715311f1897e5254002afed2
    ReservedCode1: A3W2Bax7HvtLe6GmYIGpPjnDjfKg9xaXcsOWvuLEN9/ekr4ghjOgFkX4alfWc30BMrTSitvEsHi/8vjrnsZQWOZbXZlYBW1zX8YcNZdnJlkg5eDi9TMk9bNVzUws9q89jqiRgnxXA1XGxHQuZKZL9dvClbW98vMGDVafF1HHSB7nU1+N+uHOLruwqpY=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: d9bd63fb95daf4f45cedf90df782023d_9369a895715311f1897e5254002afed2
    ReservedCode2: A3W2Bax7HvtLe6GmYIGpPjnDjfKg9xaXcsOWvuLEN9/ekr4ghjOgFkX4alfWc30BMrTSitvEsHi/8vjrnsZQWOZbXZlYBW1zX8YcNZdnJlkg5eDi9TMk9bNVzUws9q89jqiRgnxXA1XGxHQuZKZL9dvClbW98vMGDVafF1HHSB7nU1+N+uHOLruwqpY=
---

# 虾兵权限分级清单

> 版本: v2.0 | 生效: 2026-06-26 | 执行: 麒麟编排层

## 🟢 只读级 (READ_ONLY)

**工具白名单**: read_text, web_search, web_fetch, analyze_image, sessions_list, sessions_history

**虾兵列表**:

| 虾兵 | ID | 职责 |
|------|----|------|
| 白泽 | baize | 全体系记忆中枢 |
| 重明 | chongming | 系统监控/态势感知 |
| 谛听 | diting | 安全审查/内容检阅 |
| 毕方 | bifang | 信息搜索/情报整理 |
| 商羊 | shangyang | 信息搜集/舆情监测 |
| 金乌 | jinwu | 文件检索/数据查询 |

**熔断参数**: maxTurnCount=5, taskTimeout=120000

---

## 🟡 内容级 (CONTENT)

**工具白名单**: read_text, write_file, edit_file, web_search, web_fetch, analyze_image, sessions_list, sessions_history, sessions_spawn

**禁止工具**: shell_executor, python_executor（禁止直接执行代码/命令）

**虾兵列表**:

| 虾兵 | ID | 职责 |
|------|----|------|
| 青龙 | qinglong | 深度推理/方案设计 |
| 朱雀 | zhuque | 代码生成/技术文档 |
| 应龙 | yinglong | 内容创作/文案 |
| 饕餮 | taotie | 复杂任务编排 |
| 貔貅 | pixiu | 数据分析/报告 |
| 灵芝 | (lingzhi) | 知识整理/学习 |
| 鹊桥 | (queqiao) | 沟通协调/社交 |
| 离珠 | (lizhu) | 财务计算/数据处理 |
| 太史 | (taishi) | 文档管理/归档 |
| 净坛 | (jingtan) | 内容审核/清理 |
| 辟邪 | bixie | 风险分析/预警 |
| 龟甲 | (guijia) | 数据备份/版本管理 |

**熔断参数**: maxTurnCount=10, taskTimeout=240000

---

## 🔴 运维级 (OPS)

**工具白名单**: 全部工具可用

**特殊约束**: 
- 格式化/系统关键路径删除 → 必须麒麟二次确认
- 每次 shell_executor 调用后记录操作日志

**虾兵列表**:

| 虾兵 | ID | 职责 |
|------|----|------|
| 玄武 | xuanwu | 安全架构/防御策略 |
| 穷奇 | qiongqi | 攻击面分析/渗透测试 |
| 刑天 | (xingtian) | 系统运维/部署 |
| 鲲鹏 | (kunpeng) | 高性能计算/并行调度 |

**熔断参数**: maxTurnCount=15, taskTimeout=360000

---

## 执行规则

1. 麒麟在 `sessions_spawn` 时必须注入权限标识和熔断参数
2. 虾兵收到任务后，检查权限标识，严格遵守工具白名单
3. 越权操作由麒麟检测并强制回收
4. 熔断事件写入 `memory/bus/circuit-break-{timestamp}.md`
*（内容由AI生成，仅供参考）*
