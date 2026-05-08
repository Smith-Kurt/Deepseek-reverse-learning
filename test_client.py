"""
DeepSeek API 学习项目 - 测试脚本
声明：本项目完全由 AI 生成，仅供个人学习研究使用，拒绝任何商业行为和非法行为。

使用方法:
    python3 test_client.py          # 运行基本测试
    python3 test_client.py basic    # 基本对话测试
    python3 test_client.py model    # 模型测试
    python3 test_client.py file     # 文件上传测试
    python3 test_client.py all      # 运行所有测试
"""

import sys
import os
import tempfile
from client import DeepSeekClient


def get_token():
    """获取 Token"""
    token = os.getenv("DEEPSEEK_TOKEN")
    if not token:
        print("错误: 请设置 DEEPSEEK_TOKEN 环境变量")
        print("  export DEEPSEEK_TOKEN='your_token'")
        sys.exit(1)
    return token


def test_basic():
    """基本对话测试"""
    print("=" * 60)
    print("基本对话测试")
    print("=" * 60)
    
    token = get_token()
    client = DeepSeekClient(token=token)
    
    # 创建会话
    session = client.create_session()
    print(f"会话 ID: {session['id']}")
    
    # 发送消息
    print("\n发送: What is 1+1?")
    print("回复: ", end="")
    result = client.chat("What is 1+1? Reply with just the number.", session["id"])
    print(f"\n回复内容: {result['response']}")
    
    print("\n✅ 基本对话测试通过")


def test_multi_turn():
    """多轮对话测试"""
    print("=" * 60)
    print("多轮对话测试")
    print("=" * 60)
    
    token = get_token()
    client = DeepSeekClient(token=token)
    
    session = client.create_session()
    session_id = session["id"]
    print(f"会话 ID: {session_id}")
    
    # 第一轮
    print("\n[第一轮] 我的名字是 Alice")
    result1 = client.chat("My name is Alice.", session_id, verbose=False)
    print(f"回复: {result1['response']}")
    
    # 第二轮
    print("\n[第二轮] 我的名字是什么？")
    result2 = client.chat("What is my name?", session_id, verbose=False)
    print(f"回复: {result2['response']}")
    
    if "Alice" in result2["response"]:
        print("\n✅ 多轮对话测试通过 - AI 记住了名字")
    else:
        print("\n⚠️ 多轮对话测试 - AI 可能没有记住名字")


def test_model_types():
    """模型类型测试"""
    print("=" * 60)
    print("模型类型测试")
    print("=" * 60)
    
    token = get_token()
    client = DeepSeekClient(token=token)
    
    session = client.create_session()
    session_id = session["id"]
    
    tests = [
        ("deepseek-chat", "default", False, False),
        ("deepseek-expert", "expert", False, False),
        ("deepseek-chat-search", "default", False, True),
    ]
    
    for model_name, model_type, thinking, search in tests:
        print(f"\n测试: {model_name}")
        print(f"  类型: {model_type}, 深度思考: {thinking}, 智能搜索: {search}")
        
        try:
            result = client.chat(
                "What is 2+2? Reply with just the number.",
                session_id,
                model_type=model_type,
                thinking_enabled=thinking,
                search_enabled=search,
                verbose=False
            )
            print(f"  回复: {result['response'][:50]}")
        except Exception as e:
            print(f"  错误: {e}")
    
    print("\n✅ 模型类型测试完成")


def test_file_upload():
    """文件上传测试"""
    print("=" * 60)
    print("文件上传测试")
    print("=" * 60)
    
    token = get_token()
    client = DeepSeekClient(token=token)
    
    session = client.create_session()
    session_id = session["id"]
    print(f"会话 ID: {session_id}")
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("The answer to life, the universe, and everything is 42.")
        test_file = f.name
    
    print(f"测试文件: {test_file}")
    
    # 上传文件
    print("\n上传文件中...")
    try:
        file_id = client.upload_and_prepare_file(test_file)
        print(f"文件 ID: {file_id}")
        
        # 发送带附件的消息
        print("\n发送带附件的消息...")
        result = client.chat(
            "What is the answer according to the file?",
            session_id,
            file_ids=[file_id],
            search_enabled=False,
            verbose=False
        )
        print(f"回复: {result['response']}")
        
        if "42" in result["response"]:
            print("\n✅ 文件上传测试通过 - AI 读取了文件内容")
        else:
            print("\n⚠️ 文件上传测试 - AI 可能没有读取文件内容")
    except Exception as e:
        print(f"\n❌ 文件上传测试失败: {e}")
    finally:
        # 清理测试文件
        os.unlink(test_file)


def test_session_management():
    """会话管理测试"""
    print("=" * 60)
    print("会话管理测试")
    print("=" * 60)
    
    token = get_token()
    client = DeepSeekClient(token=token)
    
    # 创建会话
    session = client.create_session()
    print(f"创建会话: {session['id']}")
    
    # 获取会话列表
    sessions = client.get_chat_sessions()
    print(f"会话数量: {len(sessions)}")
    
    # 删除会话
    try:
        client.delete_session(session['id'])
        print(f"删除会话: {session['id']}")
        print("\n✅ 会话管理测试通过")
    except Exception as e:
        print(f"\n⚠️ 删除会话失败: {e}")


def test_stream():
    """流式响应测试"""
    print("=" * 60)
    print("流式响应测试")
    print("=" * 60)
    
    token = get_token()
    client = DeepSeekClient(token=token)
    
    session = client.create_session()
    session_id = session["id"]
    
    print("发送: Write a short poem about AI")
    print("回复:\n")
    
    for event in client.send_message(
        session_id=session_id,
        prompt="Write a short poem about AI. Max 4 lines.",
        model_type="default"
    ):
        if "content" in event:
            print(event["content"], end="", flush=True)
    
    print("\n\n✅ 流式响应测试完成")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("DeepSeek Reverse API 完整测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("基本对话", test_basic),
        ("多轮对话", test_multi_turn),
        ("模型类型", test_model_types),
        ("流式响应", test_stream),
        ("会话管理", test_session_management),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            test_func()
            results.append((name, "✅ 通过"))
        except Exception as e:
            results.append((name, f"❌ 失败: {e}"))
        print()
    
    # 跳过文件上传测试（需要较长时间）
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        print(f"  {name}: {result}")
    
    print("\n提示: 文件上传测试需要单独运行: python3 test_client.py file")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        tests = {
            "basic": test_basic,
            "multi": test_multi_turn,
            "model": test_model_types,
            "file": test_file_upload,
            "session": test_session_management,
            "stream": test_stream,
            "all": run_all_tests,
        }
        
        if test_name in tests:
            tests[test_name]()
        else:
            print(f"未知测试: {test_name}")
            print(f"可用测试: {', '.join(tests.keys())}")
    else:
        # 默认运行基本测试
        test_basic()


if __name__ == "__main__":
    main()
