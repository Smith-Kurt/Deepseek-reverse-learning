"""
DeepSeek API 学习项目 - API Server
声明：本项目完全由 AI 生成，仅供个人学习研究使用，拒绝任何商业行为和非法行为。
OpenAI 兼容格式，支持 Cherry Studio 等客户端
"""

import os
import json
import time
import uuid
import asyncio
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tempfile
import os

from client import DeepSeekClient


# ============== 配置 ==============

# 从环境变量读取配置
DEEPSEEK_TOKEN = os.getenv("DEEPSEEK_TOKEN", "")
DEEPSEEK_EMAIL = os.getenv("DEEPSEEK_EMAIL", "")
DEEPSEEK_PASSWORD = os.getenv("DEEPSEEK_PASSWORD", "")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
API_KEY = os.getenv("API_KEY", "")  # 可选：保护你的服务

# 全局客户端实例
client: Optional[DeepSeekClient] = None


# ============== 工具函数 ==============

def get_client() -> DeepSeekClient:
    """获取或创建客户端实例"""
    global client
    if client is None:
        if DEEPSEEK_TOKEN:
            # 使用 token
            client = DeepSeekClient(token=DEEPSEEK_TOKEN)
        elif DEEPSEEK_EMAIL and DEEPSEEK_PASSWORD:
            # 使用邮箱密码登录
            client = DeepSeekClient(email=DEEPSEEK_EMAIL, password=DEEPSEEK_PASSWORD)
        else:
            raise HTTPException(
                status_code=500,
                detail="Please set DEEPSEEK_TOKEN or DEEPSEEK_EMAIL+DEEPSEEK_PASSWORD"
            )
    return client


def verify_api_key(request: Request):
    """验证 API Key（如果配置了的话）"""
    if not API_KEY:
        return True
    
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        return token == API_KEY
    
    return False


def model_name_to_type(model: str) -> tuple:
    """
    将模型名称转换为 DeepSeek 模型类型和功能配置
    
    支持的模型格式：
    - deepseek-chat: 快速模式
    - deepseek-expert: 专家模式
    - deepseek-chat-think: 快速模式 + 深度思考
    - deepseek-chat-search: 快速模式 + 智能搜索
    - deepseek-chat-think-search: 快速模式 + 深度思考 + 智能搜索
    - deepseek-expert-think: 专家模式 + 深度思考
    - deepseek-expert-search: 专家模式 + 智能搜索
    - deepseek-expert-think-search: 专家模式 + 深度思考 + 智能搜索
    
    Returns:
        (model_type, thinking_enabled, search_enabled, display_name)
    """
    model = model.lower().strip()
    
    # 解析模型类型
    if "expert" in model:
        model_type = "expert"
    else:
        model_type = "default"
    
    # 解析功能
    thinking_enabled = "think" in model or "r1" in model
    search_enabled = "search" in model
    
    # 构建显示名称
    base_name = "Expert" if model_type == "expert" else "Chat"
    features = []
    if thinking_enabled:
        features.append("Think")
    if search_enabled:
        features.append("Search")
    
    display_name = f"DeepSeek {base_name}"
    if features:
        display_name += f" ({'+'.join(features)})"
    
    return model_type, thinking_enabled, search_enabled, display_name


# ============== 数据模型 ==============

class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = "deepseek-chat"
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Any] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "deepseek"

class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelInfo]


def build_prompt_with_context(messages: List[ChatMessage]) -> str:
    """
    将消息列表构建为带上下文的 prompt
    
    Cherry Studio 会发送包含历史记录的消息列表，格式如：
    [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮你的？"},
        {"role": "user", "content": "1+1等于几？"}
    ]
    
    我们需要将其转换为 DeepSeek 能理解的格式
    """
    if not messages:
        return ""
    
    # 如果只有一条消息，直接返回
    if len(messages) == 1:
        return messages[0].content
    
    # 多条消息时，构建带上下文的 prompt
    # 方案：将历史对话格式化为上下文
    context_parts = []
    current_prompt = ""
    
    for i, msg in enumerate(messages):
        if msg.role == "system":
            # 系统消息作为上下文前缀
            context_parts.append(f"[System: {msg.content}]")
        elif msg.role == "user":
            if i == len(messages) - 1:
                # 最后一条用户消息作为当前 prompt
                current_prompt = msg.content
            else:
                context_parts.append(f"[User: {msg.content}]")
        elif msg.role == "assistant":
            context_parts.append(f"[Assistant: {msg.content}]")
    
    # 如果有上下文，将其与当前 prompt 组合
    if context_parts:
        context = "\n".join(context_parts)
        return f"""Previous conversation:
{context}

Current question: {current_prompt}"""
    
    return current_prompt


