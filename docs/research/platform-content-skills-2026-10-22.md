# 抖音 / 小红书内容工作流与 Agent Skills 核查

核查日期：2026-10-22。范围：帮助现有实拍素材完成选题、对标、脚本、镜头结构、标题封面和复盘的社区工作流。只读查阅原作者仓库、`SKILL.md`、脚本和作者演示；未安装、调用付费接口、登录平台、发布内容或操作本机应用。

**结论：有能借用的工作流，尚无本轮可证实的“稳定制造爆款”方案。最贴近本项目的是：借用灵造的对标研究与 Easel 的视频分镜、复盘方法，由现有剪映执行成片。OpenStoryline 可单独测试素材理解与叙事组织。** 这是一项组合建议，属于推断，不是已实测集成；OpenStoryline 与剪映可编辑工程是否互通尚未验证。

四个候选都面向中文内容，不能笼统归为只做英语 TikTok 的产品；但各自覆盖的环节差别很大。**图文“爆款复刻”、字幕切片、真正看懂实拍画面是三种不同能力。**

## 候选对照

下表的“有”仅表示源码或工作流实际包含相应入口，不能当作本机验收通过。

| 候选 | 选题 / 对标与内容策划 | 公开数据或本人后台 | 实拍素材理解 / 剪辑执行 | 发布与复盘 | 本项目判断 |
|---|---|---|---|---|---|
| [灵造 Lingzao][L0] | 账号筛选、笔记拆解、标题封面、关键词、口播 / Vlog 改写 | 有服务端 API 调用代码；真实返回质量本轮未调用 | 公开链接文案提取；不能据此认定已逐秒看懂视频；无本地时间线剪辑器 | 复盘接收后台截图和原内容；公开指标可走付费接口；未发现发布执行器 | **优先借用研究和复盘流程**；完整实时研究另需服务积分 |
| [Xiangyu-CAS 小红书运营 Skill][X0] | 账号定位、首页分析、选题、结构仿写 | OpenClaw 浏览器登录后读页面 / DOM；不是内置数据 API | Viral Copy 重点是图文；视频上传流程不等于素材理解或剪辑 | 浏览器发布与评论 SOP；Markdown 知识库；默认停在发布按钮前 | 可借用小红书运营结构，**不作为现有实拍视频的主引擎** |
| [ZJU-REAL Easel][E0] | Discover → Plan → Produce → Publish → Attribute；具体视频脚本和对标剪辑拆解 | 热榜为第三方公益 API；有本人小红书 / 抖音后台读取脚本 | 有字幕、音频 / 转录选高光、FFmpeg 执行；部分模块只适合英语口播 | 有发布脚本、账号数据读取、快照、确定性聚合与 LLM 解读 | **最完整的研究型工作台候选**，先借用少数方法；不能仅因功能多就视为成熟交付方案 |
| [FireRed-OpenStoryline][F0] | 素材描述 → 筛选 → 叙事分组 → 旁白 / 标题 | 无本轮发现的平台选题数据 / 账号表现接入 | 真正包含视觉素材理解、镜头筛选分组、时间线规划和渲染代码 | 可把满意的剪辑逻辑保存为个人 Skill；未发现发布 / 账号数据反馈闭环 | **最贴近“我有实拍素材，帮我组织出故事”**；平台运营需要另补 |

## 1. 灵造：比较贴近中国平台的研究与复盘流程

**事实：不是只有提示词。** 轻量子技能是可单独借用的 Markdown 方法；完整 CLI 会请求灵造服务的搜索、账号、笔记详情、评论与视频文案提取接口。需要灵造 API Key 和积分；客户端代码没有要求用户提供自己的抖音 / 小红书登录 Cookie。其服务如何采集、实际覆盖率和返回质量，本轮未验证。[API 客户端][L1] · [主 Skill][L2]

值得保留的是对标筛选：检查账号近期仍在更新、近期有相对突出的作品、内容形式与资源门槛适合自己，要求列出证明作品。它不是“找十条点赞最多的作品”就结束。[对标筛选规则][L3]

