"""
逆向 Agent: 静态分析/动态调试/脱壳/协议逆向

工具白名单 (tools/configs/*.yaml):
  ghidra, radare2, objdump, gdb, checksec,
  strings, xxd, binwalk
"""
from typing import List, Optional
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

REVERSE_TOOLS = [
    # 静态分析
    "ghidra",
    "radare2",
    "objdump",
    # 动态调试
    "gdb",
    # 二进制检查
    "checksec",
    # 文件分析
    "strings",
    "xxd",
    "binwalk",
]

REVERSE_PROMPT = """你是一个专业的逆向工程专家。

## 职责
分析二进制程序的结构和逻辑，理解其行为，找出隐藏信息或漏洞。

## 擅长领域
1. **静态分析** — ghidra 反编译、radare2 交叉引用、objdump 反汇编
2. **动态调试** — gdb 断点调试、单步跟踪、内存查看
3. **二进制保护** — checksec 检查保护机制 (NX/PIE/RELRO/Canary)
4. **字符串提取** — strings / xxd 扫描硬编码信息
5. **文件结构** — binwalk 分析文件布局、脱壳
6. **协议逆向** — 分析网络协议格式和通信逻辑

## 分析流程
1. file + checksec 获取基本信息（架构、保护、类型）
2. strings / xxd 快速扫描（找字符串、magic bytes）
3. 反汇编/反编译理解主要逻辑
4. 定位关键函数（main、加密、验证）
5. 分析算法并编写解密脚本

## 常见模式
- License 验证 → 找比较指令，提取 key
- 加密函数 → 识别算法，逆向或爆破
- 混淆代码 → 控制流分析，去除垃圾指令

## 输出格式
记录: 文件信息 → 保护机制 → 关键发现 → 算法分析 → 解决方案

## 原则
- 先易后难，strings 可能直接出答案
- 注意反调试和混淆
- 用多种工具交叉验证分析结果"""


class ReverseAgent(BaseAgent):
    """逆向工程专家 Agent — 二进制分析与逆向"""

    def __init__(self, name: str = "reverse", model: str = "deepseek-chat",
                 tools: Optional[List[str]] = None, **kwargs):
        super().__init__(
            name=name,
            system_prompt=REVERSE_PROMPT,
            model=model,
            tools=tools or REVERSE_TOOLS,
            **kwargs,
        )
        logger.info(f"ReverseAgent '{self.name}' 初始化完成, "
                     f"加载工具: {[t for t in self.core.tool_functions]}")
