# 快速开始指南

5 分钟快速上手 DeepSeek Reverse API。

---

## 前置条件

确保已安装：
- Python 3.9+
- Node.js 16+

检查版本：
```bash
python3 --version
node --version
```

---

## 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

---

## 步骤 2: 获取 Token（必须）

### 方法一：浏览器获取（推荐）

1. 打开 https://chat.deepseek.com 并登录
2. 按 `F12` 打开开发者工具
3. 切换到 `Console` 标签
4. 输入以下代码并回车：

```javascript
JSON.parse(localStorage.getItem('userToken')).value
```

5. 复制返回的字符串（一长串字母数字）

### 方法二：使用邮箱密码登录

如果你不想手动获取 Token，可以使用邮箱密码自动登录（见下方配置）。

---

## 步骤 3: 配置登录信息

### 方式 A: 使用 Token

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 Token：

```
DEEPSEEK_TOKEN=粘贴你获取的Token
```

### 方式 B: 使用邮箱密码

编辑 `.env`，填入邮箱和密码：

```
DEEPSEEK_EMAIL=your_email@example.com
DEEPSEEK_PASSWORD=your_password
```

---

## 步骤 4: 启动服务

```bash
./start.sh
```

或：

```bash
python3 server.py
```

看到以下输出表示启动成功：

```
============================================================
  DeepSeek Reverse API Server
============================================================
  服务地址: http://0.0.0.0:8000
  API 文档: http://0.0.0.0:8000/docs
============================================================
```

---

## 步骤 5: 使用

### 方式 A: Cherry Studio

1. 打开 Cherry Studio
2. 设置 → 模型服务商 → 添加
3. 选择 OpenAI，填写：
   - API 地址: `http://127.0.0.1:8000/v1`
   - API 密钥: 留空
4. 添加模型: `deepseek-chat`
5. 保存，开始对话

### 方式 B: Python 代码

```python
from client import DeepSeekClient

# 使用 Token
client = DeepSeekClient(token="你的Token")

# 或使用邮箱密码
# client = DeepSeekClient(email="your_email", password="your_password")

session = client.create_session()

result = client.chat("你好", session["id"])
print(result["response"])
```

### 方式 C: curl 测试

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

---

## 常用模型

| 模型 | 说明 |
|------|------|
| `deepseek-chat` | 快速模式 |
| `deepseek-expert` | 专家模式 |
| `deepseek-chat-think` | 快速 + 深度思考 |
| `deepseek-chat-search` | 快速 + 智能搜索 |

---

## 遇到问题？

1. **Token 失效**: 重新获取 Token
2. **连接失败**: 检查服务是否启动，端口是否正确
3. **依赖缺失**: 运行 `pip install -r requirements.txt`

详细文档请查看 [README.md](./README.md)