**事实：单条视频拆解明确设有证据边界。** 只拿到标题、封面和文案时，不应声称看过具体秒数；看镜头和剪辑节奏需要画面 / 截图等可见线索。轻量拆解支持口播、Vlog 和拍摄节奏，但这属于分析指令，不等于具备自动视频视觉分析实现。[单条拆解工作流][L4] · [轻量拆解 Skill][L5]

复盘会把后台指标与标题、封面、开头、主体和观众承诺对应，要求提出下一次修改 / 实验。它接收 24 小时、48 小时、7 天的数据；这些是作者的复盘窗口建议，不是平台官方流量规则。[复盘 Skill][L6]

**判断：** 最适合作为本项目选题和对标研究的参考包。可先用用户提供的链接、截图、数据运行轻量方法，待证明研究确实能改变选题，再决定是否购买数据积分。没有依据声称充值后爆款概率会提高。

## 2. Xiangyu-CAS：小红书浏览器运营 SOP，视频创作能力有限

**事实：** 核心交付是主 Skill、参考流程、人设和知识库；依靠 OpenClaw 浏览器读取平台页面，第一次需要扫码登录。流程会从同题材互动内容提取标题、钩子、角度和评论信号，然后结合账号定位形成选题。[主 Skill][X1] · [README][X0]

其 Viral Copy 明确输出封面 / 配图、标题、正文、话题，默认使用封面风格参考；还列出轮播图 DOM 选择器和 Nano Banana 2 生图步骤。**因此不能把“爆款复刻”理解成自动拆解并重新剪出一条实拍视频。** 生图需要额外模型服务配置；README 提到 Gemini API Key，未独立核实当前额度或价格。[Viral Copy 原文][X2]

发布支持视频 / 图文 / 长文类型，默认在最终发布按钮前停手；这证实有上传 SOP，不证明具备视频语义分析。知识库用于保存 pattern、topic、review 等记录。[发布及沉淀规则][X1]

**效果证据：作者声明。** README 展示过账号诊断结果和发布 / 回复示例，但高赞样本是被分析账号原有内容的表现，不能证明使用 Skill 后获得相应增长。未发现独立对照、持续账号实验或可复验的增长数据。

## 3. Easel：覆盖最完整，但要拆开看“方法、工具、数据”

**事实：** 仓库并非占位概念，包含实际可执行媒体工具、前端、发布与读取代码。作者演示的是工作台可产出图文和视频，并非已经证明平台增长效果。[原作者说明][E0]

几个最有用的具体模块：

- **对标拆成可执行镜头表。** `edit-anatomy.md` 要求同时看转录与关键帧，逐段记录镜头、切点、屏幕文字、字幕样式、运动和声音，再提炼 3–5 个可复用方法，交给剪映等编辑器执行。这个产物比“剪得高级一点”具体得多。文中关于爆款原因和前两秒作用的断言是作者方法论，本轮不把它当平台实验证据。[剪辑拆解参考][E1]
- **分秒脚本。** `video-script` 产出 3 个开头变体、时间码、口播、字幕、画面和封面。里面的 Hook / 质量分是模型按自定义标尺评分，**不能当作爆款概率**；固定语速、统一互动优先级等也要按本素材与平台数据调整。[视频脚本 Skill][E2]
- **复盘有计算层。** `skill-publish-analytics` 从发布日志和快照聚合表现，报告缺失覆盖率与样本量，明确相关性不能证明因果。它的互动综合分是项目自定义权重，不能说是抖音 / 小红书算法公式。[分析 Skill][E3]
- **部分真实数据读取已写代码。** `account_stats.py` 复用独立持久登录态，包含无头 Playwright、本人小红书创作中心接口与抖音后台页面字段读取。静态源码存在，不代表在当前账号上已经跑通，也没有据此确认能自动取得每条视频完整留存曲线。[账号数据代码][E4]

需要准确区分：`skill-data-tracker` 自身接受用户输入 / 快照并计算；自动读取由另一层完成。热榜模块调用 60s / xxapi 第三方公益服务，返回的热点并不等于适合本账号的需求。[快照 Skill][E5] · [热点 Skill][E6]

