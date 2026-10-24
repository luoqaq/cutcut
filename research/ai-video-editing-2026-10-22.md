# AI 视频剪辑方案与 Skills 调研

调研日期：2026-10-22。仅核对官方文档、原作者仓库、源码与发布记录；本报告不包含本机剪映验收结果，也没有安装或连接下列工具。

## 结论与选择

**已有剪映会员，先用剪映做实际素材的小样，暂时没有必要另买订阅。** 要让 Codex 长期代剪，优先考虑两条路线：

- **保留剪映可编辑工程：**剪映桌面操作；需要批量编排时，再试 Mac 专用的 Jianying Local MCP。后者仍是实验性草稿生成器，必须在目标剪映版本实际打开、修改和导出后才算通过。
- **交给 Codex 本地制作并导出：**Remotion 官方 Agent Skills。适合素材拼接、字幕、片头、图形动画和固定栏目，成片可重复生成；选镜头、讲故事仍依赖模型判断与人工审片。

口播、访谈、播客长视频切片另看 Descript 与 OpusClip。若愿意增加专业软件，**DaVinci Resolve Studio 21.1 已有官方原生 MCP，并明确支持 Codex**，不必优先寻找第三方桥接器。

另有一个容易被旧文章漏掉的新变化：**CapCut 官网现在提供官方 CapCut × Codex 插件。**它属于国际版产品，不能据此推断能控制国内剪映，或使用现有剪映 SVIP 权益。[官方页面](https://www.capcut.com/tools/capcut-x-codex)

## 七个值得关注的方案

| 方案 | 最合适的素材 / 工作 | Agent 接入与输出 | 判断 |
|---|---|---|---|
| 剪映 / CapCut 官方能力 | 实拍短视频、口播、现有剪映工作流 | 剪映内 AI 工具；国际版有官方 Codex 插件 | 先复用现有会员；两款产品分开验证 |
| Jianying Local MCP | Mac 上多段实拍、图片、字幕、多轨编排 | 本地 MCP 生成剪映草稿；在剪映检查和导出 | 最贴近现有软件，但仍实验性 |
| Remotion 官方 Skills | 本地素材编排、字幕、包装、动画、批量栏目 | Codex 写 React 视频工程，Studio 预览，CLI 渲染 | 最值得实测的本地 Skill 路线 |
| Descript + Underlord | 口播、访谈、播客、课程、录屏 | 官方 API / CLI / MCP；可编辑项目与发布后下载 | 产品完整；云处理、另用其额度 |
| OpusClip | 长视频切片、短口播包装、参考风格剪辑 | 官方 Skills / CLI / MCP；AI Producer 插件 | 切片方向成熟；不同入口限制不同 |
| DaVinci Resolve Studio | 长期专业实拍、多机位、调色、交付 | 21.1 起官方原生 MCP，含渲染工作流 | 专业软件成熟；Agent 集成较新 |
| Premiere | 已在 Adobe 工作流中的素材整理与粗剪 | 官方 AI Assistant beta；UXP 编程接口 | 主编辑器成熟；对话代剪仍 beta |

### 1. 剪映与 CapCut：有 AI，也已有官方 Codex 产品

剪映官网列有智能剪口播、智能解说粗剪、素材智能搜索、降噪、人声分离、智能调色等能力；这些适合在现有会员内先试。官网能力介绍不等于公开的桌面时间线编程接口，本次未找到国内剪映向普通用户开放、可直接调用的官方剪辑 / 渲染 API 文档。[剪映官网](https://www.capcut.cn/)

CapCut × Codex 官方页面明确描述上传素材或草稿、生成初稿、对话修改时间线、字幕与音乐，并可打开编辑器继续调整。页面说明面向桌面任务，地区、账号和应用版本会影响可用性，当前美国尚未开放。[CapCut × Codex](https://www.capcut.com/tools/capcut-x-codex)

**证据边界：**官网提供的 [官方安装 SKILL.md](https://sf16-sg.tiktokcdn.com/obj/eden-sg/962370eh7nupenuhbo/capcut_codex_plugin/SKILL.md) 在本次环境中无法取得正文：浏览工具不可达，Python 与 curl 均遇到 TLS EOF。因此只能确认官网提供了安装与授权入口；尚未核实其包内容、Mac 安装细节、完整定价、配额及素材在客户端和云端间如何处理。不能称为已安装或已接通，也不宜将其宣传的免费体验理解成无限免费。

剪映会员能否抵扣 CapCut：未找到 CapCut 自己的当前会员条款支持互通；ASUS 与 CapCut 联合活动的官方 FAQ 对两款会员是否通用回答为否。它是合作方活动资料，不代替当前账号权益页，实际接入仍需核对。[合作活动 FAQ](https://www.asus.com/ch-en/support/faq/1053490/)

### 2. Jianying Local MCP：Mac 剪映最贴近目标的社区候选

原作者仓库提供 22 个本地 stdio MCP 工具，可编排镜头、多轨、SRT 与原生文字、关键帧和批量修订。最新 release 为 **v0.3.0，2026-09-10**。仓库有真实剪映工程与样片记录，而不只有接口演示。[仓库](https://github.com/Capricornus-joe/jianying-local-mcp) · [release](https://github.com/Capricornus-joe/jianying-local-mcp/releases/tag/v0.3.0)

但作者明确把 Mac 兼容性标为实验性：历史原生样片验证于剪映 **11.4.0**；0.3 的程序与 stdio 回归不能替代新增接口的完整原生导出验收。它只维护自己创建的计划，不回读加密草稿，剪映内手改不会同步回计划，也没有可靠的 Mac 自动导出。[兼容性说明](https://github.com/Capricornus-joe/jianying-local-mcp/blob/main/docs/compatibility.md)

**建议：**需要保留剪映工程时值得试一个短项目。新建、发布、原生打开、改一句字幕、导出与重复导出都成功后，再扩大素材规模。它是 MCP 服务，本仓库未发现可直接安装的 `SKILL.md`。

同名生态不要混用：

- **GuanYixuan/pyJianYingDraft**：0.3.1 于 2026-10-14 发布，新版剪映 10.8 草稿生成有验证；模板回读通常要另接 `fallback_loader`。README 明写 Mac/Linux 不支持自动导出，生成草稿仍需 Windows 剪映导出；新版 7+ 的自动导出也通常不可用。不能把“剪映 6+ 加密”误写为“所有新版都无法生成新草稿”。[README](https://github.com/GuanYixuan/pyJianYingDraft) · [0.3.1](https://github.com/GuanYixuan/pyJianYingDraft/releases/tag/0.3.1)
- **GuanYixuan/pyCapCut**：0.0.4 于 2026-10-16 发布，面向国际版；README 要求在 Windows CapCut 打开并手动导出，加密模板不支持。它不是本机 Mac 剪映自动化的替代品。[README](https://github.com/GuanYixuan/pyCapCut) · [0.0.4](https://github.com/GuanYixuan/pyCapCut/releases/tag/0.0.4)
- **aoguai fork**：另有新版加密草稿支持说明，但要求 Windows 64 位 Python 与本机剪映环境，声称验证范围为 10.3.0–10.6.5；不能套用于 Mac。[fork README](https://github.com/aoguai/pyJianYingDraft/blob/main/README.md)

### 3. Remotion：优先试的官方 Skill

Remotion 自己维护 `remotion-dev/skills`，明确支持 Codex。仓库真实包含 `remotion-create`、`remotion-captions`、`remotion-studio`、`remotion-render` 等 `SKILL.md`，当前技能头版本为 **4.0.537**；2026-10-19 仍有提交。[官方技能文档](https://www.remotion.dev/docs/ai/skills) · [原作者仓库](https://github.com/remotion-dev/skills) · [近期提交](https://github.com/remotion-dev/skills/commit/039e8a2fc78b67efc228d5645367838b85818a1c)

官方入门直接给出“把 Downloads 中的视频放上时间线”“给本地视频加字幕”的提示例子；有 Studio 可视预览和 `npx remotion render` 成片出口。并非只能做代码动画。[本地素材示例](https://www.remotion.dev/docs/your-first-video) · [渲染 Skill](https://github.com/remotion-dev/skills/blob/main/skills/remotion-render/SKILL.md)

**判断：**工具链可重复、可检查，适合 Codex 工作；它不天然提供剪映的全部特效、素材库与调色能力，也不能保证自动选镜头有叙事品味。个人当前可免费用于制作视频，较大商业组织需检查 Company License。[许可证](https://www.remotion.dev/license)

后续若决定试用，官方安装入口是 `npx skills add remotion-dev/skills`；本次未执行。

### 4. Descript：偏内容表达的云端剪辑

Underlord 可通过转录稿做去赘词、音频清理、字幕、场景与 highlight reel。官方现有 API、CLI 和 MCP，支持本地上传与 URL 导入；MCP 使用 OAuth，按一个 Drive 授权，并使用该账号的媒体分钟和 AI credits。[API 能力与限制](https://help.descript.com/api-and-mcp/api) · [MCP 文档](https://help.descript.com/api-and-mcp/mcp)

**容易误读的导出限制：**可以先发布为 Descript web link，再取得 MP4 的签名下载地址；不支持“不发布就直接下载渲染文件”的 API 路线。官方营销页表述较笼统，应以此帮助文档为准。[官方限制](https://help.descript.com/api-and-mcp/api#known-limitations)

适合口播与访谈；中文转录、方言、字幕断句及实际成片质量仍应拿用户自己的素材验证。已有剪映会员不会自动提供 Descript 额度。本次未连接服务。

### 5. OpusClip：把三条路线区分开

- **ClipAnything / 传统 OpusClip：**从长视频找片段、重构为社媒短片；官方有 API 与 MCP。[官方产品](https://www.opus.pro/clipanything)
- **`opus-pro/opus-skills`：**原作者维护的真正 Agent Skills，包含剪片 CLI、`copy-video-style` 与媒体生成。`copy-video-style` 可本地分析参考片并本地剪辑，OpusClip 视频理解为可选付费增强；依赖本地 FFmpeg 等工具。仓库 2026-10-16 仍更新，README 明标 beta，API 价格未必等于网页价格。[官方技能仓库](https://github.com/opus-pro/opus-skills)
- **AI Producer：**新的一体化口播剪辑产品，有官方 Codex 插件及多份 `SKILL.md`。只支持单人对镜头讲话；当前限制为 ≤ 5 分钟、≤ 1.99 GB，尚不支持多机位与录屏；导出最高 1080p / 30 fps。Agent 入口目前限部分账号，且消耗 OpusClip credits。[使用限制](https://producer.opus.pro/docs/getting-started) · [官方插件源码](https://github.com/opus-pro/ai-producer-plugin)

**技能文件实证：**本次核对的 `main` 为 `68e72c643a3a8176416fdd4810cf12047127e0c8`，递归 [GitHub API tree](https://api.github.com/repos/opus-pro/opus-skills/git/trees/68e72c643a3a8176416fdd4810cf12047127e0c8?recursive=1) 未截断，确实包含三份 `SKILL.md`。另外两份嵌套在 `skills/opusclip/skills/` 下，并非与 `opusclip` 同级：[copy-video-style 原始文件](https://raw.githubusercontent.com/opus-pro/opus-skills/68e72c643a3a8176416fdd4810cf12047127e0c8/skills/opusclip/skills/copy-video-style/SKILL.md) 与 [opusclip-media-generation 原始文件](https://raw.githubusercontent.com/opus-pro/opus-skills/68e72c643a3a8176416fdd4810cf12047127e0c8/skills/opusclip/skills/opusclip-media-generation/SKILL.md) 均返回 HTTP 200，且 YAML `name` 分别匹配上述名称。

**建议：**长访谈批量切片优先测试传统 OpusClip；短口播可试 AI Producer。旅行、生活记录等多段实拍不能直接套用其单人口播产品承诺。

### 6. DaVinci Resolve Studio：最值得留意的专业路线

2026-09-08 的 **21.1** 正式加入原生 MCP；官方明确支持 Claude、Claude Code 与 ChatGPT Codex。当前官方下载元数据列出的最新维护版为 **21.1.1，2026-10-02**。[官方发布稿](https://www.blackmagicdesign.com/media/partial/release/20260908-03) · [官方下载元数据](https://www.blackmagicdesign.com/api/support/us/downloads.json)

已直接读取官方 **21.1 Reference Manual 第 4318 页**：明确是 Studio，入口 `File > Setup AI Assistants`，列有时间线分析、素材命名、调色、9:16 重构与多格式渲染示例。官方 release notes 同时确认 native MCP、advanced scripting 需 Studio；Mac 要 macOS 15+ 与 Apple Silicon。[手册 p.4318](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_21.1_Reference_Manual.pdf?_v=1788850812000#page=4318) · [21.1 官方 release notes](https://www.blackmagicdesign.com/support/content/readme/baf7c071c0524fbf8ccc961925c9f443)

**判断：**原生工程、媒体管理、调色与交付基础成熟，官方 Agent 接入比第三方私有格式桥接更值得长期投入；集成本身刚上线不久，不能保证任意创意要求都能一键完成。需要额外 Studio 许可，现有剪映会员不覆盖。

### 7. Premiere：已有 Adobe 订阅再考虑

官方 AI Assistant 自 2026 年公开 beta，能整理素材、生成转录、找场记板、标记及组装 stringout / 初剪，修改留在可编辑项目并进入 Undo / History。Adobe 明确说这是早期 public beta，不建议直接用于客户工作。[官方概览](https://helpx.adobe.com/premiere/desktop/premiere-ai-assistant/overview.html)

另有官方 UXP API，可编程访问 Premiere 功能，但 UXP 是开发接口，不能直接等同于装一个通用 Skill 就会自动创作成片。[官方 UXP](https://developer.adobe.com/premiere-pro/uxp/)

**建议：**已在 Adobe 流程内可试；仅为了目前的 AI 代剪需求，不优先新增订阅。

## 其他候选与生成式视频

**FireRed-OpenStoryline** 值得跟踪，但暂不列为成熟首选。原作者项目有对话剪辑、素材理解、MCP、真正的安装 / 使用 `SKILL.md` 和口播粗剪 Skill；README 把其他 Agent 兼容标为实验性，需 Python、模型资源和外部 API 配置。2026-07-31 仍有源码修复，未找到 GitHub 正式 release；这只能证明项目可研究，不能证明本机已能稳定出片。[原作者仓库](https://github.com/FireRedTeam/FireRed-OpenStoryline) · [近期源码提交](https://github.com/FireRedTeam/FireRed-OpenStoryline/commit/c9e945215586f45c12a61c1951ee9a8e9c43a027)

小云雀、即梦等创作 Agent 有生成镜头、脚本与包装能力；小云雀官方也提供本地素材上传、画布裁剪和剪辑。它们适合补镜头和营销创作，**生成式视频能力不等于能准确剪好用户现有实拍素材**。本任务首轮不以购买生成模型积分为前提。[小云雀官网](https://xyq.jianying.com/) · [官方画布手册](https://xyq.jianying.com/tutorials/creation-agent-canvas)

## 最小实测建议

1. **剪映路线：**同一组本地视频制作 15–30 秒小样，确认切点、字幕、音频、原生可编辑对象和导出文件；需要接 MCP 时只在独立新工程测试，记录真实应用版本。
2. **Skill 路线：**用同组素材测试 Remotion 官方 Skills，交付本地 MP4 与可复现工程；审查开头 3 秒、故事顺序、字幕、音乐压人声及多次修改后的可控性。

先比较这两份实际成片，再决定是否值得增加 Descript / OpusClip 云额度或 Resolve Studio 许可。当前未进行这些安装、上传或付费调用。
