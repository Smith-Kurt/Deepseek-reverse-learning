"""
DeepSeek API 学习项目 - Python 客户端
声明：本项目完全由 AI 生成，仅供个人学习研究使用，拒绝任何商业行为和非法行为。
"""

import json
import time
import uuid
import base64
import requests
from typing import Generator, Optional, List, Dict
from pow_solver_wasm import solve_pow


class DeepSeekClient:
    """DeepSeek Web API 客户端"""
    
    BASE_URL = "https://chat.deepseek.com/api/v0"
    
    def __init__(self, token: str = None, email: str = None, password: str = None, device_id: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            token: 直接提供的 auth token
            email: 邮箱（用于自动登录）
            password: 密码（用于自动登录）
            device_id: 设备 ID
        """
        self.device_id = device_id or str(uuid.uuid4())
        self.token = None
        self.session = requests.Session()
        self._setup_base_headers()
        
        # 如果提供了 token，直接使用
        if token:
            self.token = token
            self.session.headers.update({"authorization": f"Bearer {token}"})
        # 如果提供了邮箱和密码，自动登录获取 token
        elif email and password:
            self.token = self._login_with_password(email, password)
            self.session.headers.update({"authorization": f"Bearer {self.token}"})
        else:
            raise ValueError("Must provide either token or email+password")
    
    def _setup_base_headers(self):
        """设置基础请求头"""
        self.session.headers.update({
            "content-type": "application/json",
            "x-app-version": "20241129.1",
            "x-client-locale": "en_US",
            "x-client-platform": "web",
            "x-client-timezone-offset": "28800",
            "x-client-version": "2.0.0",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        })
    
    def _login_with_password(self, email: str, password: str) -> str:
        """
        使用邮箱密码登录获取 token
        
        Args:
            email: 邮箱地址
            password: 密码
        
        Returns:
            auth token
        """
        # 判断是邮箱还是手机号
        is_email = "@" in email
        
        login_data = {
            "email": email if is_email else "",
            "mobile": "" if is_email else email,
            "password": password,
            "area_code": "" if is_email else "+86",
            "device_id": self.device_id,
            "os": "web"
        }
        
        # 登录请求不需要 authorization header
        headers = {"authorization": ""}
        
        resp = self.session.post(
            f"{self.BASE_URL}/users/login",
            json=login_data,
            headers=headers
        )
        
        data = resp.json()
        
        # 检查登录结果
        biz_code = data.get("data", {}).get("biz_code")
        
        if biz_code == 0:
            # 登录成功
            user = data.get("data", {}).get("biz_data", {}).get("user", {})
            token = user.get("token")
            if token:
                return token
            else:
                raise Exception("Login succeeded but no token returned")
        elif biz_code == 2:
            raise Exception("Wrong email/password")
        elif biz_code == 10:
            raise Exception("Account is banned")
        else:
            biz_msg = data.get("data", {}).get("biz_msg", "Unknown error")
            raise Exception(f"Login failed: {biz_msg}")
    
    def _check_response(self, resp: requests.Response) -> dict:
        """检查响应，处理常见错误"""
        data = resp.json()
        
        # 检查 HTTP 状态码
        if resp.status_code == 401:
            raise Exception("Token expired or invalid. Please refresh your token.")
        
        # 检查业务错误码
        code = data.get("code")
        if code != 0:
            biz_code = data.get("data", {}).get("biz_code")
            biz_msg = data.get("data", {}).get("biz_msg", "")
            
            if biz_code == 40002:
                raise Exception("Missing token")
            elif biz_code == 40003:
                raise Exception("Invalid token")
            elif biz_code == 40300:
                raise Exception("POW header error")
            elif biz_code == 40301:
                raise Exception("Invalid POW response")
            elif biz_code == 50006:
                raise Exception("User is muted (rate limited)")
            else:
                raise Exception(f"API error: code={code}, biz_code={biz_code}, msg={biz_msg}")
        
        return data
    
    def create_session(self) -> dict:
        """
        创建新的对话会话
        
        Returns:
            会话信息，包含 id, seq_id, model_type 等
        """
        resp = self.session.post(f"{self.BASE_URL}/chat_session/create", json={})
        data = self._check_response(resp)
        return data["data"]["biz_data"]["chat_session"]
    
    def get_pow_challenge(self, target_path: str) -> dict:
        """
        获取 POW 挑战
        
        Args:
            target_path: 目标 API 路径
        
        Returns:
            挑战数据，包含 algorithm, challenge, salt, difficulty, expire_at, signature
        """
        resp = self.session.post(f"{self.BASE_URL}/chat/create_pow_challenge", json={
            "target_path": target_path
        })
        data = self._check_response(resp)
        return data["data"]["biz_data"]["challenge"]
    
    def upload_file(self, file_path: str) -> dict:
        """
        上传文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件信息，包含 id, file_name, status 等
        """
        import os
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 获取 POW 挑战（文件上传也需要 POW）
        challenge_data = self.get_pow_challenge("/api/v0/file/upload_file")
        
        # 求解 POW
        pow_result = solve_pow(challenge_data)
        pow_json = json.dumps({
            "algorithm": pow_result["algorithm"],
            "challenge": pow_result["challenge"],
            "salt": pow_result["salt"],
            "answer": pow_result["answer"],
            "signature": pow_result["signature"],
            "target_path": "/api/v0/file/upload_file"
        })
        pow_response = base64.b64encode(pow_json.encode()).decode()
        
        # 上传文件
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            
            # 需要临时移除 Content-Type header，让 requests 自动设置 multipart/form-data
            original_content_type = self.session.headers.get('Content-Type')
            self.session.headers.pop('Content-Type', None)
            
            headers = {
                'X-DS-PoW-Response': pow_response
            }
            
            try:
                resp = self.session.post(
                    f"{self.BASE_URL}/file/upload_file",
                    files=files,
                    headers=headers
                )
            finally:
                # 恢复 Content-Type
                if original_content_type:
                    self.session.headers['Content-Type'] = original_content_type
        
        data = resp.json()
        
        # 检查响应
        if data.get("code") != 0:
            biz_msg = data.get("data", {}).get("biz_msg", "Upload failed")
            raise Exception(f"File upload failed: {biz_msg}")
        
        return data["data"]["biz_data"]
    
    def fork_file(self, file_id: str, model_type: str = "default") -> dict:
        """
        将文件关联到当前会话（fork 文件任务）
        
        Args:
            file_id: 文件 ID
            model_type: 模型类型
        
        Returns:
            文件信息
        """
        resp = self.session.post(f"{self.BASE_URL}/file/fork_file_task", json={
            "file_id": file_id,
            "to_model_type": model_type
        })
        
        data = resp.json()
        
        if data.get("code") != 0:
            biz_code = data.get("data", {}).get("biz_code")
            biz_msg = data.get("data", {}).get("biz_msg", "Fork file failed")
            raise Exception(f"Fork file failed: {biz_msg} (code: {biz_code})")
        
        return data["data"]["biz_data"]
    
    def upload_and_prepare_file(self, file_path: str, model_type: str = "default", wait_for_parse: bool = True, timeout: int = 60) -> str:
        """
        上传文件并准备使用（上传 + 等待解析）
        
        Args:
            file_path: 文件路径
            model_type: 模型类型
            wait_for_parse: 是否等待文件解析完成
            timeout: 等待超时时间（秒）
        
        Returns:
            可以在 send_message 中使用的文件 ID
        """
        # 1. 上传文件
        file_info = self.upload_file(file_path)
        file_id = file_info["id"]
        status = file_info.get("status", "PENDING")
        
        # 2. 如果需要等待解析完成
        if wait_for_parse and status != "SUCCESS":
            import time
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 检查文件状态
                try:
                    file_status = self.get_file_status(file_id)
                    status = file_status.get("status", "PENDING")
                    
                    if status == "SUCCESS":
                        # 解析成功，返回文件 ID
                        return file_id
                    elif status in ("FAILED", "ERROR"):
                        raise Exception(f"File parse failed: {status}")
                    
                    # 等待一秒后重试
                    time.sleep(1)
                except Exception as e:
                    if "File parse failed" in str(e):
                        raise
                    # 其他错误继续等待
                    time.sleep(1)
            
            raise Exception(f"File parse timeout after {timeout} seconds")
        
        return file_id
    
    def get_file_status(self, file_id: str) -> dict:
        """
        获取文件状态
        
        Args:
            file_id: 文件 ID
        
        Returns:
            文件状态信息
        """
        resp = self.session.get(
            f"{self.BASE_URL}/file/fetch_files",
            params={"file_ids": file_id}
        )
        
        data = resp.json()
        
        if data.get("code") != 0:
            raise Exception(f"Get file status failed: {data}")
        
        files = data.get("data", {}).get("biz_data", {}).get("files", [])
        if files:
            return files[0]
        
        return {"status": "UNKNOWN"}
    
    def send_message(
        self, 
        session_id: str, 
        prompt: str, 
        parent_message_id: Optional[str] = None,
        model_type: str = "default",
        thinking_enabled: bool = False,
        search_enabled: bool = True,
        file_ids: List[str] = None
    ) -> Generator[dict, None, None]:
        """
        发送消息并获取流式响应
        
        Args:
            session_id: 会话ID
            prompt: 用户消息
            parent_message_id: 父消息ID（多轮对话）
            model_type: 模型类型 (default/expert)
            thinking_enabled: 是否启用深度思考
            search_enabled: 是否启用搜索
            file_ids: 文件 ID 列表（可选）
        
        Yields:
            事件字典，包含 event 和 data
        """
        # 1. 获取 POW 挑战
        challenge_data = self.get_pow_challenge("/api/v0/chat/completion")
        
        # 2. 解决 POW 并构建请求头
        pow_result = solve_pow(challenge_data)
        pow_json = json.dumps({
            "algorithm": pow_result["algorithm"],
            "challenge": pow_result["challenge"],
            "salt": pow_result["salt"],
            "answer": pow_result["answer"],
            "signature": pow_result["signature"],
            "target_path": "/api/v0/chat/completion"
        })
        # Base64 编码
        pow_response = base64.b64encode(pow_json.encode()).decode()
        pow_headers = {"X-DS-PoW-Response": pow_response}
        
        # 3. 构建请求体
        request_body = {
            "chat_session_id": session_id,
            "parent_message_id": parent_message_id,
            "model_type": model_type,
            "prompt": prompt,
            "ref_file_ids": file_ids or [],
            "thinking_enabled": thinking_enabled,
            "search_enabled": search_enabled,
            "preempt": False
        }
        
        # 4. 发送请求
        resp = self.session.post(
            f"{self.BASE_URL}/chat/completion",
            json=request_body,
            headers=pow_headers,
            stream=True
        )
        
        # 检查响应状态
        if resp.status_code != 200:
            print(f"[ERROR] Status: {resp.status_code}, Response: {resp.text[:500]}")
            return
        
        # 检查是否是 JSON 错误响应
        content_type = resp.headers.get('content-type', '')
        if 'application/json' in content_type:
            try:
                error_data = resp.json()
                if error_data.get('code') != 0:
                    print(f"[ERROR] API Error: {error_data}")
                    return
            except:
                pass
        
        # 5. 解析 SSE 流
        message_id = None
        current_event = None
        is_thinking = False
        is_searching = False
        
        for line in resp.iter_lines():
            if not line:
                continue
            
            line_str = line.decode('utf-8')
            
            # 解析 event 行
            if line_str.startswith('event: '):
                current_event = line_str[7:].strip()
                continue
            
            # 解析 data 行
            if line_str.startswith('data: '):
                data_str = line_str[6:]
                
                if data_str == '[DONE]':
                    break
                
                try:
                    data = json.loads(data_str)
                    
                    # 构造统一的事件格式
                    event_data = {
                        "event": current_event,
                        "data": data
                    }
                    
                    # 提取 message_id
                    if current_event == "ready":
                        msg_id = data.get("response_message_id")
                        if msg_id:
                            message_id = str(msg_id)
                    
                    # 提取内容 - 处理 DeepSeek 的多种格式
                    content = None
                    
                    # 格式1: 完整响应结构 {"v": {"response": {"fragments": [...]}}}
                    if isinstance(data.get("v"), dict):
                        response = data.get("v", {}).get("response", {})
                        fragments = response.get("fragments", [])
                        for frag in fragments:
                            frag_type = frag.get("type", "")
                            frag_content = frag.get("content")
                            
                            if frag_type == "THINK":
                                is_thinking = True
                                is_searching = False
                            elif frag_type == "SEARCH":
                                is_searching = True
                                is_thinking = False
                            elif frag_type == "RESPONSE":
                                is_thinking = False
                                is_searching = False
                            
                            if frag_type == "RESPONSE" and frag_content and isinstance(frag_content, str):
                                content = frag_content
                    
                    # 格式5: BATCH 操作 {"p": "response", "o": "BATCH", "v": [...]}
                    elif data.get("o") == "BATCH" and isinstance(data.get("v"), list):
                        for sub_op in data.get("v", []):
                            sub_p = sub_op.get("p", "")
                            sub_o = sub_op.get("o", "")
                            sub_v = sub_op.get("v")
                            
                            if sub_o == "APPEND" and "fragment" in sub_p.lower():
                                if isinstance(sub_v, list) and sub_v:
                                    frag = sub_v[0]
                                    frag_type = frag.get("type", "")
                                    frag_content = frag.get("content")
                                    
                                    if frag_type == "THINK":
                                        is_thinking = True
                                        is_searching = False
                                    elif frag_type == "SEARCH":
                                        is_searching = True
                                        is_thinking = False
                                    elif frag_type == "RESPONSE":
                                        is_thinking = False
                                        is_searching = False
                                        if frag_content and isinstance(frag_content, str):
                                            content = frag_content
                    
                    # 格式2: 简单字符串增量 {"v": "Hello"}
                    elif isinstance(data.get("v"), str):
                        if not is_thinking and not is_searching:
                            content = data["v"]
                    
                    # 格式3: 新 fragment 开始 {"p": "response/fragments", "o": "APPEND", "v": [...]}
                    elif data.get("p") == "response/fragments" and data.get("o") == "APPEND":
                        new_frags = data.get("v", [])
                        if isinstance(new_frags, list) and new_frags:
                            frag = new_frags[0]
                            frag_type = frag.get("type", "")
                            frag_content = frag.get("content")
                            
                            if frag_type == "THINK":
                                is_thinking = True
                                is_searching = False
                            elif frag_type == "SEARCH":
                                is_searching = True
                                is_thinking = False
                            elif frag_type == "RESPONSE":
                                is_thinking = False
                                is_searching = False
                                if frag_content and isinstance(frag_content, str):
                                    content = frag_content
                    
                    # 格式4: 增量更新 {"p": "...", "o": "APPEND", "v": "!"}
                    elif data.get("o") == "APPEND" and isinstance(data.get("v"), str):
                        path = data.get("p", "")
                        path_upper = path.upper()
                        
                        if "THINK" in path_upper:
                            is_thinking = True
                            is_searching = False
                        elif "SEARCH" in path_upper:
                            is_searching = True
                            is_thinking = False
                        elif "RESPONSE" in path_upper:
                            is_thinking = False
                            is_searching = False
                        
                        if not is_thinking and not is_searching:
                            content = data["v"]
                    
                    # 过滤掉状态文本
                    if content and isinstance(content, str) and content not in ("FINISHED", "STOP", "END"):
                        event_data["content"] = content
                    
                    yield event_data
                    
                    # 更新 current_event
                    current_event = None
                    
                except json.JSONDecodeError:
                    continue
        
        # 返回 message_id 供后续使用
        return message_id
    
    def chat(
        self, 
        prompt: str, 
        session_id: Optional[str] = None,
        parent_message_id: Optional[str] = None,
        model_type: str = "default",
        thinking_enabled: bool = False,
        search_enabled: bool = True,
        file_ids: List[str] = None,
        verbose: bool = True
    ) -> dict:
        """
        完整对话接口
        
        Args:
            prompt: 用户消息
            session_id: 会话ID（可选）
            parent_message_id: 父消息ID（多轮对话）
            model_type: 模型类型
            thinking_enabled: 深度思考
            search_enabled: 搜索
            file_ids: 文件 ID 列表（可选）
            verbose: 是否打印响应
        
        Returns:
            包含 session_id, message_id, response, events 的字典
        """
        if not session_id:
            session = self.create_session()
            session_id = session["id"]
        
        response_parts = []
        events = []
        message_id = None
        
        for event in self.send_message(
            session_id=session_id,
            prompt=prompt,
            parent_message_id=parent_message_id,
            model_type=model_type,
            thinking_enabled=thinking_enabled,
            search_enabled=search_enabled,
            file_ids=file_ids
        ):
            events.append(event)
            event_type = event.get("event")
            data = event.get("data", {})
            
            # 从事件中提取内容
            content = event.get("content", "")
            
            if content:
                response_parts.append(content)
                if verbose:
                    print(content, end="", flush=True)
            
            elif event_type == "ready":
                message_id = data.get("response_message_id")
            
            elif event_type == "finish":
                break
            
            elif event_type == "hint":
                raise Exception(f"Server hint: {data.get('content', 'Unknown error')}")
        
        if verbose:
            print()  # 换行
        
        return {
            "session_id": session_id,
            "message_id": message_id,
            "response": "".join(response_parts),
            "events": events
        }
    
    def multi_turn_chat(
        self, 
        messages: List[str], 
        session_id: Optional[str] = None,
        model_type: str = "default"
    ) -> List[dict]:
        """
        多轮对话接口
        
        Args:
            messages: 消息列表
            session_id: 会话ID（可选）
            model_type: 模型类型
        
        Returns:
            响应列表
        """
        if not session_id:
            session = self.create_session()
            session_id = session["id"]
        
        results = []
        parent_message_id = None
        
        for i, msg in enumerate(messages):
            print(f"\n[Round {i+1}]")
            print(f"User: {msg}")
            print("Assistant: ", end="")
            
            result = self.chat(
                prompt=msg,
                session_id=session_id,
                parent_message_id=parent_message_id,
                model_type=model_type,
                verbose=True
            )
            
            # 更新 parent_message_id 用于下一轮
            parent_message_id = result.get("message_id")
            results.append(result)
        
        return results
    
    def get_chat_sessions(self) -> List[dict]:
        """获取会话列表"""
        resp = self.session.get(f"{self.BASE_URL}/chat_session/fetch_page", params={
            "lte_cursor.pinned": "false"
        })
        data = self._check_response(resp)
        return data["data"]["biz_data"]["chat_sessions"]
    
    def get_history_messages(self, session_id: str) -> List[dict]:
        """获取历史消息"""
        resp = self.session.get(f"{self.BASE_URL}/chat/history_messages", params={
            "chat_session_id": session_id
        })
        data = self._check_response(resp)
        return data["data"]["biz_data"]["messages"]
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        resp = self.session.post(f"{self.BASE_URL}/chat_session/delete", json={
            "chat_session_id": session_id
        })
        data = self._check_response(resp)
        return True
    
    def get_settings(self, scope: str = "main") -> dict:
        """获取客户端设置"""
        resp = self.session.get(f"{self.BASE_URL}/client/settings", params={
            "did": self.device_id,
            "scope": scope
        })
        data = self._check_response(resp)
        return data["data"]["biz_data"]["settings"]
