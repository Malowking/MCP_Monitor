# API文档

## 基础信息

- 基础URL: `http://localhost:8000/api/v1`
- 所有请求和响应使用JSON格式
- 需要CORS支持

## 端点列表

### 1. 健康检查

**GET** `/health`

检查服务是否运行正常。

**响应**
```json
{
  "status": "healthy",
  "service": "MCP Monitor"
}
```

---

### 2. 处理查询

**POST** `/query`

处理用户查询，返回是否需要确认。

**请求体**
```json
{
  "user_id": "string",
  "question": "string",
  "context": [
    {
      "role": "user",
      "content": "string"
    }
  ]
}
```

**响应**
```json
{
  "request_id": "uuid",
  "requires_confirmation": true,
  "risk_score": 0.85,
  "tool_calls": [
    {
      "tool_call_id": "string",
      "tool_name": "delete_file",
      "tool_parameters": {"path": "/tmp/file.txt"},
      "requires_confirmation": true,
      "blocked": false,
      "risk_score": 0.85,
      "risk_level": "high",
      "confirmation_message": "详细的确认消息...",
      "risk_reasons": ["原因1", "原因2"],
      "historical_insights": ["历史信息1"],
      "similar_case_count": 3
    }
  ],
  "content": "模型生成的响应内容",
  "routing_info": {
    "detected_intents": ["file"],
    "active_domains": ["file"],
    "tool_count": 5
  }
}
```

---

### 3. 确认工具调用

**POST** `/confirm`

用户确认或拒绝工具调用。

**请求体**
```json
{
  "request_id": "uuid",
  "user_id": "string",
  "confirmed": true,
  "feedback": "这个操作是安全的"
}
```

**响应**
```json
{
  "success": true,
  "message": "工具调用已确认，可以执行",
  "action": "execute"
}
```

---

### 4. 记录执行结果

**POST** `/execution`

记录工具执行的结果。

**请求体**
```json
{
  "request_id": "uuid",
  "execution_success": true,
  "execution_result": {
    "deleted_files": 5,
    "message": "操作成功"
  }
}
```

**响应**
```json
{
  "success": true,
  "message": "Execution result recorded"
}
```

---

### 5. 注册MCP服务

**POST** `/services/register`

注册新的MCP服务。

**请求体**
```json
{
  "service_name": "file_operations",
  "service_url": "http://localhost:9000",
  "description": "文件操作服务",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "delete_file",
        "description": "删除文件",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {
              "type": "string",
              "description": "文件路径"
            }
          },
          "required": ["path"]
        }
      }
    }
  ],
  "layer": "L2",
  "domain": "file"
}
```

**响应**
```json
{
  "success": true,
  "message": "Service file_operations registered"
}
```

---

### 6. 列出所有服务

**GET** `/services/list?layer=L2&active_only=true`

列出MCP服务。

**查询参数**
- `layer`: 可选，筛选层级（L1/L2/L3）
- `active_only`: 是否只返回活跃服务，默认true

**响应**
```json
{
  "total": 3,
  "services": [
    {
      "service_name": "file_operations",
      "description": "文件操作服务",
      "layer": "L2",
      "domain": "file",
      "is_active": true,
      "health_status": "healthy",
      "circuit_breaker_state": "closed",
      "tool_count": 5,
      "tools": [...]
    }
  ]
}
```

---

### 7. 获取服务状态

**GET** `/services/{service_name}/status`

获取特定服务的详细状态。

**响应**
```json
{
  "service_name": "file_operations",
  "is_active": true,
  "health_status": "healthy",
  "circuit_breaker_state": "closed",
  "layer": "L2",
  "domain": "file",
  "tools": [...],
  "metrics": {
    "total_calls": 100,
    "success_calls": 95,
    "failed_calls": 5,
    "success_rate": 95.0,
    "avg_latency_ms": 120.5
  },
  "last_health_check": "2025-10-13T10:30:00"
}
```

---

### 8. 获取服务工具列表

**GET** `/services/{service_name}/tools`

获取服务提供的所有工具。

**响应**
```json
{
  "service_name": "file_operations",
  "tool_count": 5,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "delete_file",
        "description": "删除文件",
        "parameters": {...}
      }
    }
  ]
}
```

---

### 9. 获取用户历史

**GET** `/history/{user_id}?limit=50&tool_name=delete_file`

获取用户的工具调用历史。

**查询参数**
- `limit`: 返回记录数量，默认50
- `tool_name`: 可选，筛选特定工具

**响应**
```json
{
  "total": 10,
  "histories": [
    {
      "request_id": "uuid",
      "user_question": "帮我删除文件",
      "tool_name": "delete_file",
      "risk_score": 0.85,
      "user_confirmed": true,
      "execution_success": true,
      "created_at": "2025-10-13T10:00:00"
    }
  ]
}
```

---

## 错误响应

所有错误响应遵循以下格式：

```json
{
  "detail": "错误信息描述"
}
```

**HTTP状态码**
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

## 使用流程

1. **注册MCP服务**: 使用 `/services/register` 注册你的MCP服务
2. **发送查询**: 使用 `/query` 处理用户问题
3. **检查确认需求**: 如果 `requires_confirmation=true`，展示确认信息给用户
4. **用户确认**: 使用 `/confirm` 提交用户的确认决策
5. **执行工具**: 根据确认结果执行工具
6. **记录结果**: 使用 `/execution` 记录执行结果

## 完整示例

查看 `examples/usage_example.py` 了解完整的使用流程。
