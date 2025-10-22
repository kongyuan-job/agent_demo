# Agent可观测性系统

## 概述

本系统提供了一个完整的Agent可观测性解决方案，替代LangSmith平台，实现Agent执行过程的监控、日志记录和性能分析。

## 功能特性

### 🔍 实时监控
- Agent执行次数统计
- 成功率/失败率监控
- 平均执行时间追踪
- 实时性能指标展示

### 📊 数据存储
- SQLite数据库存储执行记录
- 结构化数据存储（JSON格式）
- 自动索引优化查询性能
- 数据持久化保存

### 📈 可视化仪表板
- 总体概览统计
- Agent性能对比图表
- 执行历史记录查看
- 详细执行信息展示

### 📋 日志记录
- 结构化日志记录
- 错误信息详细记录
- 执行元数据保存
- 日志文件轮转

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent执行     │───►│  可观测性管理器  │───►│  SQLite数据库   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   日志文件      │
                       │                 │
                       └─────────────────┘
```

## 核心组件

### 1. ObservabilityManager
负责管理所有的可观测性功能：
- 数据库操作
- 指标计算
- 日志记录
- 数据导出

### 2. AgentExecution
记录单次Agent执行的详细信息：
- 执行ID、Agent ID
- 输入输出数据
- 执行时间和状态
- 错误信息和元数据

### 3. AgentMetrics
统计Agent的性能指标：
- 执行次数统计
- 成功率计算
- 平均执行时间
- 错误率分析

## API接口

### 获取Agent指标
```
GET /api/observability/metrics?agent_id={agent_id}
```

### 获取执行历史
```
GET /api/observability/history?agent_id={agent_id}&limit={limit}
```

### 导出数据
```
GET /api/observability/export?agent_id={agent_id}&format=json
```

### 仪表板数据
```
GET /api/observability/dashboard
```

## 使用方法

### 1. 自动记录
系统会自动记录所有Agent的执行过程，无需手动配置。

### 2. 手动记录
```python
from observability import log_agent_execution

execution_id = log_agent_execution(
    agent_id="your_agent_id",
    user_input="用户输入",
    response="Agent响应",
    execution_time=0.5,
    success=True,
    metadata={"custom_field": "value"}
)
```

### 3. 查看仪表板
访问 `/static/observability.html` 查看可视化仪表板。

### 4. 数据导出
```python
from observability import observability_manager

# 导出特定Agent数据
data = observability_manager.export_data("agent_id", "json")

# 导出所有数据
data = observability_manager.export_data(format="json")
```

## 数据库结构

### agent_executions 表
```sql
CREATE TABLE agent_executions (
    execution_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    user_input TEXT,
    response TEXT,
    input_type TEXT,
    output_type TEXT,
    execution_time REAL,
    timestamp TEXT,
    metadata TEXT,
    success BOOLEAN,
    error_message TEXT
);
```

### agent_metrics 表
```sql
CREATE TABLE agent_metrics (
    agent_id TEXT PRIMARY KEY,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    avg_execution_time REAL DEFAULT 0,
    total_execution_time REAL DEFAULT 0,
    last_execution TEXT,
    error_rate REAL DEFAULT 0
);
```

## 配置选项

### 环境变量
- `OBSERVABILITY_DB_PATH`: 数据库文件路径
- `LOG_LEVEL`: 日志级别

### 数据库配置
- 默认使用SQLite数据库
- 支持自定义数据库路径
- 自动创建表和索引

## 性能优化

### 1. 数据库优化
- 自动创建索引
- 批量插入优化
- 查询性能优化

### 2. 内存管理
- 限制历史记录数量
- 定期清理过期数据
- 高效的数据结构

### 3. 异步处理
- 异步数据库操作
- 非阻塞日志记录
- 并发安全设计

## 监控指标

### 基础指标
- 总执行次数
- 成功执行次数
- 失败执行次数
- 平均执行时间

### 高级指标
- 成功率百分比
- 错误率百分比
- 执行时间分布
- 输入输出类型统计

## 错误处理

### 1. 数据库错误
- 连接失败自动重试
- 事务回滚机制
- 错误日志记录

### 2. 记录错误
- 记录失败不影响主流程
- 错误信息详细记录
- 异常堆栈跟踪

## 扩展功能

### 1. 自定义指标
可以添加自定义的性能指标：
```python
metadata = {
    "custom_metric": "value",
    "business_metric": 123
}
```

### 2. 数据导出格式
支持多种导出格式：
- JSON格式
- CSV格式（可扩展）
- 自定义格式

### 3. 告警机制
可以集成告警系统：
- 错误率告警
- 性能下降告警
- 异常执行告警

## 最佳实践

### 1. 数据管理
- 定期备份数据库
- 清理过期数据
- 监控存储空间

### 2. 性能监控
- 关注执行时间趋势
- 监控错误率变化
- 分析使用模式

### 3. 故障排查
- 查看详细执行记录
- 分析错误日志
- 对比历史性能

## 总结

本可观测性系统提供了完整的Agent监控解决方案，无需依赖外部平台，实现了：
- ✅ 完整的执行记录
- ✅ 实时性能监控
- ✅ 可视化仪表板
- ✅ 数据导出功能
- ✅ 生产环境就绪

适合在生产环境中替代LangSmith，提供更好的控制和定制能力。
