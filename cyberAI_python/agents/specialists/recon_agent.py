"""
侦察 Agent: 子域名枚举/端口扫描/服务识别/指纹/技术栈

工具白名单 (tools/configs/*.yaml):
  nmap_scan, subfinder, masscan, rustscan, amass, dnsenum,
  fierce, arp_scan, enum4linux_ng, wafw00f, whatweb, nbtscan,
  fofa_search, shodan_search, zoomeye_search, quake_search,
  gau, katana, waybackurls, dirsearch, feroxbuster, ffuf
"""
from typing import List, Optional
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

RECON_TOOLS = [
    # 主动扫描
    "nmap_scan",
    "masscan",
    "rustscan",
    # 子域名枚举
    "subfinder",
    "amass",
    "dnsenum",
    "fierce",
    # 网络发现
    "arp_scan",
    "enum4linux_ng",
    "nbtscan",
    # Web指纹
    "wafw00f",
    "whatweb",
    # 目录/路径
    "ffuf",
    "dirsearch",
    "feroxbuster",
    "gau",
    "katana",
    "waybackurls",
    # 被动情报
    "fofa_search",
    "shodan_search",
    "zoomeye_search",
    "quake_search",
]

RECON_PROMPT = """你是一个专业的信息收集/侦察专家。

## 职责
对目标进行全面的资产发现和技术栈识别，为后续攻击面分析提供基础。

## 标准流程
1. **域名/IP 枚举** — subfinder / amass / dnsenum 发现子域名
2. **端口扫描** — nmap_scan / masscan 发现开放端口和服务
3. **服务识别** — nmap -sV 识别具体服务版本
4. **Web 指纹** — whatweb / wafw00f 识别框架、WAF
5. **目录发现** — ffuf / dirsearch / feroxbuster 枚举路径
6. **被动情报** — shodan / fofa / zoomeye 查询公开信息

## 输出格式
每步完成后简要总结关键发现（IP、端口、服务、版本、技术栈）。
最后给出完整的资产清单，标注高价值目标。

## 原则
- 先被动再主动，减少对目标的请求量
- 发现的每个端口/服务都值得记录
- 注意 WAF/IDS 检测，必要时降低扫描强度"""


class ReconAgent(BaseAgent):
    """侦察专家 Agent — 信息收集与资产发现"""

    def __init__(self, name: str = "recon", model: str = "deepseek-chat",
                 tools: Optional[List[str]] = None, **kwargs):
        super().__init__(
            name=name,
            system_prompt=RECON_PROMPT,
            model=model,
            tools=tools or RECON_TOOLS,
            **kwargs,
        )
        logger.info(f"ReconAgent '{self.name}' 初始化完成, "
                     f"加载工具: {[t for t in self.core.tool_functions]}")
