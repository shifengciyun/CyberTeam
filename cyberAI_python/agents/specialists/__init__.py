"""
专业 Agent 包 — 7 个安全领域专家

用法:
    from agents.specialists import ReconAgent, WebAgent, CryptoAgent
    agent = ReconAgent()
    result = agent.think("扫描目标 10.0.0.1")
"""
from agents.specialists.recon_agent import ReconAgent
from agents.specialists.web_agent import WebAgent
from agents.specialists.exploit_agent import ExploitAgent
from agents.specialists.crypto_agent import CryptoAgent
from agents.specialists.forensics_agent import ForensicsAgent
from agents.specialists.reverse_agent import ReverseAgent
from agents.specialists.pwn_agent import PwnAgent

SPECIALIST_MAP = {
    "recon": ReconAgent,
    "web": WebAgent,
    "exploit": ExploitAgent,
    "crypto": CryptoAgent,
    "forensics": ForensicsAgent,
    "reverse": ReverseAgent,
    "pwn": PwnAgent,
}

__all__ = [
    "ReconAgent", "WebAgent", "ExploitAgent",
    "CryptoAgent", "ForensicsAgent", "ReverseAgent", "PwnAgent",
    "SPECIALIST_MAP",
]
