# DeepSeek API 学习项目

> **声明：本项目完全由 AI 生成，仅供个人学习研究使用，拒绝任何商业行为和非法行为。使用本项目所产生的一切后果由使用者自行承担。**

学习 DeepSeek 网页版 API 通信原理，实现 OpenAI 兼容接口，支持 Cherry Studio 等客户端调用。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| ✅ POW 自动求解 | 使用 WASM 解决 DeepSeekHashV1 工作量证明 |
| ✅ 多模型支持 | 快速模式、专家模式 |
| ✅ 深度思考 | 支持 DeepThink 功能 |
| ✅ 智能搜索 | 支持联网搜索 |
| ✅ 多轮对话 | 自动处理上下文 |
| ✅ 文件上传 | 支持上传附件对话 |
| ✅ 流式响应 | SSE 流式输出 |
| ✅ 自动登录 | Token 或邮箱密码登录 |
| ✅ OpenAI 兼容 | 可直接对接 Cherry Studio 等客户端 |

---

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | 主要运行环境 |
| Node.js | 16+ | 用于 POW WASM 求解 |
| pip | 最新版 | Python 包管理器 |

### 安装环境

**macOS:**
```bash
brew install python
brew install node
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
```

**Windows:**
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/

---

## 快速开始

### 第一步：下载项目

```bash
git clone <repository_url>
cd deepseek-reverse
```

### 第二步：安装依赖

```bash
pip install -r requirements.txt
```

### 第三步：获取登录凭证（二选一）

#### 方式一：获取 Token

1. 打开浏览器，访问 https://chat.deepseek.com
2. 登录你的 DeepSeek 账号
3. 按 `F12` 打开开发者工具
4. 切换到 `Console`（控制台）标签
5. 输入以下代码并回车：

```javascript
JSON.parse(localStorage.getItem('userToken')).value
```

6. 复制返回的 Token 字符串

#### 方式二：使用邮箱密码

直接使用邮箱和密码登录，无需手动获取 Token。

### 第四步：配置登录信息

**方式一：创建配置文件（推荐）**

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
# 使用 Token
DEEPSEEK_TOKEN=你的Token

# 或使用邮箱密码
# DEEPSEEK_EMAIL=your_email@example.com
# DEEPSEEK_PASSWORD=your_password
```

**方式二：设置环境变量**

```bash
# Token 方式
export DEEPSEEK_TOKEN="你的Token"

# 或邮箱密码方式
export DEEPSEEK_EMAIL="your_email@example.com"
export DEEPSEEK_PASSWORD="your_password"
```

### 第五步：启动服务

```bash
./start.sh
```

或：

```bash
python3 server.py
```

### 第六步：开始使用

- **Cherry Studio** - 参见 [Cherry Studio 配置](#cherry-studio-配置)
- **代码调用** - 参见 [代码调用指南](#代码调用指南)
- **API 文档** - 访问 http://127.0.0.1:8000/docs

---

## Cherry Studio 配置

### 安装 Cherry Studio

下载地址：https://cherry-ai.com/

### 配置步骤

1. 打开 Cherry Studio，点击左下角齿轮图标 ⚙️ 进入设置
2. 点击左侧菜单 **模型服务商**
3. 点击 **添加** 按钮
4. 填写配置：

| 配置项 | 填写内容 |
|--------|----------|
| 供应商类型 | OpenAI |
| 名称 | DeepSeek Local |
| API 密钥 | 留空 |
| API 地址 | `http://127.0.0.1:8000/v1` |

5. 点击 **添加模型**，输入模型名称：

| 模型名称 | 说明 |
|----------|------|
| `deepseek-chat` | 快速模式（日常对话） |
| `deepseek-expert` | 专家模式（复杂问题） |
| `deepseek-chat-think` | 快速 + 深度思考 |
| `deepseek-chat-search` | 快速 + 智能搜索 |

6. 点击 **测试** 按钮验证连接
7. 点击 **保存**

---

## 代码调用指南

### 使用封装的客户端

```python
from client import DeepSeekClient

# 初始化（Token 方式）
client = DeepSeekClient(token="your_token")

# 或邮箱密码方式
# client = DeepSeekClient(email="your_email", password="your_password")

# 创建会话
session = client.create_session()

# 发送消息
result = client.chat("你好", session["id"])
print(result["response"])
```

### 多轮对话

```python
session = client.create_session()
session_id = session["id"]

# 第一轮
client.chat("我的名字是 Alice", session_id)

# 第二轮（自动携带上下文）
result = client.chat("我的名字是什么？", session_id)
print(result["response"])  # 会回答 "Alice"
```

### 使用不同模型

```python
# 专家模式 + 深度思考
result = client.chat(
    "请详细解释量子计算",
    session_id,
    model_type="expert",
    thinking_enabled=True
)

# 快速模式 + 智能搜索
result = client.chat(
    "今天的最新新闻是什么？",
    session_id,
    search_enabled=True
)
```

