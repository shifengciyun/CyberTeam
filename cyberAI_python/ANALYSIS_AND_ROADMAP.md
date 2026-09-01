# CyberStrikeAI Python — 框架分析与实施路线图

> 本文档基于对项目所有源码的逐文件审阅，记录每个文件的实际作用、完成状态，
> 以及基于依赖关系排列的实施优先级。

---

## 一、项目定位

**CyberStrikeAI Python** 是一个 AI 驱动的 CTF / 渗透测试平台（对标 Go 版 CyberStrikeAI）。
核心思路：**用 LLM（DeepSeek）驱动 Agent，Agent 自主调用安全工具自动解题找 flag**。

技术栈：FastAPI + DeepSeek API（OpenAI 兼容）+ SQLAlchemy/SQLite + ChromaDB + React

---

## 二、分层架构

```
用户（CLI / React前端 / 机器人）
    │
    ▼
┌─ 入口层 ─────────────────────────────────────────────┐
│  main.py (CLI)  server.py (API)  webapp.py (完整)     │
└──────────────────────────┬───────────────────────────┘
                           │
┌─ Web后端层 ──────────────▼───────────────────────────┐
│  web/app.py          FastAPI 主应用                    │
│  web/routers/        8个路由模块（auth/chat/tools/...）│
│  web/middleware/      认证/限流/日志中间件              │
│  web/schemas/        Pydantic 请求/响应模型             │
└──────────────────────────┬───────────────────────────┘
                           │
┌─ Agent编排层 ────────────▼───────────────────────────┐
│  agents/orchestrator.py      多Agent生命周期管理        │
│  agents/base_agent.py        Agent基类（组合核心循环）   │
│  agents/single_agent.py      单Agent模式               │
│  agents/supervisor_agent.py  主管调度模式               │
│  agents/plan_execute_agent.py 先规划后执行模式          │
│  agents/specialists/         7个专业Agent               │
└──────────────────────────┬───────────────────────────┘
                           │
┌─ 核心引擎层 ─────────────▼───────────────────────────┐
│  core/agent.py       ⭐ Agent核心循环（已完整实现）     │
│  core/llm.py         LLM客户端封装                     │
│  core/tools.py       工具管理门面                       │
│  core/memory.py      记忆系统（短期+长期）              │
│  core/workflow.py    工作流门面                         │
└──────────┬────────────────────────┬──────────────────┘
           │                        │
┌─ 工具层 ─▼──────────┐  ┌─ 知识库层 ▼────────────────┐
│  tools/registry.py   │  │  knowledge/base.py          │
│  tools/executor.py   │  │  knowledge/vector_store.py  │
│  tools/builtin/      │  │  knowledge/retriever.py     │
│   14个安全工具模块    │  │  knowledge/embeddings.py    │
│  tools/configs/      │  │  knowledge/docs/            │
│   YAML工具配置       │  │   4个知识文档(JSON)         │
│  tools/mcp_*.py      │  └────────────────────────────┘
│   MCP协议扩展        │
└──────────────────────┘
           │
┌─ 工作流层 ▼──────────────────────────────────────────┐
│  workflow/engine.py    工作流引擎入口                   │
│  workflow/graph.py    DAG图 + 拓扑排序                 │
│  workflow/executor.py 按拓扑序执行节点                  │
│  workflow/state.py    共享状态 + 变量引用               │
│  workflow/node.py     节点定义（6种类型）               │
│  workflow/templates/  3个预定义工作流模板               │
└──────────────────────────┬───────────────────────────┘
                           │
┌─ 数据层 ─────────────────▼───────────────────────────┐
│  database/models.py    7张ORM表                        │
│  database/db.py        Database类（CRUD完整）           │
│  database/repositories/ 5个独立Repository（骨架）       │
└──────────────────────────┬───────────────────────────┘
                           │
┌─ 安全层 ─────────────────▼───────────────────────────┐
│  security/auth.py      认证管理                        │
│  security/token.py     JWT Token管理                   │
│  security/password.py  密码哈希                        │
│  security/rbac.py      RBAC权限控制                    │
│  security/middleware.py 安全中间件                     │
└──────────────────────────────────────────────────────┘
```

