# DeepSeek API 通信原理学习笔记

> **声明：本项目完全由 AI 生成，仅供个人学习研究使用，拒绝任何商业行为和非法行为。**

本文档记录了学习 DeepSeek 网页版 API 通信原理的过程，包括发现的问题和解决方案。

---

## 一、学习目标

通过分析 DeepSeek 网页版的网络请求，学习其 API 通信原理，并实现 OpenAI 兼容接口。

---

## 二、工具清单

| 工具 | 用途 |
|------|------|
| 浏览器开发者工具 | 捕获网络请求，分析 API 调用 |
| js-reverse-mcp | 辅助分析 JavaScript 代码 |
| Node.js | 运行 WASM 求解 POW |
| Python + FastAPI | 构建 API 服务 |

---

## 三、API 端点发现

通过浏览器开发者工具捕获网络请求，发现以下端点：

### 核心端点

| 功能 | 端点 | 方法 |
|------|------|------|
| 创建会话 | `/api/v0/chat_session/create` | POST |
| 发送消息 | `/api/v0/chat/completion` | POST (SSE) |
| 获取挑战 | `/api/v0/chat/create_pow_challenge` | POST |
| 上传文件 | `/api/v0/file/upload_file` | POST |
| 查询文件 | `/api/v0/file/fetch_files` | GET |

### 用户端点

| 功能 | 端点 | 方法 |
|------|------|------|
| 邮箱密码登录 | `/api/v0/users/login` | POST |
| 手机验证码登录 | `/api/v0/users/login_by_mobile_sms` | POST |

### 会话端点

| 功能 | 端点 | 方法 |
|------|------|------|
| 获取会话列表 | `/api/v0/chat_session/fetch_page` | GET |
| 删除会话 | `/api/v0/chat_session/delete` | POST |

---

## 四、请求头分析

### 必需请求头

```javascript
{
  "authorization": "Bearer {token}",
  "content-type": "application/json",
  "x-app-version": "20241129.1",
  "x-client-locale": "en_US",
  "x-client-platform": "web",
  "x-client-timezone-offset": "28800",
  "x-client-version": "2.0.0"
}
```

### 特殊请求头

| 头部 | 说明 |
|------|------|
| `X-DS-PoW-Response` | POW 答案（Base64 编码） |

---

## 五、防护机制分析

### 1. Token 认证

- 存储位置：`localStorage.userToken`
- 格式：一串字母数字字符串
- 有效期：未知（可能几小时到几天）

### 2. POW (Proof of Work)

**算法：** DeepSeekHashV1

**挑战数据：**
```json
{
  "algorithm": "DeepSeekHashV1",
  "challenge": "...",
  "salt": "...",
  "difficulty": 144000,
  "expire_at": 1778172270505
}
```

**求解过程：**
1. 构造前缀：`prefix = salt + "_" + expire_at + "_"`
2. 遍历 i 从 0 到 difficulty
3. 计算哈希：`hash = SHA3_WASM(prefix + str(i))`
4. 找到满足 `hash == challenge` 的 i

**请求头格式：**
```json
{
  "X-DS-PoW-Response": "Base64(JSON{algorithm, challenge, salt, answer, signature, target_path})"
}
```

### 3. 硬件签名

**结论：DeepSeek 没有硬件级签名（如 mtgsig）**

---

## 六、问题与解决方案

### 问题 1：POW 算法未知

**现象：** 发送消息需要先解决 POW 挑战。

**解决：**
- 搜索前端代码，找到 Worker 文件
- 使用 WASM 版本求解

### 问题 2：哈希算法不匹配

**现象：** Python 的 SHA3-256 与浏览器结果不同。

**原因：** DeepSeek 使用原始 Keccak-256，不是 NIST SHA3-256。

**解决：** 使用 Node.js 加载 WASM 文件求解。

### 问题 3：POW 头部格式错误

**现象：** 返回 `40300 MISSING_HEADER`。

**原因：** POW 头部需要 Base64 编码。

**解决：**
```python
import base64
import json

pow_json = json.dumps({...})
pow_header = base64.b64encode(pow_json.encode()).decode()
```

### 问题 4：SSE 响应格式不同

**现象：** 响应内容为空。

**原因：** DeepSeek 使用自定义 SSE 格式。

**解决：** 解析多种格式，提取 fragments 中的 content。

### 问题 5：上下文不生效

**现象：** 多轮对话时 AI 不记得历史。

**原因：** 代码只取最后一条消息。

**解决：** 处理整个 messages 数组，构建带上下文的 prompt。

### 问题 6：回复包含 "FINISHED"

**现象：** 回复末尾多出 "FINISHED"。

**原因：** finish 事件的内容被错误解析。

**解决：** 过滤状态文本。

### 问题 7：文件 ID 无效

**现象：** 返回 `invalid ref file id`。

**原因：** 文件需要等待解析完成。

**解决：** 轮询 `/api/v0/file/fetch_files` 等待 status 为 SUCCESS。

---

## 七、登录机制分析

### 邮箱密码登录

**端点：** `POST /api/v0/users/login`

**请求体：**
```json
{
  "email": "user@example.com",
  "mobile": "",
  "password": "password",
  "area_code": "",
  "device_id": "uuid",
  "os": "web"
}
```

**错误码：**
| biz_code | 说明 |
|----------|------|
| 0 | 成功 |
| 2 | 密码错误 |
| 10 | 账号被封禁 |

---

## 八、模型配置

### 模型类型

| 类型 | 说明 |
|------|------|
| `default` | 快速模式 |
| `expert` | 专家模式 |

### 功能开关

| 参数 | 说明 |
|------|------|
| `thinking_enabled` | 深度思考 |
| `search_enabled` | 智能搜索 |

---

## 九、文件上传流程

```
1. POST /api/v0/chat/create_pow_challenge
   - 获取文件上传的 POW 挑战

2. POST /api/v0/file/upload_file
   - 上传文件（multipart/form-data）
   - 返回 file_id

3. GET /api/v0/file/fetch_files?file_ids={file_id}
   - 轮询等待 status 为 SUCCESS

4. POST /api/v0/chat/completion
   - ref_file_ids: [file_id]
```

---

## 十、SSE 响应格式

### 事件类型

| 事件 | 说明 |
|------|------|
| `ready` | 就绪，包含 message_id |
| `delta` | 内容增量 |
| `finish` | 完成 |

### 数据格式

**格式1：简单字符串**
```json
{"v": "Hello"}
```

**格式2：完整响应**
```json
{
  "v": {
    "response": {
      "fragments": [
        {"type": "RESPONSE", "content": "Hello"}
      ]
    }
  }
}
```

**格式3：增量更新**
```json
{
  "p": "response/fragments/-1/content",
  "o": "APPEND",
  "v": "!"
}
```

---

## 十一、总结

DeepSeek 网页版的防护相对简单：
1. 只有 POW + Token，没有硬件签名
2. POW 使用 WASM 实现，可用 Node.js 调用
3. SSE 格式是自定义的，需要特殊解析
4. 文件上传需要等待解析完成

这些知识对于理解现代 Web 应用的 API 通信原理非常有帮助。
