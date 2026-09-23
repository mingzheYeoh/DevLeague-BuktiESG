# BuktiESG

BuktiESG 帮团队整理客户 ESG 问卷、上传佐证文件、逐题审核答案并追踪待办。目前是**团队演示版**。

## 直接体验云端版本

打开 <https://buktiesg.vercel.app/>，先用项目所属的 Vercel 团队账号通过访问验证，再在应用内注册账号。注册后会创建你的独立组织。演示文件在 [`sample/`](sample/)；请只上传合成测试资料。云端使用 Neon PostgreSQL 和私有 Vercel Blob，单个上传文件上限为 **4 MiB**。云端未配置 DeepSeek 提取密钥，因此不会自动提取文档中的数值。

## 在本机启动

需要 Docker Desktop（或 Docker Engine + Compose）、[uv](https://docs.astral.sh/uv/)、Node.js **22** 和 npm。uv 会安装项目所需的 Python 3.12。下面的命令从**仓库根目录**开始；API 和网页请分别开一个终端。

1. 复制配置文件，并在 `.env` 中填入一个本地数据库密码：

   ```powershell
   # Windows PowerShell
   Copy-Item .env.example .env
   ```

   macOS/Linux 用 `cp .env.example .env`。把 `.env` 里的 `POSTGRES_PASSWORD=` 改成 `POSTGRES_PASSWORD=你自己设的密码`，然后启动数据库：

   ```bash
   docker compose up -d --wait
   ```

2. 启动 API（第一个终端）：

   ```bash
   cd backend
   uv sync
   uv run alembic upgrade head
   uv run uvicorn app.main:app --reload
   ```

   健康检查：<http://localhost:8000/health>。

3. 启动网页（从仓库根目录打开第二个终端）：

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

   打开 <http://localhost:3000>，注册账号后即可新建案例并上传 `sample/questionnaire/customer-esg-questionnaire-2026.xlsx`。Windows PowerShell 若阻止运行 `npm.ps1`，把上面的 `npm` 改为 `npm.cmd`。

4. **可选：**如需运行文档数值提取，在第三个终端执行：

   ```bash
   cd backend
   uv run python worker.py
   ```

   没有 `DEEPSEEK_API_KEY` 时，不会向模型提供商发送文档内容，也不会提取数值。若在根目录 `.env` 配置了此密钥，**只能上传合成文件**：文档文本会发送到 `api.deepseek.com`。处理任何真实客户文件前，必须移除该密钥并在提供商处轮换旧密钥。

停止时，在运行 API、网页和 worker 的终端按 `Ctrl+C`，然后从仓库根目录运行 `docker compose stop`；数据库数据会保留。macOS/Linux 也可在完成依赖安装后使用 `./demo.sh up` 和 `./demo.sh down`。

## 验证

```bash
cd backend
uv run pytest -q --basetemp .venv/pytest-tmp

cd ../packages/ai-pipeline
uv sync
uv run pytest -q --basetemp .venv/pytest-tmp

cd ../../frontend
npm run typecheck
npm run build
```

浏览器测试首次运行前执行 `npx playwright install chromium`，之后在 `frontend/` 执行 `npm run test:e2e`。这些测试会自行启动网页并模拟 API。

## 目录与边界

`backend/` 是 FastAPI 服务和数据库迁移，`frontend/` 是 Next.js 网页，`packages/ai-pipeline/` 负责解析与分析，`sample/` 是合成演示资料。每个 API 请求都要求登录，案例数据按组织隔离。AI 输出不能直接决定审核或证据状态，也不能自行提供引用位置；状态由规则引擎计算，引用位置由服务器从文档块解析。

历史规范与决策已从工作树移除，可通过 `git show bfd45ad:docs/spec/BuktiESG-Technical-Spec-EN.md` 查阅；代码注释引用的旧执行规则可通过 `git show 06d2c84:AGENTS.md` 查阅。受保护的计算规则、安全边界和关键测试仍然有效。
