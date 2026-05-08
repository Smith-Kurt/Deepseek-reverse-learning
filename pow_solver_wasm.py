"""
DeepSeek API 学习项目 - POW 求解器
声明：本项目完全由 AI 生成，仅供个人学习研究使用，拒绝任何商业行为和非法行为。
使用 WASM 实现 DeepSeekHashV1 算法求解
"""

import os
import json
import struct
import urllib.request
from typing import Optional

# WASM 文件 URL
WASM_URL = "https://fe-static.deepseek.com/chat/static/sha3_wasm_bg.7b9ca65ddd.wasm"
WASM_FILE = os.path.join(os.path.dirname(__file__), "sha3_wasm.wasm")


def download_wasm():
    """下载 WASM 文件"""
    if not os.path.exists(WASM_FILE):
        print(f"Downloading WASM from {WASM_URL}...")
        urllib.request.urlretrieve(WASM_URL, WASM_FILE)
        print(f"Downloaded to {WASM_FILE}")


class WASMPOWSolver:
    """使用 WASM 求解 POW"""
    
    def __init__(self):
        self.engine = None
        self.store = None
        self.instance = None
        self.memory = None
        self._initialized = False
    
    def initialize(self):
        """初始化 WASM"""
        if self._initialized:
            return
        
        try:
            from wasmtime import Engine, Store, Module, Instance, Memory, MemoryType, Limits
        except ImportError:
            raise ImportError("Please install wasmtime: pip install wasmtime")
        
        # 下载 WASM 文件
        download_wasm()
        
        # 加载 WASM
        self.engine = Engine()
        self.store = Store(self.engine)
        
        # 读取 WASM 文件
        with open(WASM_FILE, 'rb') as f:
            wasm_bytes = f.read()
        
        # 编译和实例化
        module = Module(self.engine, wasm_bytes)
        
        # 创建导入
        # WASM 需要一些导入函数，我们需要提供它们
        # 但从代码来看，实际的求解函数不需要外部导入
        
        # 简单实例化（可能会失败，因为缺少导入）
        try:
            self.instance = Instance(self.store, module, [])
        except Exception as e:
            print(f"Instance creation failed: {e}")
            # 尝试提供空导入
            raise
        
        self._initialized = True
    
    def solve(self, challenge_data: dict) -> int:
        """求解 POW"""
        # 注意：这个实现可能不完整，因为 WASM 需要特定的导入
        raise NotImplementedError("WASM solver needs proper import handling")


def solve_pow_with_node(challenge_data: dict) -> dict:
    """
    使用 Node.js 求解 POW（推荐方法）
    
    Args:
        challenge_data: 挑战数据
    
    Returns:
        答案数据
    """
    import subprocess
    import tempfile
    
    # 创建 Node.js 脚本
    script = f"""
const fs = require('fs');
const https = require('https');

// 下载 WASM
const wasmUrl = '{WASM_URL}';
const wasmFile = '{WASM_FILE}';

async function downloadWasm() {{
  if (fs.existsSync(wasmFile)) return;
  
  return new Promise((resolve, reject) => {{
    const file = fs.createWriteStream(wasmFile);
    https.get(wasmUrl, (response) => {{
      response.pipe(file);
      file.on('finish', () => {{
        file.close();
        resolve();
      }});
    }}).on('error', reject);
  }});
}}

async function solve() {{
  await downloadWasm();
  
  const wasmBuffer = fs.readFileSync(wasmFile);
  const result = await WebAssembly.instantiate(wasmBuffer);
  const exports = result.instance.exports;
  const memory = exports.memory;
  
  const challenge = {json.dumps(challenge_data['challenge'])};
  const salt = {json.dumps(challenge_data['salt'])};
  const expireAt = {challenge_data['expire_at']};
  const difficulty = {challenge_data['difficulty']};
  
  const prefix = salt + '_' + expireAt + '_';
  const encoder = new TextEncoder();
  
  // 分配内存
  const challengeBytes = encoder.encode(challenge);
  const challengePtr = exports.__wbindgen_export_0(challengeBytes.length, 1);
  new Uint8Array(memory.buffer, challengePtr, challengeBytes.length).set(challengeBytes);
  
  const prefixBytes = encoder.encode(prefix);
  const prefixPtr = exports.__wbindgen_export_0(prefixBytes.length, 1);
  new Uint8Array(memory.buffer, prefixPtr, prefixBytes.length).set(prefixBytes);
  
  // 调用求解函数
  const resultPtr = exports.__wbindgen_add_to_stack_pointer(-16);
  exports.wasm_solve(resultPtr, challengePtr, challengeBytes.length, prefixPtr, prefixBytes.length, difficulty);
  
  // 读取结果
  const resultView = new DataView(memory.buffer);
  const found = resultView.getInt32(resultPtr + 0, true);
  const answer = resultView.getFloat64(resultPtr + 8, true);
  
  exports.__wbindgen_add_to_stack_pointer(16);
  
  if (found === 1) {{
    console.log(JSON.stringify({{ success: true, answer: Math.floor(answer) }}));
  }} else {{
    console.log(JSON.stringify({{ success: false, error: 'No solution found' }}));
  }}
}}

solve().catch(err => {{
  console.log(JSON.stringify({{ success: false, error: err.message }}));
}});
"""
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(script)
        script_file = f.name
    
    try:
        # 运行 Node.js
        result = subprocess.run(
            ['node', script_file],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            raise Exception(f"Node.js error: {result.stderr}")
        
        # 解析结果
        output = result.stdout.strip()
        data = json.loads(output)
        
        if not data.get("success"):
            raise Exception(f"POW solve failed: {data.get('error', 'unknown')}")
        
        return {
            "algorithm": challenge_data["algorithm"],
            "challenge": challenge_data["challenge"],
            "salt": challenge_data["salt"],
            "answer": data["answer"],
            "signature": challenge_data["signature"]
        }
    finally:
        os.unlink(script_file)


# 全局缓存
_cached_answer = None


def solve_pow(challenge_data: dict) -> dict:
    """
    求解 POW（带缓存）
    """
    global _cached_answer
    
    # 使用 Node.js 求解
    return solve_pow_with_node(challenge_data)


if __name__ == "__main__":
    import time
    
    test_challenge = {
        "algorithm": "DeepSeekHashV1",
        "challenge": "7e34e7b548e16f95b7aa3d929ca40205ec5e0e6a6f063ef3df48a03328ee0be7",
        "salt": "a65a2bfec31207fd4908",
        "difficulty": 144000,
        "signature": "0713e88f833f8dbd2281feba7be4ba0156af27f91ee8e3116ab37971d9fd07e9",
        "expire_at": 1778172270505,
        "expire_after": 300000
    }
    
    print("Testing WASM POW solver (via Node.js)...")
    start = time.time()
    result = solve_pow(test_challenge)
    elapsed = time.time() - start
    
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}s")
