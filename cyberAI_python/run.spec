# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 — CyberStrikeAI Python

用法:
    pip install pyinstaller
    pyinstaller run.spec

产出:
    dist/CyberStrikeAI/CyberStrikeAI.exe  (目录模式, ~50MB)
    或 dist/CyberStrikeAI.exe             (单文件模式, 启动较慢)
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
ROOT = os.path.dirname(os.path.abspath(SPEC))

# ========== 收集数据文件 ==========
# 需要打包进去的目录/文件
datas = [
    # 工具配置
    (os.path.join(ROOT, 'tools', 'configs'), 'tools/configs'),
    # 工作流模板
    (os.path.join(ROOT, 'workflow', 'templates'), 'workflow/templates'),
    # 知识库
    (os.path.join(ROOT, 'knowledge', 'docs'), 'knowledge/docs'),
    (os.path.join(ROOT, 'knowledge', 'skills'), 'knowledge/skills'),
    (os.path.join(ROOT, 'knowledge', 'configs'), 'knowledge/configs'),
    # Agent角色配置
    (os.path.join(ROOT, 'agents', 'roles'), 'agents/roles'),
    # 前端静态文件
    (os.path.join(ROOT, 'frontend'), 'frontend'),
    # 配置文件
    (os.path.join(ROOT, 'config.yaml'), '.'),
    (os.path.join(ROOT, '.env.example'), '.'),
]

# ========== 收集隐藏导入 ==========
hiddenimports = [
    # FastAPI 相关
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'starlette',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.middleware.base',
    # 数据库
    'sqlalchemy',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.ext',
    'sqlalchemy.ext.declarative',
    # 安全
    'jose',
    'passlib',
    'passlib.hash',
    'bcrypt',
    # 知识库
    'chromadb',
    # 项目内部模块
    'web.app',
    'web.deps',
    'web.routers',
    'web.routers.auth',
    'web.routers.chat',
    'web.routers.tools',
    'web.routers.agent',
    'web.routers.workflow',
    'web.routers.knowledge',
    'web.routers.admin',
    'web.routers.websocket',
    'web.middleware.auth',
    'web.middleware.rate_limit',
    'web.middleware.logging',
    'core.agent',
    'core.llm',
    'core.tools',
    'core.memory',
    'core.workflow',
    'core.checkpoint',
    'core.context_budget',
    'tools.registry',
    'tools.executor',
    'database.db',
    'database.models',
    'security.auth',
    'security.token',
    'security.password',
    'security.rbac',
    'knowledge.base',
    'knowledge.vector_store',
    'knowledge.retriever',
    'knowledge.embeddings',
    'workflow.engine',
    'workflow.graph',
    'workflow.executor',
    'workflow.state',
    'workflow.node',
    'agents.base_agent',
    'agents.orchestrator',
    'agents.supervisor_agent',
    'agents.plan_execute_agent',
    'agents.roles_loader',
    'agents.specialists',
    'agents.specialists.recon_agent',
    'agents.specialists.web_agent',
    'agents.specialists.exploit_agent',
    'agents.specialists.crypto_agent',
    'agents.specialists.forensics_agent',
    'agents.specialists.reverse_agent',
    'agents.specialists.pwn_agent',
    'integrations.dingtalk',
    'integrations.feishu',
    'integrations.telegram',
    'integrations.wechat',
    'integrations.base',
]

a = Analysis(
    ['run.py'],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[os.path.join(ROOT, '_hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大包，减小体积
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'scipy', 'PIL', 'cv2', 'torch', 'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- 目录模式(推荐): 启动快, dist/CyberStrikeAI/CyberStrikeAI.exe ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CyberStrikeAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 保留控制台, 显示启动日志
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CyberStrikeAI',
)
