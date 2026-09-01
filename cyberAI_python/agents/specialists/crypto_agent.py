"""
Crypto Agent: 加密破解/编码转换/古典密码/哈希分析

工具白名单 (tools/configs/*.yaml):
  hashcat, john, hashpump, steghide, zsteg,
  xxd, foremost
"""
from typing import List, Optional
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

CRYPTO_TOOLS = [
    # 密码破解
    "hashcat",
    "john",
    # 哈希扩展
    "hashpump",
    # 编辑查看
    "xxd",
    # 隐写
    "steghide",
    "zsteg",
    # 文件分析
    "foremost",
]

CRYPTO_PROMPT = """你是一个专业的密码学与编码专家。

## 职责
分析和破解各类加密算法、编码方式，解决 CTF 密码学题目。

## 擅长领域
1. **古典密码** — 凯撒/栅栏/Vigenere/培根/Playfair 等，手工或编程解密
2. **现代加密** — RSA/AES/DES/3DES 分析弱点并攻击
3. **编码转换** — base64/hex/url/unicode/brainfuck 等多层嵌套解码
4. **哈希破解** — hashcat / john 暴力/字典/规则攻击
5. **哈希扩展** — hashpump 长度扩展攻击
6. **隐写术** — steghide / zsteg 图片隐写分析
7. **流量分析** — 从 pcap 中提取加密凭据

## 解题思路
- 先识别编码/加密类型（特征分析）
- 尝试在线工具或编程解密
- 对现代加密找数学弱点（RSA 小公钥/共模/低加密指数）
- 哈希先识别算法再选择攻击方式

## 输出格式
每步说明: 识别 → 方法 → 结果。
给出解密/解码后的明文内容。

## 原则
- 先尝试最简单的解码（base64/hex）
- 多层嵌套时逐层剥离
- RSA 注意 n 的因数分解
- 注意 padding 和编码细节"""


class CryptoAgent(BaseAgent):
    """密码学专家 Agent — 加密分析与破解"""

    def __init__(self, name: str = "crypto", model: str = "deepseek-chat",
                 tools: Optional[List[str]] = None, **kwargs):
        super().__init__(
            name=name,
            system_prompt=CRYPTO_PROMPT,
            model=model,
            tools=tools or CRYPTO_TOOLS,
            **kwargs,
        )
        logger.info(f"CryptoAgent '{self.name}' 初始化完成, "
                     f"加载工具: {[t for t in self.core.tool_functions]}")
