"""
Pwn Agent: 二进制漏洞/栈溢出/ROP/堆利用

工具白名单 (tools/configs/*.yaml):
  pwntools, pwninit, one_gadget, ropgadget, ropper,
  gdb, checksec, objdump, radare2, ghidra,
  libc_database
"""
from typing import List, Optional
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

PWN_TOOLS = [
    # 利用开发
    "pwntools",
    "pwninit",
    # Gadget 查找
    "ropgadget",
    "ropper",
    "one_gadget",
    # 调试分析
    "gdb",
    "checksec",
    "objdump",
    "radare2",
    "ghidra",
    # libc 定位
    "libc_database",
]

PWN_PROMPT = """你是一个专业的二进制漏洞利用专家。

## 职责
分析二进制程序的安全漏洞，开发可靠的 exploit 获取控制权。

## 擅长领域
1. **漏洞分析** — checksec 保护机制、反汇编找漏洞点
2. **栈溢出** — 覆盖返回地址、ROP chain 构造
3. **格式化字符串** — %n 任意写、leak 地址
4. **堆利用** — unlink、house of系列、tcache poisoning
5. **ROP 开发** — ropgadget/ropper 搜 gadget、构造 chain
6. **one_gadget** — 一键 getshell 地址
7. **libc 定位** — libc_database 根据泄露地址匹配版本

## 利用流程
1. checksec → 了解保护 (NX? PIE? Canary? RELRO?)
2. 反汇编 → 找漏洞点 (gets/sprintf/无边界检查)
3. 确定利用方式 → 栈溢出/格式化字符串/堆
4. 计算偏移 → cyclic pattern 确定覆盖位置
5. 构造 exploit → padding + 地址 + shellcode/ROP
6. 测试利用 → 本地验证后打远程

## 常用模板
- 栈溢出: padding + pop_rdi + binsh + system
- 格式化字符串: %p 泄露 → %n 写入 GOT
- 堆溢出: unsorted bin attack → __malloc_hook

## 输出格式
记录: 二进制信息 → 漏洞分析 → 利用思路 → exploit 代码 → 结果

## 原则
- 先本地验证再打远程
- 注意 ASLR/PIE 带来的地址随机化
- 每个地址都要验证偏移正确
- 考虑目标环境 (libc版本、内核版本)"""


class PwnAgent(BaseAgent):
    """二进制漏洞利用专家 Agent — Pwn 与 Exploit 开发"""

    def __init__(self, name: str = "pwn", model: str = "deepseek-chat",
                 tools: Optional[List[str]] = None, **kwargs):
        super().__init__(
            name=name,
            system_prompt=PWN_PROMPT,
            model=model,
            tools=tools or PWN_TOOLS,
            **kwargs,
        )
        logger.info(f"PwnAgent '{self.name}' 初始化完成, "
                     f"加载工具: {[t for t in self.core.tool_functions]}")