**适用边界：** `video-highlights` 的“内容选高光”是先 ASR 转录再由 Agent 选语义段，默认模式则按音量能量找点，适合直播 / 口播；不宜把音量高直接当剧情好或视觉好。该文件明确另一个 `clipify` 更偏英文口播，本模块可用于中文。[高光 Skill][E7]

完整工作台引入 Python、Node、OpenClaw、FFmpeg、Playwright；通用模型需要可用配置，AI 视频 / 音乐 / 云配音按使用能力配置服务。**判断：** 本项目先借用镜头表、视频脚本和复盘结构更划算，暂不因“覆盖全部环节”就安装整套或自动经营账号。

## 4. OpenStoryline：真正补上素材理解，但不是平台增长 Agent

**事实：** 默认流程明确串起素材加载、镜头切分、内容理解、筛选、叙事分组、旁白、音乐、时间线和渲染。内容理解节点把本地图片 / 视频片段交给模型，生成描述与画面质量分，不是仅靠文件名推测内容。[默认 Skill][F1] · [视觉理解实现][F2]

画面提示词涵盖主体动作、场景、构图、环境、情绪和画质。排序提示词可依据用户意图采用 Hook → 核心展示 → 氛围 → 收尾，也可按场景和动作连续性分组。这个排序是生成式启发规则，尚不能推导为某个平台验证过的留存优化。[视觉提示词][F3] · [叙事排序提示词][F4]

**事实：** 支持满意后保存剪辑逻辑为 Skill，复用节奏和表达风格；有中文界面 / 提示词，作者明确展示 Vlog 和现有素材流程。[使用指南][F5]

需要 LLM / VLM 模型配置；云模型、TTS、可选 AI 转场可能有独立费用。Pexels Key 仅用于额外素材检索，已有自己的素材不必据此增加图库依赖。源码与作者演示证明能力设计存在，**本轮未验收本机兼容、成片质量或剪映工程互通**。[配置文件][F6]

**判断：** 可后续做小样对照：同一批自有素材，用手工 / 当前 Agent 方案与 OpenStoryline 各做一版，比较镜头选取、事实保真、叙事和修改成本。没有必要把平台发布接进这个小样。

## 证据强弱与建议

**本轮未找到这四个候选具有独立、可复验的抖音 / 小红书账号增长或对照试验。** 已看到的是作者演示、作者测试记录、工作流文件和实现代码。前两类可证明作者尝试过；后两类可证明能力入口存在；都不足以证明“稳定成为爆款”。搜索榜单、Star、安装次数不作为内容效果证据。

实际值得借用的能力组合是：

1. **研究：** 从同赛道、同形式、相近资源条件的近期作品中取样，保留链接、发布时间、公开互动和相对表现；同时看普通作品，避免只看幸存的爆款。灵造的筛选规则可作为起点。
2. **创作：** 先建立自有素材镜头清单，再输出两个平台分别适用的观众承诺、开头、分镜和封面标题。Easel 的镜头表可直接交给剪映执行；素材语义组织可以另试 OpenStoryline。
3. **学习：** 发布后把成片版本与真实后台数据对应，比较同账号基线；每轮只优先检验一个清晰变化。Easel 的统计与灵造的“内容 ↔ 指标”诊断可结合，但不把相关关系写成唯一成因。

若后续沉淀为本项目 Skill，建议固定交付 `素材清单 → 对标证据 → 两平台创作方案 → 时间码镜头表 → 成片与版本记录 → 数据复盘及下一实验`。这会比安装一个名叫“爆款”的通用提示词更容易验收，仍需通过实际内容验证效果。

## 核查快照与候选筛选

通过 GitHub 仓库 API 获取的默认分支最新提交（用于避免 README 后续漂移）：

| 仓库 | 当前读取提交 | 提交时间（UTC） |
|---|---|---|
| atian-create/lingzao-skill | `1727b3a1` | 2026-07-02 |
| Xiangyu-CAS/xiaohongshu-ops-skill | `5b0b80b7` | 2026-03-19 |
| ZJU-REAL/Easel | `3f1d4fb8` | 2026-10-21 |
| FireRedTeam/FireRed-OpenStoryline | `c9e94521` | 2026-07-31 |

