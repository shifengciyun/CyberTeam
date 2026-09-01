"""
工作流门面 - 对上层暴露 DAG 工作流接口
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
from workflow.engine import WorkflowEngine
from workflow.graph import WorkflowGraph
import logging

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


class WorkflowManager:
    """工作流管理器 — 加载模板 + 执行工作流"""

    def __init__(self):
        self.engine = WorkflowEngine()
        self._templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self):
        """启动时加载所有 YAML 模板"""
        if not TEMPLATES_DIR.exists():
            logger.warning(f"工作流模板目录不存在: {TEMPLATES_DIR}")
            return
        for fp in sorted(TEMPLATES_DIR.glob("*.yaml")):
            try:
                with open(fp, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                name = cfg.get("name", fp.stem)
                self._templates[name] = {
                    "name": name,
                    "description": cfg.get("description", ""),
                    "nodes": cfg.get("nodes", []),
                    "edges": cfg.get("edges", []),
                    "file": str(fp),
                }
            except Exception as e:
                logger.error(f"加载工作流模板失败 {fp}: {e}")
        logger.info(f"已加载 {len(self._templates)} 个工作流模板: {list(self._templates)}")

    def run(self, definition: Dict, input_data: Dict[str, Any] = None) -> Dict:
        """执行工作流（支持直接定义或模板名）"""
        # 如果传入的是模板名，先加载模板定义
        if isinstance(definition, str):
            definition = self.load_template(definition)
        return self.engine.execute(definition, input_data or {})

    def list_templates(self) -> List[Dict]:
        """列出所有可用工作流模板"""
        return [
            {"name": t["name"], "description": t["description"]}
            for t in self._templates.values()
        ]

    def load_template(self, name: str) -> Dict:
        """按名称加载工作流模板，返回完整定义"""
        if name not in self._templates:
            available = list(self._templates.keys())
            raise ValueError(f"工作流模板 '{name}' 不存在。可用模板: {available}")
        tpl = self._templates[name]
        # 返回不含 file 路径的干净定义
        return {
            "name": tpl["name"],
            "description": tpl["description"],
            "nodes": tpl["nodes"],
            "edges": tpl["edges"],
        }

    def reload_templates(self):
        """重新加载模板目录"""
        self._templates.clear()
        self._load_templates()