---

## 三、逐文件分析

### 3.1 入口文件

| 文件 | 状态 | 作用 |
|------|------|------|
| `main.py` | 完整 | CLI入口，`python main.py "任务"` 调 Agent.think() |
| `server.py` | 完整 | API服务器入口，启动 uvicorn（端口8080） |
| `webapp.py` | 骨架 | Web应用入口，未来挂载React静态文件 |

### 3.2 core/ — 核心引擎层

| 文件 | 状态 | 作用 |
|------|------|------|
| `core/agent.py` | **完整** | Agent核心类。实现完整的 Agent 循环：构建消息 → 调LLM → 判断tool_calls → 执行工具 → 结果回传 → 循环直到输出最终答案。支持3种模式、工具注册（代码+YAML）、记忆系统、最大迭代控制（默认30轮） |
| `core/llm.py` | 骨架 | LLM客户端封装。定义了 chat/chat_with_tools/stream_chat/embed 四个接口，均 `raise NotImplementedError` |
| `core/tools.py` | 骨架 | 工具管理门面（ToolManager）。组合 ToolRegistry + ToolExecutor，暴露 get_schemas/execute/aexecute |
| `core/memory.py` | 骨架 | 记忆系统。两层设计：短期（会话内消息）+ 长期（SQLite持久化），定义了 remember/recall/forget |
| `core/workflow.py` | 骨架 | 工作流门面。组合 WorkflowEngine + WorkflowGraph，暴露 run/list_templates/load_template |

### 3.3 agents/ — 多Agent编排层

| 文件 | 状态 | 作用 |
|------|------|------|
| `agents/base_agent.py` | 完整 | Agent基类。组合模式：持有 `core.agent.Agent`（核心循环）+ 自己的策略。think() 直接转发给 core |
| `agents/single_agent.py` | 骨架 | 单Agent模式，最简，适合简单问答/单工具链 |
| `agents/supervisor_agent.py` | 骨架 | Supervisor模式。主管拆分任务 → 分发给子Agent → 汇总结果（并行分工）。核心是 `_dispatch()` 和 `_aggregate()` |
| `agents/plan_execute_agent.py` | 骨架 | Plan-Execute模式。LLM生成执行计划 → 逐步执行 → 失败时修订计划重试（串行步骤） |
| `agents/orchestrator.py` | 骨架 | 编排器。管理Agent实例生命周期（全局单例），get_or_create/destroy/list_active |
| `agents/specialists/recon_agent.py` | 骨架 | 侦察Agent（子域名/端口/指纹/技术栈） |
| `agents/specialists/web_agent.py` | 骨架 | Web安全Agent |
| `agents/specialists/exploit_agent.py` | 骨架 | 漏洞利用Agent |
| `agents/specialists/crypto_agent.py` | 骨架 | 密码学Agent |
| `agents/specialists/forensics_agent.py` | 骨架 | 取证Agent |
| `agents/specialists/reverse_agent.py` | 骨架 | 逆向Agent |
| `agents/specialists/pwn_agent.py` | 骨架 | 二进制漏洞Agent |

### 3.4 tools/ — 工具系统层

