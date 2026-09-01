"""
Web 安全 Agent: 目录爆破/注入/XSS/SSRF/文件上传

工具白名单 (tools/configs/*.yaml):
  nikto, sqlmap, ffuf, nuclei, gobuster, dirsearch,
  dalfox, xsser, jaeles, graphql-scanner, jwt-analyzer,
  wpscan, wafw00f, zap, x8, paramspider
"""
from typing import List, Optional
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

WEB_TOOLS = [
    # 扫描器
    "nikto",
    "nuclei",
    "jaeles",
    "zap",
    # 注入
    "sqlmap",
    # XSS
    "dalfox",
    "xsser",
    # 目录/参数
    "ffuf",
    "dirsearch",
    "gobuster",
    "paramspider",
    # CMS/框架
    "wpscan",
    "graphql-scanner",
    "jwt-analyzer",
    # 指纹
    "wafw00f",
    "x8",
]

WEB_PROMPT = """你是一个专业的 Web 应用安全测试专家。

## 职责
对目标 Web 应用进行全面的安全检测，发现漏洞并尝试利用。

## 检测范围
1. **信息收集** — wafw00f 识别 WAF、whatweb 指纹、paramspider 发现参数
2. **目录枚举** — ffuf / dirsearch / gobuster 发现隐藏路径和文件
3. **SQL 注入** — sqlmap 检测并尝试提取数据
4. **XSS 检测** — dalfox / xsser 测试反射/存储型 XSS
5. **通用漏洞** — nikto / nuclei / jaeles 模板化扫描
6. **认证测试** — jwt-analyzer 分析 JWT、wpscan 测试 CMS
7. **高级测试** — zap 主动扫描、graphql-scanner 接口测试

## 输出格式
按漏洞严重程度排列: Critical → High → Medium → Low → Info。
每个漏洞包含: 类型、位置、Payload、验证方法。

## 原则
- 先被动枚举再主动测试
- SQL 注入先用 sqlmap --batch 自动检测
- 注意 WAF 绕过技巧
- 记录所有发现，包括负面结果（证明已测试过）"""


class WebAgent(BaseAgent):
    """Web安全专家 Agent — Web应用漏洞检测与利用"""

    def __init__(self, name: str = "web", model: str = "deepseek-chat",
                 tools: Optional[List[str]] = None, **kwargs):
        super().__init__(
            name=name,
            system_prompt=WEB_PROMPT,
            model=model,
            tools=tools or WEB_TOOLS,
            **kwargs,
        )
        logger.info(f"WebAgent '{self.name}' 初始化完成, "
                     f"加载工具: {[t for t in self.core.tool_functions]}")
