"""
CyberStrikeAI 统一入口 — 打包为 .exe 后双击启动。

功能:
  1. 双击运行 → 启动 Web 服务 (端口 8080)
  2. 命令行模式 → python run.py cli "你的任务"
  3. 带参数 → python run.py --port 9090 --host 127.0.0.1

打包: pyinstaller run.spec
"""
import sys
import os
import argparse

# --- 打包兼容: 让 import 能找到项目根目录 ---
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后，sys._MEIPASS 是临时解压目录
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BUNDLE_DIR)
sys.path.insert(0, BUNDLE_DIR)


def start_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """启动 Web 服务器"""
    import uvicorn
    print(f"\n{'='*50}")
    print(f"  CyberStrikeAI Python")
    print(f"  http://{host}:{port}")
    print(f"  API 文档: http://{host}:{port}/docs")
    print(f"{'='*50}\n")
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=reload and not getattr(sys, 'frozen', False),
    )


def start_cli(task: str):
    """CLI 模式"""
    from core.agent import Agent
    agent = Agent(name="CTF专家")
    print(f"\n任务: {task}\n{'-'*40}")
    result = agent.think(task)
    print(f"\n{'='*40}\n结果:\n{result}")


def main():
    parser = argparse.ArgumentParser(
        description="CyberStrikeAI Python — AI驱动的CTF安全测试平台"
    )
    sub = parser.add_subparsers(dest="command")

    # web 子命令（默认）
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="监听端口 (默认 8080)")

    # cli 子命令
    cli_parser = sub.add_parser("cli", help="命令行模式")
    cli_parser.add_argument("task", help="要执行的任务")

    args = parser.parse_args()

    if args.command == "cli":
        start_cli(args.task)
    else:
        start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