| 文件 | 状态 | 作用 |
|------|------|------|
| `tools/registry.py` | **完整** | 工具注册表。支持 YAML配置注册、动态导入、分类管理、启用/禁用、schema构建。是工具系统的核心 |
| `tools/executor.py` | 完整 | 工具执行器。同步执行（带计时）+ 异步执行（run_in_executor），错误包装 |
| `tools/mcp_client.py` | 骨架 | MCP客户端。连接外部MCP工具服务器（如HexStrike/Burp），支持stdio/SSE |
| `tools/mcp_server.py` | 骨架 | MCP服务器。把ToolRegistry暴露为MCP服务端 |
| `tools/builtin/http_tools.py` | 骨架 | HTTP请求工具（GET/POST/HEAD等） |
| `tools/builtin/encoding_tools.py` | 骨架 | 编解码工具（base64/hex/url） |
| `tools/builtin/nmap_tool.py` | 骨架 | Nmap端口扫描 |
| `tools/builtin/sqlmap_tool.py` | 骨架 | SQL注入检测 |
| `tools/builtin/ffuf_tool.py` | 骨架 | 目录/参数爆破 |
| `tools/builtin/gobuster_tool.py` | 骨架 | 子域名/目录扫描 |
| `tools/builtin/nikto_tool.py` | 骨架 | Web漏洞扫描 |
| `tools/builtin/nuclei_tool.py` | 骨架 | 模板化漏洞扫描 |
| `tools/builtin/hydra_tool.py` | 骨架 | 暴力破解 |
| `tools/builtin/subfinder_tool.py` | 骨架 | 子域名发现 |
| `tools/builtin/whatweb_tool.py` | 骨架 | Web指纹识别 |
| `tools/builtin/crypto_tools.py` | 骨架 | 密码学工具（RSA/AES/哈希/异或） |
| `tools/builtin/forensics_tools.py` | 骨架 | 取证工具（file/strings/exiftool/binwalk） |
| `tools/builtin/misc_tools.py` | 骨架 | 杂项工具（DNS/whois/JSON格式化） |
| `tools/configs/nmap.yaml` | 已有 | Nmap工具的YAML配置 |
| `tools/configs/sqlmap.yaml` | 已有 | SQLMap工具的YAML配置 |

### 3.5 web/ — Web后端层

| 文件 | 状态 | 作用 |
|------|------|------|
| `web/app.py` | **完整** | FastAPI主应用。CORS配置、所有路由注册、Pydantic模型、启动事件。调用AuthManager/ToolRegistry/Database等 |
| `web/routers/auth.py` | 骨架 | 认证路由 /api/auth（login/logout/register） |
| `web/routers/chat.py` | 骨架 | 对话路由 /api/chat + /api/conversations |
| `web/routers/agent.py` | 骨架 | Agent路由 /api/agents（CRUD） |
| `web/routers/tools.py` | 骨架 | 工具路由 /api/tools（列表/详情/执行） |
| `web/routers/knowledge.py` | 骨架 | 知识库路由 /api/knowledge |
| `web/routers/workflow.py` | 骨架 | 工作流路由 /api/workflows |
| `web/routers/admin.py` | 骨架 | 管理路由 /api/admin（stats/audit/system） |
| `web/routers/websocket.py` | 骨架 | WebSocket /ws 实时对话 |
| `web/middleware/auth.py` | 骨架 | 认证中间件 |
| `web/middleware/logging.py` | 完整 | 日志中间件（记录method/path/status/耗时） |
| `web/middleware/rate_limit.py` | 骨架 | 限流中间件（令牌桶，按IP+路径） |

### 3.6 database/ — 数据层

| 文件 | 状态 | 作用 |
|------|------|------|
| `database/models.py` | **完整** | SQLAlchemy ORM模型。7张表：User、Conversation、Message、Agent、ToolExecution、Workflow、AuditLog |
| `database/db.py` | **完整** | Database类。会话管理（上下文管理器）+ 全部CRUD操作（用户/对话/消息/Agent/工具执行/工作流/审计/统计） |
| `database/repositories/*.py` | 骨架 | 各表的独立Repository（audit/conversation/message/tool_execution/user） |

### 3.7 security/ — 安全层

| 文件 | 状态 | 作用 |
|------|------|------|
| `security/auth.py` | 部分 | 认证管理。create_access_token/verify_token/revoke_token 已转发给 TokenManager；authenticate/register 未实现 |
| `security/token.py` | 骨架 | JWT Token管理。create_token/verify_token/revoke_token 均未实现 |
| `security/password.py` | 骨架 | 密码哈希。hash_password/verify_password 未实现 |
| `security/rbac.py` | 骨架 | RBAC权限控制。定义了三级权限（admin/user/guest），check/require 未实现 |
| `security/middleware.py` | 骨架 | 安全中间件（安全头/敏感脱敏） |

### 3.8 knowledge/ — 知识库/RAG层

