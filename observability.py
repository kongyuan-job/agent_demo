#!/usr/bin/env python3
"""
可观测性模块 - 替代LangSmith的Agent监控和日志记录系统
"""

import json
import time
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

@dataclass
class AgentExecution:
    """Agent执行记录"""
    execution_id: str
    agent_id: str
    user_input: Any
    response: Any
    input_type: str
    output_type: str
    execution_time: float
    timestamp: str
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

@dataclass
class ToolCall:
    """工具调用记录"""
    call_id: str
    execution_id: str
    agent_id: str
    tool_name: str
    tool_type: str
    input_params: Dict[str, Any]
    output: str
    call_time: float
    timestamp: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class LLMCall:
    """LLM调用记录"""
    call_id: str
    execution_id: str
    agent_id: str
    model: str
    messages: List[Dict[str, str]]
    response: str
    tokens_used: Optional[int]
    call_time: float
    timestamp: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class AgentMetrics:
    """Agent性能指标"""
    agent_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_time: float
    total_execution_time: float
    last_execution: Optional[str]
    error_rate: float

class ObservabilityManager:
    """可观测性管理器"""
    
    def __init__(self, db_path: str = "agent_observability.db"):
        self.db_path = db_path
        self.setup_database()
        self.setup_logging()
    
    def setup_database(self):
        """设置数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建执行记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_executions (
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
            )
        ''')
        
        # 创建指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_metrics (
                agent_id TEXT PRIMARY KEY,
                total_executions INTEGER DEFAULT 0,
                successful_executions INTEGER DEFAULT 0,
                failed_executions INTEGER DEFAULT 0,
                avg_execution_time REAL DEFAULT 0,
                total_execution_time REAL DEFAULT 0,
                last_execution TEXT,
                error_rate REAL DEFAULT 0
            )
        ''')
        
        # 创建工具调用记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_calls (
                call_id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                tool_name TEXT,
                tool_type TEXT,
                input_params TEXT,
                output TEXT,
                call_time REAL,
                timestamp TEXT,
                success BOOLEAN,
                error_message TEXT,
                FOREIGN KEY (execution_id) REFERENCES agent_executions(execution_id)
            )
        ''')
        
        # 创建LLM调用记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_calls (
                call_id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                model TEXT,
                messages TEXT,
                response TEXT,
                tokens_used INTEGER,
                call_time REAL,
                timestamp TEXT,
                success BOOLEAN,
                error_message TEXT,
                FOREIGN KEY (execution_id) REFERENCES agent_executions(execution_id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id ON agent_executions(agent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_executions_timestamp ON agent_executions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_calls_execution_id ON tool_calls(execution_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_calls_agent_id ON tool_calls(agent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_calls_execution_id ON llm_calls(execution_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_calls_agent_id ON llm_calls(agent_id)')
        
        conn.commit()
        conn.close()
    
    def setup_logging(self):
        """设置日志记录"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'agent_observability.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('AgentObservability')
    
    def log_execution(self, execution: AgentExecution):
        """记录Agent执行"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO agent_executions 
                (execution_id, agent_id, user_input, response, input_type, output_type, 
                 execution_time, timestamp, metadata, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution.execution_id,
                execution.agent_id,
                json.dumps(execution.user_input, ensure_ascii=False),
                json.dumps(execution.response, ensure_ascii=False),
                execution.input_type,
                execution.output_type,
                execution.execution_time,
                execution.timestamp,
                json.dumps(execution.metadata, ensure_ascii=False),
                execution.success,
                execution.error_message
            ))
            
            conn.commit()
            conn.close()
            
            # 更新指标
            self._update_metrics(execution)
            
            # 记录日志
            self.logger.info(f"Agent {execution.agent_id} executed in {execution.execution_time:.3f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to log execution: {e}")
    
    def log_tool_call(self, tool_call: ToolCall):
        """记录工具调用"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tool_calls
                (call_id, execution_id, agent_id, tool_name, tool_type, input_params,
                 output, call_time, timestamp, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tool_call.call_id,
                tool_call.execution_id,
                tool_call.agent_id,
                tool_call.tool_name,
                tool_call.tool_type,
                json.dumps(tool_call.input_params, ensure_ascii=False),
                tool_call.output,
                tool_call.call_time,
                tool_call.timestamp,
                tool_call.success,
                tool_call.error_message
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Tool {tool_call.tool_name} called in {tool_call.call_time:.3f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to log tool call: {e}")
    
    def log_llm_call(self, llm_call: LLMCall):
        """记录LLM调用"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO llm_calls
                (call_id, execution_id, agent_id, model, messages, response,
                 tokens_used, call_time, timestamp, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                llm_call.call_id,
                llm_call.execution_id,
                llm_call.agent_id,
                llm_call.model,
                json.dumps(llm_call.messages, ensure_ascii=False),
                llm_call.response,
                llm_call.tokens_used,
                llm_call.call_time,
                llm_call.timestamp,
                llm_call.success,
                llm_call.error_message
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"LLM {llm_call.model} called in {llm_call.call_time:.3f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to log LLM call: {e}")
    
    def _update_metrics(self, execution: AgentExecution):
        """更新Agent指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前指标
        cursor.execute('SELECT * FROM agent_metrics WHERE agent_id = ?', (execution.agent_id,))
        row = cursor.fetchone()
        
        if row:
            # 更新现有指标
            total_executions = row[1] + 1
            successful_executions = row[2] + (1 if execution.success else 0)
            failed_executions = row[3] + (0 if execution.success else 1)
            total_execution_time = row[5] + execution.execution_time
            avg_execution_time = total_execution_time / total_executions
            error_rate = failed_executions / total_executions
            
            cursor.execute('''
                UPDATE agent_metrics SET
                total_executions = ?, successful_executions = ?, failed_executions = ?,
                avg_execution_time = ?, total_execution_time = ?, last_execution = ?, error_rate = ?
                WHERE agent_id = ?
            ''', (total_executions, successful_executions, failed_executions,
                  avg_execution_time, total_execution_time, execution.timestamp, error_rate,
                  execution.agent_id))
        else:
            # 创建新指标
            success_count = 1 if execution.success else 0
            failed_count = 0 if execution.success else 1
            error_rate = failed_count / 1
            
            cursor.execute('''
                INSERT INTO agent_metrics 
                (agent_id, total_executions, successful_executions, failed_executions,
                 avg_execution_time, total_execution_time, last_execution, error_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (execution.agent_id, 1, success_count, failed_count,
                  execution.execution_time, execution.execution_time, execution.timestamp, error_rate))
        
        conn.commit()
        conn.close()
    
    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """获取Agent指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM agent_metrics WHERE agent_id = ?', (agent_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return AgentMetrics(
                agent_id=row[0],
                total_executions=row[1],
                successful_executions=row[2],
                failed_executions=row[3],
                avg_execution_time=row[4],
                total_execution_time=row[5],
                last_execution=row[6],
                error_rate=row[7]
            )
        return None
    
    def get_execution_history(self, agent_id: str, limit: int = 100) -> List[AgentExecution]:
        """获取执行历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM agent_executions 
            WHERE agent_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (agent_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        executions = []
        for row in rows:
            executions.append(AgentExecution(
                execution_id=row[0],
                agent_id=row[1],
                user_input=json.loads(row[2]) if row[2] else None,
                response=json.loads(row[3]) if row[3] else None,
                input_type=row[4],
                output_type=row[5],
                execution_time=row[6],
                timestamp=row[7],
                metadata=json.loads(row[8]) if row[8] else {},
                success=bool(row[9]),
                error_message=row[10]
            ))
        
        return executions
    
    def get_tool_calls(self, execution_id: str) -> List[ToolCall]:
        """获取执行过程中的工具调用"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tool_calls
            WHERE execution_id = ?
            ORDER BY timestamp ASC
        ''', (execution_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        tool_calls = []
        for row in rows:
            tool_calls.append(ToolCall(
                call_id=row[0],
                execution_id=row[1],
                agent_id=row[2],
                tool_name=row[3],
                tool_type=row[4],
                input_params=json.loads(row[5]) if row[5] else {},
                output=row[6],
                call_time=row[7],
                timestamp=row[8],
                success=bool(row[9]),
                error_message=row[10]
            ))
        
        return tool_calls
    
    def get_llm_calls(self, execution_id: str) -> List[LLMCall]:
        """获取执行过程中的LLM调用"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM llm_calls
            WHERE execution_id = ?
            ORDER BY timestamp ASC
        ''', (execution_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        llm_calls = []
        for row in rows:
            llm_calls.append(LLMCall(
                call_id=row[0],
                execution_id=row[1],
                agent_id=row[2],
                model=row[3],
                messages=json.loads(row[4]) if row[4] else [],
                response=row[5],
                tokens_used=row[6],
                call_time=row[7],
                timestamp=row[8],
                success=bool(row[9]),
                error_message=row[10]
            ))
        
        return llm_calls
    
    def get_all_metrics(self) -> List[AgentMetrics]:
        """获取所有Agent指标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM agent_metrics ORDER BY total_executions DESC')
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            metrics.append(AgentMetrics(
                agent_id=row[0],
                total_executions=row[1],
                successful_executions=row[2],
                failed_executions=row[3],
                avg_execution_time=row[4],
                total_execution_time=row[5],
                last_execution=row[6],
                error_rate=row[7]
            ))
        
        return metrics
    
    def export_data(self, agent_id: Optional[str] = None, format: str = "json") -> str:
        """导出数据"""
        if agent_id:
            executions = self.get_execution_history(agent_id)
            metrics = [self.get_agent_metrics(agent_id)]
        else:
            executions = []
            metrics = self.get_all_metrics()
            # 获取所有执行记录
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agent_executions ORDER BY timestamp DESC LIMIT 1000')
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                executions.append(AgentExecution(
                    execution_id=row[0],
                    agent_id=row[1],
                    user_input=json.loads(row[2]) if row[2] else None,
                    response=json.loads(row[3]) if row[3] else None,
                    input_type=row[4],
                    output_type=row[5],
                    execution_time=row[6],
                    timestamp=row[7],
                    metadata=json.loads(row[8]) if row[8] else {},
                    success=bool(row[9]),
                    error_message=row[10]
                ))
        
        data = {
            "metrics": [asdict(m) for m in metrics if m],
            "executions": [asdict(e) for e in executions],
            "export_time": datetime.now().isoformat()
        }
        
        if format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            # 可以扩展其他格式，如CSV
            return json.dumps(data, ensure_ascii=False, indent=2)

# 全局可观测性管理器实例
observability_manager = ObservabilityManager()

def log_agent_execution(agent_id: str, user_input: Any, response: Any, 
                       execution_time: float, success: bool = True, 
                       error_message: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None):
    """记录Agent执行的便捷函数"""
    execution = AgentExecution(
        execution_id=str(uuid.uuid4()),
        agent_id=agent_id,
        user_input=user_input,
        response=response,
        input_type=type(user_input).__name__,
        output_type=type(response).__name__,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        metadata=metadata or {},
        success=success,
        error_message=error_message
    )
    
    observability_manager.log_execution(execution)
    return execution.execution_id

def log_tool_call(execution_id: str, agent_id: str, tool_name: str, tool_type: str,
                  input_params: Dict[str, Any], output: str, call_time: float,
                  success: bool = True, error_message: Optional[str] = None) -> str:
    """记录工具调用的便捷函数"""
    tool_call = ToolCall(
        call_id=str(uuid.uuid4()),
        execution_id=execution_id,
        agent_id=agent_id,
        tool_name=tool_name,
        tool_type=tool_type,
        input_params=input_params,
        output=output,
        call_time=call_time,
        timestamp=datetime.now().isoformat(),
        success=success,
        error_message=error_message
    )
    
    observability_manager.log_tool_call(tool_call)
    return tool_call.call_id

def log_llm_call(execution_id: str, agent_id: str, model: str,
                 messages: List[Dict[str, str]], response: str, call_time: float,
                 tokens_used: Optional[int] = None, success: bool = True,
                 error_message: Optional[str] = None) -> str:
    """记录LLM调用的便捷函数"""
    llm_call = LLMCall(
        call_id=str(uuid.uuid4()),
        execution_id=execution_id,
        agent_id=agent_id,
        model=model,
        messages=messages,
        response=response,
        tokens_used=tokens_used,
        call_time=call_time,
        timestamp=datetime.now().isoformat(),
        success=success,
        error_message=error_message
    )
    
    observability_manager.log_llm_call(llm_call)
    return llm_call.call_id
