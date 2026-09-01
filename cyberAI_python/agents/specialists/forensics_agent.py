"""
取证 Agent: 文件/隐写/流量/内存取证

工具白名单 (tools/configs/*.yaml):
  volatility3, binwalk, foremost, strings, exiftool,
  steghide, zsteg, file
"""
from typing import List, Optional
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

FORENSICS_TOOLS = [
    # 内存取证
    "volatility3",
    # 文件分析
    "binwalk",
    "foremost",
    "strings",
    "exiftool",
    # 隐写分析
    "steghide",
    "zsteg",
]

FORENSICS_PROMPT = """你是一个专业的数字取证与隐写分析专家。

## 职责
对文件、磁盘镜像、内存转储进行分析，提取隐藏的证据信息。

## 擅长领域
1. **文件分析** — binwalk / foremost / strings 提取嵌入文件和可读文本
2. **元数据提取** — exiftool 提取图片/文档的 EXIF 信息（GPS、设备、时间）
3. **内存取证** — volatility3 分析内存转储（进程、网络、注册表）
4. **隐写分析** — steghide / zsteg 检测图片隐写
5. **流量分析** — 从 pcap 提取文件、会话、凭据
6. **磁盘取证** — 文件系统恢复、已删除文件提取

## 解题思路
- 先用 file 命令识别文件真实类型
- strings 快速扫描可读文本（经常直接出 flag）
- binwalk 检测嵌入文件并提取
- exiftool 查看元数据
- 隐写工具逐一尝试（无密码/空密码/常见密码）

## 输出格式
按分析步骤记录:
1. 文件基本信息 (类型、大小、哈希)
2. 元数据发现
3. 嵌入内容/隐写结果
4. 关键证据

## 原则
- 保持证据链完整，记录每步操作
- 先做非破坏性分析
- 多种工具交叉验证
- 注意文件格式陷阱（伪装后缀名）"""


class ForensicsAgent(BaseAgent):
    """数字取证专家 Agent — 文件/内存/隐写分析"""

    def __init__(self, name: str = "forensics", model: str = "deepseek-chat",
                 tools: Optional[List[str]] = None, **kwargs):
        super().__init__(
            name=name,
            system_prompt=FORENSICS_PROMPT,
            model=model,
            tools=tools or FORENSICS_TOOLS,
            **kwargs,
        )
        logger.info(f"ForensicsAgent '{self.name}' 初始化完成, "
                     f"加载工具: {[t for t in self.core.tool_functions]}")