def generate_chat_completion(
    request: ChatCompletionRequest,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """生成聊天补全响应（非流式）"""
    client = get_client()
    
    # 构建带上下文的 prompt
    prompt = build_prompt_with_context(request.messages)
    
    if not prompt:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # 获取模型类型和功能配置
    model_type, thinking_enabled, search_enabled, model_display = model_name_to_type(request.model)
    
    # 调用 DeepSeek API
    result = client.chat(
        prompt=prompt,
        session_id=session_id,
        model_type=model_type,
        thinking_enabled=thinking_enabled,
        search_enabled=search_enabled,
        verbose=False
    )
    
    # 构建 OpenAI 格式响应
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["response"]
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


async def generate_chat_completion_stream(
    request: ChatCompletionRequest,
    session_id: Optional[str] = None
):
    """生成聊天补全响应（流式）"""
    client = get_client()
    
    # 构建带上下文的 prompt
    prompt = build_prompt_with_context(request.messages)
    
    if not prompt:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # 获取模型类型和功能配置
    model_type, thinking_enabled, search_enabled, model_display = model_name_to_type(request.model)
    
    # 发送开始事件
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': request.model, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': ''}, 'finish_reason': None}]})}\n\n"
    
    # 流式调用 DeepSeek API
    try:
        for event in client.send_message(
            session_id=session_id or "",
            prompt=prompt,
            model_type=model_type,
            thinking_enabled=thinking_enabled,
            search_enabled=search_enabled
        ):
            event_type = event.get("event")
            data = event.get("data", {})
            
            # 从事件中提取内容
            content = event.get("content", "")
            
            if content:
                chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": content},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
            
            elif event_type == "finish":
                break
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    # 发送结束事件
    yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': request.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
    yield "data: [DONE]\n\n"


# ============== FastAPI 应用 ==============

app = FastAPI(
    title="DeepSeek API Server",
    description="OpenAI 兼容的 DeepSeek API 服务",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "DeepSeek API Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "models": "/v1/models",
            "chat": "/v1/chat/completions"
        }
    }


@app.get("/v1/models")
async def list_models():
    """获取可用模型列表"""
    return {
        "object": "list",
        "data": [
            # 快速模式
            {
                "id": "deepseek-chat",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            {
                "id": "deepseek-chat-think",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            {
                "id": "deepseek-chat-search",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            {
                "id": "deepseek-chat-think-search",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            # 专家模式
            {
                "id": "deepseek-expert",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            {
                "id": "deepseek-expert-think",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            {
                "id": "deepseek-expert-search",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            {
                "id": "deepseek-expert-think-search",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
            # 兼容旧名称
            {
                "id": "deepseek-r1",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            },
        ]
    }


@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest, req: Request):
    """创建聊天补全"""
    # 验证 API Key
    if not verify_api_key(req):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # 获取客户端
    client = get_client()
    
    try:
        # 创建会话
        session = client.create_session()
        session_id = session["id"]
        
        if request.stream:
            # 流式响应
            return StreamingResponse(
                generate_chat_completion_stream(request, session_id),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            result = generate_chat_completion(request, session_id)
            return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions")
async def create_completion(request: Request):
    """兼容旧版 completions 端点"""
    body = await request.json()
    
    # 转换为 chat completion 格式
    prompt = body.get("prompt", "")
    messages = [{"role": "user", "content": prompt}]
    
    chat_request = ChatCompletionRequest(
        model=body.get("model", "deepseek-chat"),
        messages=[ChatMessage(**msg) for msg in messages],
        stream=body.get("stream", False)
    )
    
    return await create_chat_completion(chat_request, request)


@app.post("/v1/files/upload")
async def upload_file(file: UploadFile = File(...), req: Request = None):
    """
    上传文件到 DeepSeek
    
    Returns:
        文件信息，包含 id, file_name 等
    """
    if not verify_api_key(req):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    client = get_client()
    
    try:
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # 上传到 DeepSeek
        result = client.upload_file(tmp_path)
        
        # 删除临时文件
        os.unlink(tmp_path)
        
        return {
            "id": result.get("id"),
            "file_name": result.get("file_name"),
            "status": result.get("status"),
            "token_usage": result.get("token_usage")
        }
    except Exception as e:
        # 确保删除临时文件
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))


# ============== 启动 ==============

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              DeepSeek API Server v1.0.0                      ║
╠══════════════════════════════════════════════════════════════╣
║  Server: http://{SERVER_HOST}:{SERVER_PORT}                            ║
║  API Docs: http://{SERVER_HOST}:{SERVER_PORT}/docs                       ║
╠══════════════════════════════════════════════════════════════╣
║  Cherry Studio 配置:                                         ║
║  - API Base URL: http://127.0.0.1:{SERVER_PORT}/v1                      ║
║  - API Key: {API_KEY or '(留空)'}                                ║
║  - Model: deepseek-chat                                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