| 文件 | 状态 | 作用 |
|------|------|------|
| `knowledge/base.py` | 骨架 | 知识库基类。add_document/get_document/list_documents/search/delete |
| `knowledge/vector_store.py` | 骨架 | 向量存储。支持ChromaDB/FAISS/sqlite-vec，add/query/delete/count |
| `knowledge/retriever.py` | 骨架 | 检索器。retrieve（向量检索）+ build_context（拼装LLM上下文） |
| `knowledge/embeddings.py` | 骨架 | 嵌入模型。embed/embed_batch |
| `knowledge/docs/*.json` | 已有 | 4个预置知识文档（CTF/漏洞/payload/工具） |
| `knowledge/configs/knowledge_config.yaml` | 已有 | 知识库配置 |

### 3.9 workflow/ — 工作流引擎层

| 文件 | 状态 | 作用 |
|------|------|------|
| `workflow/node.py` | **完整** | 节点定义。6种类型（agent/tool/condition/merge/start/end），输入输出边管理 |
| `workflow/graph.py` | 骨架 | DAG工作流图。add_node/add_edge + Kahn拓扑排序 + from_definition |
| `workflow/state.py` | 骨架 | 状态管理。共享数据存储 + `${node_id.output}` 变量引用解析 |
| `workflow/executor.py` | 骨架 | 执行器。按拓扑序执行节点 |
| `workflow/engine.py` | 骨架 | 工作流引擎。构建→校验→执行的统一入口 |
| `workflow/templates/*.yaml` | 已有 | 3个预定义模板（CTF/渗透/侦察工作流） |

### 3.10 integrations/ — 第三方平台集成

| 文件 | 状态 | 作用 |
|------|------|------|
| `integrations/dingtalk.py` | 骨架 | 钉钉机器人 |
| `integrations/feishu.py` | 骨架 | 飞书机器人 |
| `integrations/telegram.py` | 骨架 | Telegram机器人 |
| `integrations/wechat.py` | 骨架 | 微信机器人 |

### 3.11 scripts/ — 运维脚本

| 文件 | 状态 | 作用 |
|------|------|------|
| `scripts/setup.py` | 骨架 | 一键安装：venv + 依赖 + 初始化 |
| `scripts/seed.py` | 骨架 | 初始化种子数据（admin用户/示例Agent/知识） |
| `scripts/migrate.py` | 空 | 数据库迁移 |
| `scripts/backup.py` | 空 | 数据备份 |

### 3.12 frontend/ — React 前端

```
frontend/react-app/src/
├── pages/          8个页面：Login/Dashboard/Chat/Agents/Tools/Workflows/Knowledge/Settings
├── components/     7组组件：Agent/Chat/Common/Knowledge/Tools/Workflow/Admin
├── services/       api.ts（API封装）
├── store/          状态管理
├── hooks/          自定义Hooks
├── utils/          工具函数
├── App.tsx         路由配置
└── main.tsx        入口
```

状态：页面/组件骨架已建，具体功能待实现。

---

## 四、项目工作逻辑

### 4.1 核心 Agent 循环（最关键的机制）

```
用户输入 task
    │
    ▼
Agent.think(task)
    │
    ├── ① 构建消息列表：system_prompt + context + memory + user_task
    │
    ├── ② 循环（最多30轮）：
    │       │
    │       ├── 调用 DeepSeek LLM（OpenAI兼容协议）
    │       │   传入：messages + tools schema + temperature
    │       │
    │       ├── LLM 返回是否需要 tool_calls？
    │       │   │
    │       │   ├── YES → 执行工具函数 → 结果以 role="tool" 回填消息 → 继续循环
    │       │   │
    │       │   └── NO  → 返回 content 作为最终答案
    │       │           → 存入记忆（最近10条）
    │       │           → 设置状态为 completed
    │       │           → return
    │       │
    │       └── 异常处理：错误信息回填消息，继续循环
    │
    └── 达到最大迭代 → 返回"达到最大迭代次数"
```

### 4.2 工具调用流程