### 上传附件

```python
# 上传文件并等待解析
file_id = client.upload_and_prepare_file("path/to/file.txt")

# 发送带附件的消息
result = client.chat(
    "请分析这个文件的内容",
    session["id"],
    file_ids=[file_id]
)
```

---

## 模型列表

格式：`deepseek-{模式}-{功能}`

| 模型 ID | 模式 | 功能 |
|---------|------|------|
| `deepseek-chat` | 快速 | 无 |
| `deepseek-chat-think` | 快速 | 深度思考 |
| `deepseek-chat-search` | 快速 | 智能搜索 |
| `deepseek-chat-think-search` | 快速 | 深度思考 + 智能搜索 |
| `deepseek-expert` | 专家 | 无 |
| `deepseek-expert-think` | 专家 | 深度思考 |
| `deepseek-expert-search` | 专家 | 智能搜索 |
| `deepseek-expert-think-search` | 专家 | 深度思考 + 智能搜索 |

---

## 文件结构

```
deepseek-reverse/
├── README.md                 # 本文档
├── QUICKSTART.md             # 快速开始指南
├── REVERSE_ENGINEERING.md    # API 通信原理学习笔记
├── CHERRY_STUDIO.md          # Cherry Studio 配置指南
│
├── requirements.txt          # Python 依赖
├── .env.example              # 配置文件模板
├── .gitignore                # Git 忽略文件
├── start.sh                  # 启动脚本
│
├── server.py                 # OpenAI 兼容 API 服务
├── client.py                 # Python 客户端
├── pow_solver_wasm.py        # POW 求解器
├── test_client.py            # 测试脚本
│
└── sha3_wasm.wasm            # WASM 文件
```

---

## 常见问题

### Q: Token 失效怎么办？

**A:** Token 会过期，重新获取：
1. 打开 https://chat.deepseek.com
2. 登录后 F12 打开控制台
3. 执行：`JSON.parse(localStorage.getItem('userToken')).value`
4. 复制新 Token 更新配置

或使用邮箱密码方式，自动获取 Token。

### Q: Cherry Studio 连接失败？

**A:** 检查：
1. 服务是否已启动
2. API 地址是否正确（`http://127.0.0.1:8000/v1`）
3. 端口 8000 是否被占用

### Q: 如何使用邮箱密码登录？

**A:** 在 `.env` 文件中配置：
```
DEEPSEEK_EMAIL=your_email@example.com
DEEPSEEK_PASSWORD=your_password
```

---

## 技术原理

### POW (Proof of Work) 机制

DeepSeek 使用 DeepSeekHashV1 算法进行工作量证明，使用 WASM 实现。

### SSE (Server-Sent Events) 响应

DeepSeek 使用 SSE 流式返回响应内容。

### 请求流程

```
客户端                    DeepSeek 服务端
  │                           │
  ├─ POST /chat_session/create ──>  创建会话
  ├─ POST /create_pow_challenge ─>  获取 POW 挑战
  ├─ [计算 POW 答案]          │
  ├─ POST /chat/completion ────>  发送消息
  <─── SSE 流式响应 ───────────┘
```

---

## 相关学习资源

- [DeepSeek 官网](https://chat.deepseek.com)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Cherry Studio](https://cherry-ai.com/)

---

## 特别声明

> **本项目完全由 AI 生成，仅供个人学习研究使用，拒绝任何商业行为和非法行为。**

本仓库发布的程序代码及其中涉及的任何解锁和解密分析脚本，仅用于测试和学习研究，禁止用于商业用途，不能保证其合法性，准确性，完整性和有效性，请根据情况自行判断。

本项目内所有资源文件，禁止任何公众号、自媒体进行任何形式的转载、发布。

本人对任何脚本/代码/访问资源问题概不负责，包括但不限于由任何脚本错误导致的任何损失或损害。

间接使用脚本/代码/访问资源的任何用户，包括但不限于建立VPS或在某些行为违反国家/地区法律或相关法规的情况下进行传播, 本人对于由此引起的任何隐私泄漏或其他后果概不负责。

请勿将本仓库的任何内容用于商业或非法目的，否则后果自负。

如果任何单位或个人认为该项目的脚本/代码/访问资源可能涉嫌侵犯其权利，则应及时通知并提供身份证明，所有权证明，我们将在收到认证文件后删除相关脚本。

任何以任何方式查看此项目的人或直接或间接使用该项目的任何脚本的使用者都应仔细阅读此声明。本人保留随时更改或补充此免责声明的权利。一旦使用并复制了任何相关脚本或Script项目的规则，则视为您已接受此免责声明。

您必须在下载后的24小时内从计算机或手机中完全删除以上内容。

您使用或者复制了本仓库且本人制作的任何脚本/代码，则视为 **已接受** 此声明，请仔细阅读！

---

## 许可证

MIT License - 仅供学习研究使用
