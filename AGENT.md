# CutCut AI Agent Guidelines & Architecture Manual

> **致所有协同工作的 AI Agent（Codex / Claude / Gemini / Antigravity 等）：**
> 本文件定义了 CutCut 项目的**核心定位、严格的目录流向规范、标准执行命令以及绝对红线**。在执行任何剪辑、代码修改或文件创建前，请务必严格遵守以下约束。

---

## 1. 项目定位与核心引擎架构

CutCut 是一个面向短视频平台（抖音 / 小红书 / 视频号）的工业级全自动 AI 剪辑系统。
- **核心逻辑**：多模态素材感知（`ingest`） -> 声明式分镜编排（`director` & `schema`） -> 音视频归一化与侧链闪避（`prepare`） -> 纯代码无头渲染（`studio` / Remotion） -> 自动化 QA 门禁（`verify`）。
- **技术栈**：Python 3.9+ (底层处理与 CLI) + Remotion (React 18 + TS, 渲染引擎) + FFmpeg 6.0+。

---

## 2. 严格的目录职责与 I/O 数据流向规范（红线约束）

任何 AI Agent 在处理任务时，**绝对禁止**在项目根目录下随意创建散乱文件或目录。必须严格遵守以下输入/输出约定：

| 目录路径 | 角色定义 | 存放内容与规范 | Git 追踪约束 |
| :--- | :--- | :--- | :--- |
| `data/raw/<主题名>/` | **【唯一】素材输入区** | 用户放置原始相机/手机视频的目录（例如 `data/raw/desk_setup/`）。AI **只读**此目录。 | ❌ **绝对禁止将大文件（>10MB）纳入 Git**（仅保留 `.gitkeep` 与 `README.md`） |
| `projects/<项目名>/` | **【唯一】剪辑工程区** | 每个剪辑项目的配置文件与生成结果统一存放在此（例如 `projects/pet-douyin-v02/`）。 | ✅ 只追踪 `edit_spec.json` 等配置 JSON；❌ 自动排除成片 MP4 与切片缓存 |
| `pipeline/` | **【核心】流水线引擎** | Python 算法与工具套件（感知、导演、预处理、校验、QA、CLI）。 | ✅ 纯代码，完整纳入 Git |
| `studio/` | **【渲染】Remotion 套件** | React + TypeScript 视频画幅、动效与字幕组件库。 | ✅ 纯代码与配置，完整纳入 Git（`node_modules` 排除） |
| `docs/` | **【本地笔记】过程知识库** | `docs/research/` 与 `docs/reviews/`（仅限本地参考，不入 Git 仓库）。 | ❌ **仅保留本地，不纳入 Git 仓库** |

---

## 3. 标准操作工作流与 CLI 命令指南

AI Agent 为用户剪辑视频或排查问题时，统一使用以下标准命令：

### A. 一键全自动 AI 剪辑 (端到端无人值守)
```bash
python3 -m pipeline.cli auto \
  --source data/raw/<素材子目录> \
  --prompt "<用户创意要求>" \
  --out-dir projects/<项目名> \
  --duration 20.0
```

### B. 模块化分步交互 (Agent-in-the-Loop 调试模式)
1. **素材扫描**：
   `python3 -m pipeline.cli scan --source data/raw/<素材子目录> --out projects/<项目名>/analysis`
2. **AI 导演构思 EditSpec**：
   `python3 -m pipeline.cli direct --analysis projects/<项目名>/analysis --source data/raw/<素材子目录> --prompt "..." --out-spec projects/<项目名>/edit_spec.json`
3. **合法性校验 (防跳剪/防越界/槽位完整性)**：
   `python3 -m pipeline.cli validate --spec projects/<项目名>/edit_spec.json --source data/raw/<素材子目录>`
4. **编译成片与 QA**：
   `python3 -m pipeline.cli build --spec projects/<项目名>/edit_spec.json --source data/raw/<素材子目录>`

---

## 4. AI Agent 的绝对行为红线 (Critical Guardrails)

1. **防仓库污染红线**：
   - 任何生成的 `.mp4`, `.mov`, `.wav`, `.jpg`, `.png` 临时切片和缓存，**必须落在 `projects/<项目名>/` 对应的子目录内**，严禁在项目根目录创建；
   - 执行 `git add` 前，必须检查 `git status`，确保绝无媒体二进制大文件被意外暂存。
2. **声明式规范优先**：
   - 所有剪辑决策必须收敛在 `projects/<项目名>/edit_spec.json` 中，严禁编写一次性的硬编码 ffmpeg 剪切脚本。
3. **跨平台兼容性**：
   - 编写 Python 代码时，路径处理一律使用 `pathlib.Path`，严禁硬编码 `/bin/ps` 或 macOS 专属绝对路径，保证 macOS 与 Windows 能够无缝双向兼容。
4. **主观审美与 QA 门禁**：
   - 视频不能仅靠“代码跑通无报错”验收；生成后必须通过 `pipeline.verify` 检查全片解码完整度与 EBU R128 响度（推荐 `-16.5 LUFS` 左右），并生成九宫格连环画供用户直观审阅。