```
LLM 返回 tool_calls: [{name: "nmap_scan", arguments: {target: "10.0.0.1"}}]
    │
    ├── 把 assistant 消息（含 tool_calls）加入消息历史
    │
    ├── 遍历每个 tool_call：
    │       │
    │       ├── 解析 function_name + arguments
    │       │
    │       ├── 在 tool_functions 字典中查找对应函数
    │       │
    │       ├── 执行：result = tool_functions[name](**arguments)
    │       │   （工具内部：subprocess.run / requests.get / pycryptodome 等）
    │       │
    │       ├── 截断过长结果（>2000字符）
    │       │
    │       └── 以 role="tool" + tool_call_id 回填消息
    │
    └── 记录到 state.tool_calls（用于审计/API返回）
```

### 4.3 Web 请求流程

```
浏览器/客户端
    │
    ▼
FastAPI (web/app.py)
    │
    ├── POST /api/auth/login
    │   → AuthManager.authenticate() → TokenManager.create_token()
    │   → 返回 JWT access_token
    │
    ├── POST /api/chat (需Bearer Token)
    │   → TokenManager.verify_token() → 验证用户
    │   → Database.create_conversation() → 创建对话
    │   → Agent.think(message) → 核心循环
    │   → Database.save_message() × 2（用户+助手）
    │   → 返回 {response, conversation_id, tool_calls}
    │
    ├── WebSocket /ws
    │   → 实时双向通信 → 调 Agent.think() → 流式返回
    │
    ├── /api/tools → ToolRegistry 列表/执行
    ├── /api/agents → Agent CRUD
    ├── /api/workflows → 工作流 执行
    ├── /api/knowledge → 知识库 搜索
    └── /api/admin → 系统统计/审计日志
```

### 4.4 工作流执行流程

```
YAML定义 (如 ctf_workflow.yaml)
    │
    ▼
WorkflowGraph.from_definition()     → 构建 DAG 图
    │
    ▼
graph.topological_order()           → Kahn拓扑排序，确定执行顺序
    │
    ▼
WorkflowExecutor.execute()          → 按拓扑序逐节点执行
    │                                  每个节点 = 调用对应 Agent.think()
    ▼
WorkflowState                       → 节点结果写入共享状态
                                      下游节点通过 ${node_id.output} 读取上游结果
```

### 4.5 多 Agent 协作模式

```
┌─ Single 模式（默认）──────────────────────────┐
│  用户 → Agent.think() → 工具循环 → 返回        │
└───────────────────────────────────────────────┘

┌─ Supervisor 模式 ─────────────────────────────┐
│  用户 → SupervisorAgent                        │
│           ├─ LLM拆分任务                       │
│           ├─ 分发给子Agent (recon/web/exploit) │
│           │   每个子Agent.think() = 一个工具    │
│           └─ 汇总所有子Agent结果                │
└───────────────────────────────────────────────┘

┌─ Plan-Execute 模式 ───────────────────────────┐
│  用户 → PlanExecuteAgent                       │
│           ├─ LLM生成执行计划                    │
│           │   [{step:1, action:"nmap", params}│
│           │    {step:2, action:"sqlmap", ...}] │
│           ├─ 逐步执行                           │
│           └─ 失败时 _revise() 修订计划重试      │
└───────────────────────────────────────────────┘
```

---

## 五、完成度总结

| 层级 | 完成度 | 说明 |
|------|--------|------|
| core/agent.py | 100% | 核心Agent循环完整可用 |
| database/ (models+db) | 90% | ORM + CRUD完整，Repository层未实现 |
| tools/registry.py | 100% | 工具注册表完整 |
| tools/executor.py | 100% | 工具执行器完整 |
| web/app.py | 80% | 路由定义完整，但调用的模块多为骨架 |
| agents/base_agent.py | 100% | 基类完整 |
| security/ | 20% | 框架在，具体实现未完成 |
| knowledge/ | 10% | RAG全链路未实现 |
| workflow/ | 15% | 节点定义完整，引擎/执行器未实现 |
| agents/specialists/ | 5% | 只有空壳，未注册专业工具 |
| tools/builtin/ | 5% | 14个安全工具全部为骨架 |
| integrations/ | 5% | 4个平台集成全部为骨架 |
| frontend/ | 30% | 页面结构有，具体功能待实现 |