另外定位了 [wenziai/wenzi-xiaohongshu-workflow](https://github.com/wenziai/wenzi-xiaohongshu-workflow)，原仓库介绍以账号定位、标题、真人化改稿、图文规划和复盘为主。为控制范围，未作第五个深入候选；不能据此评价其实际效果，也未安装。

[L0]: https://github.com/atian-create/lingzao-skill/tree/1727b3a1acf83aa6754d08f0e3552be8550c5cb9
[L1]: https://github.com/atian-create/lingzao-skill/blob/1727b3a1acf83aa6754d08f0e3552be8550c5cb9/scripts/lingzao_client.py
[L2]: https://github.com/atian-create/lingzao-skill/blob/1727b3a1acf83aa6754d08f0e3552be8550c5cb9/SKILL.md
[L3]: https://github.com/atian-create/lingzao-skill/blob/1727b3a1acf83aa6754d08f0e3552be8550c5cb9/playbooks/benchmark-account-discovery-quality-gate.md
[L4]: https://github.com/atian-create/lingzao-skill/blob/1727b3a1acf83aa6754d08f0e3552be8550c5cb9/playbooks/single-note-breakdown-workflow.md
[L5]: https://github.com/atian-create/lingzao-skill/blob/1727b3a1acf83aa6754d08f0e3552be8550c5cb9/skills/xhs-note-breakdown/SKILL.md
[L6]: https://github.com/atian-create/lingzao-skill/blob/1727b3a1acf83aa6754d08f0e3552be8550c5cb9/skills/xhs-postpublish-review/SKILL.md
[X0]: https://github.com/Xiangyu-CAS/xiaohongshu-ops-skill/blob/5b0b80b7261396955de0494df18182f2401cabc4/README.md
[X1]: https://github.com/Xiangyu-CAS/xiaohongshu-ops-skill/blob/5b0b80b7261396955de0494df18182f2401cabc4/SKILL.md
[X2]: https://github.com/Xiangyu-CAS/xiaohongshu-ops-skill/blob/5b0b80b7261396955de0494df18182f2401cabc4/references/xhs-viral-copy-flow.md
[E0]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/README.md
[E1]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/skills/builtin/video-strategy/references/edit-anatomy.md
[E2]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/skills/builtin/video-script/SKILL.md
[E3]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/skills/builtin/skill-publish-analytics/SKILL.md
[E4]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/skills/shared/scripts/account_stats.py
[E5]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/skills/builtin/skill-data-tracker/SKILL.md
[E6]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/skills/builtin/skill-trending-topics/SKILL.md
[E7]: https://github.com/ZJU-REAL/Easel/blob/3f1d4fb8b99694f7231ee97163b637df89b50d3b/skills/builtin/video-highlights/SKILL.md
[F0]: https://github.com/FireRedTeam/FireRed-OpenStoryline/tree/c9e945215586f45c12a61c1951ee9a8e9c43a027
[F1]: https://github.com/FireRedTeam/FireRed-OpenStoryline/blob/c9e945215586f45c12a61c1951ee9a8e9c43a027/.storyline/skills/default_editing_workflow_skill/SKILL.md
[F2]: https://github.com/FireRedTeam/FireRed-OpenStoryline/blob/c9e945215586f45c12a61c1951ee9a8e9c43a027/src/open_storyline/nodes/core_nodes/understand_clips.py
[F3]: https://github.com/FireRedTeam/FireRed-OpenStoryline/blob/c9e945215586f45c12a61c1951ee9a8e9c43a027/prompts/tasks/understand_clips/zh/system_detail.md
[F4]: https://github.com/FireRedTeam/FireRed-OpenStoryline/blob/c9e945215586f45c12a61c1951ee9a8e9c43a027/prompts/tasks/group_clips/zh/system.md
[F5]: https://github.com/FireRedTeam/FireRed-OpenStoryline/blob/c9e945215586f45c12a61c1951ee9a8e9c43a027/docs/source/zh/guide.md
[F6]: https://github.com/FireRedTeam/FireRed-OpenStoryline/blob/c9e945215586f45c12a61c1951ee9a8e9c43a027/config.toml