---

## 六、实施路线图

> 原则：**先跑通一条完整链路，再逐步扩展**。每个阶段结束后可独立验证。

### 阶段一：跑通核心链路

**目标**：`用户输入 → Agent → LLM → 工具执行 → 返回结果` 端到端跑通。

**依赖关系**：core/llm.py 是所有后续工作的基础，必须最先完成。

| 优先级 | 文件 | 工作内容 | 预估工作量 |
|--------|------|----------|-----------|
| P0 | `core/llm.py` | 实现 chat_with_tools()：传入 messages + tools，返回含 tool_calls 的响应。这是 Agent 调 LLM 的基础 | 小 |
| P1 | `tools/builtin/http_tools.py` | 实现 HTTP 请求工具（requests），GET/POST/HEAD，返回状态码+响应头+响应体 | 小 |
| P2 | `tools/builtin/encoding_tools.py` | base64/hex/url 编解码，纯标准库，CTF高频使用 | 小 |
| P3 | `security/token.py` | JWT 创建/验证/吊销（python-jose + HS256） | 小 |
| P4 | `security/password.py` | 密码哈希（passlib pbkdf2_sha256） | 小 |
| P5 | `security/auth.py` | authenticate（查用户+验密码）/ register（建用户） | 小 |

**验收标准**：
- `python main.py "访问 http://example.com 并告诉我状态码"` → Agent 自主调用 http_get 工具并返回结果
- `python server.py` 启动后，`curl` 注册 → 登录拿 token → 带 token 调 `/api/chat`

### 阶段二：补全安全工具集

**目标**：Agent 能调用真实的安全扫描工具解CTF题。

**依赖关系**：需要阶段一完成（Agent循环已跑通），且目标系统需安装对应工具。

| 优先级 | 文件 | 工作内容 |
|--------|------|----------|
| P0 | `tools/builtin/nmap_tool.py` | 端口扫描（subprocess调nmap） |
| P0 | `tools/builtin/nikto_tool.py` | Web漏洞扫描 |
| P1 | `tools/builtin/sqlmap_tool.py` | SQL注入检测 |
| P1 | `tools/builtin/ffuf_tool.py` | 目录/参数爆破 |
| P1 | `tools/builtin/subfinder_tool.py` | 子域名发现 |
| P1 | `tools/builtin/nuclei_tool.py` | 模板化漏洞扫描 |
| P2 | `tools/builtin/gobuster_tool.py` | 子域名/目录扫描 |
| P2 | `tools/builtin/hydra_tool.py` | 暴力破解 |
| P2 | `tools/builtin/whatweb_tool.py` | Web指纹识别 |
| P2 | `tools/builtin/crypto_tools.py` | RSA/AES/哈希/异或 |
| P2 | `tools/builtin/forensics_tools.py` | file/strings/exiftool/binwalk |
| P2 | `tools/builtin/misc_tools.py` | DNS/whois/JSON格式化 |

同时为每个专业 Agent 注册对应工具集：
- `recon_agent` → nmap + subfinder + whatweb
- `web_agent` → nikto + sqlmap + ffuf + nuclei + http
- `exploit_agent` → sqlmap + http + encoding
- `crypto_agent` → crypto_tools + encoding
- `forensics_agent` → forensics_tools + encoding
- `reverse_agent` → crypto_tools + misc
- `pwn_agent` → nmap + misc

**验收标准**：Agent 能自主选择并调用 5+ 种工具完成 CTF 题目。

### 阶段三：知识库 RAG

**目标**：Agent 解题时能检索相关知识辅助决策。

| 优先级 | 文件 | 工作内容 |
|--------|------|----------|
| P0 | `knowledge/embeddings.py` | 接入 embedding 模型（优先用 LLM embed 接口） |
| P1 | `knowledge/vector_store.py` | ChromaDB 向量存储（add/query/delete） |
| P2 | `knowledge/retriever.py` | 查询向量化 → 相似检索 → 拼装上下文 |
| P3 | `knowledge/base.py` | 知识库 CRUD |
| P3 | `core/memory.py` | Agent 长期记忆实现（remember/recall/forget） |

**验收标准**：问 Agent "SQL注入有哪些绕过WAF的技巧"，能从知识库检索相关文档并结合回答。

### 阶段四：工作流引擎

**目标**：支持 CTF/渗透/侦察等多步骤自动化工作流。

| 优先级 | 文件 | 工作内容 |
|--------|------|----------|
| P0 | `workflow/graph.py` | DAG 构建 + Kahn 拓扑排序 + from_definition |
| P1 | `workflow/executor.py` | 按拓扑序执行节点 |
| P2 | `workflow/state.py` | 变量引用解析 `${node.output}` |
| P3 | `workflow/engine.py` | 引擎入口串联 |

**验收标准**：加载 ctf_workflow.yaml，自动执行 侦察→分析→利用 三步流程。

### 阶段五：多Agent协作

**目标**：Supervisor 拆任务、Plan-Execute 规划执行。

| 优先级 | 文件 | 工作内容 |
|--------|------|----------|
| P0 | `agents/supervisor_agent.py` | 任务拆分 + 子Agent调度（_dispatch） + 结果汇总（_aggregate） |
| P1 | `agents/plan_execute_agent.py` | LLM生成计划 → 逐步执行 → 失败修订（_plan/_execute_step/_revise） |
| P2 | `agents/orchestrator.py` | Agent 生命周期管理 |

**验收标准**：Supervisor 模式下，能自动将"对目标做完整渗透测试"拆分为侦察+Web+利用子任务。

### 阶段六：平台集成 + 前端

| 优先级 | 文件 | 工作内容 |
|--------|------|----------|
| P1 | `web/routers/*.py` | 8个路由模块填空实现 |
| P1 | `web/middleware/auth.py` | 认证中间件 |
| P1 | `web/middleware/rate_limit.py` | 限流中间件 |
| P2 | `integrations/*.py` | 飞书/钉钉/Telegram/微信 Bot |
| P2 | `frontend/react-app/` | React 前端页面功能补全 |
| P3 | `scripts/seed.py` | 初始化种子数据 |

---

## 七、关键技术决策

### 7.1 为什么 Agent 循环用同步而非异步

`core/agent.py` 的 `think()` 是同步的，因为：
- Agent 循环是串行的（必须等 LLM 返回才能决定下一步）
- 工具执行（subprocess）本身是阻塞的
- Web层可以通过 `run_in_executor` 把同步 think() 放到线程池异步执行

### 7.2 工具注册的两种方式

1. **代码注册**：在 Python 文件中定义函数，调用 `agent.register_tool()`
2. **YAML配置注册**：在 `tools/configs/*.yaml` 中声明 command/args/parameters，`registry.register_from_yaml()` 自动生成工具函数和 schema

建议：简单工具用代码注册（更灵活），外部命令行工具用YAML（更声明式）。

### 7.3 多Agent的本质

多Agent不是"多个独立循环"，而是**单循环 + 子Agent作为工具**。Supervisor把自己的子Agent的 `think()` 注册为工具函数，LLM觉得某个子Agent合适就"调用"它。底层仍然是同一个 Agent 循环在驱动。

---

## 八、常见问题

1. **工具输出太大**：工具结果会塞进 LLM 上下文，`core/agent.py` 已有 `[:2000]` 截断
2. **subprocess 超时**：nmap/sqlmap 可能跑很久，务必设置 `timeout=` 参数
3. **LLM 参数类型**：工具函数要容忍 str/int 混用，executor 做宽松校验
4. **JWT 密钥**：`security/token.py` 中 `secret="CHANGE_ME"` 是占位，必须从 `.env` 读取
5. **数据库路径**：确保 `data/` 目录存在
6. **前端跨域**：React dev(5173) 调后端(8080) 需配 Vite proxy 或依赖 app.py 已开的 CORS
