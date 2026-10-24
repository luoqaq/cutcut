# CutCut AI 视频剪辑流水线 (`pipeline/` + `studio/`)

面向实拍短视频（抖音 / 小红书 9:16 竖屏成片）的 **声明式多模态 AI 剪辑工作流**。采用 **双出口架构**：
- **出口 A（Remotion 高颜值成片直出）**：支持居中宽画幅电影框（`cinema_frame`）、上下三联屏（`triptych`）、上下双联屏（`split_2`）、沉浸竖屏卡（`full_bleed`）混合排版，带平滑关键帧缩放、杂志感顶部角标、高亮关键词双层字幕与自动闪避（Ducking）混音。
- **出口 B（剪映专业版可编辑工程）**：同步导出标准 `captions.srt`、`timeline.fcpxml` 以及适配 Mac 剪映专业版 11.4 的原生草稿包（含独立视频轨、独立 BGM 轨、独立降噪原声轨与原生可编辑文本字幕），支持一键注册进剪映首页二次微调。

---

## 五阶段架构

1. **Stage 1 · 多模态场记扫描 (`pipeline/ingest.py`)**
   - 自动解析横竖屏与旋转矩阵（兼容相机 4K XAVC 与手机竖屏 HEVC）
   - 逐秒音频特征分析：识别清脆互动声（`[CRISP]`：敲击键盘声、宠物哼唧声）与环境噪音尖峰（`[NOISE!]`：窗外鸣笛等）
   - 输出高密度时间码+锐度评分+音量标记场记板（`*_sheet_*.jpg`）与 `catalog.json`

2. **Stage 2 · 剪辑协议与防呆质检 (`pipeline/schema.py`)**
   - 统一由 `edit_spec.json` 驱动分镜、画幅、推拉焦点、字幕与多轨声音
   - 自动拦截同源时间倒流跳切（Jump Cut）、源时长越界、字幕重叠与过长字幕空窗期

3. **Stage 3 · 切片精裁与音频自动闪避混音 (`pipeline/prepare.py`)**
   - 硬件加速帧精确切片、色彩统一（`bt709`）与自动扶正旋转方向
   - 对选中保留的原声片段执行带通滤波与 FFT 降噪（`highpass` + `afftdn`），并在原声出现区间对 BGM 执行平滑包络闪避（Sidechain-style Ducking），最终按 `-15.5 LUFS` 响度标准化输出

4. **Stage 4A & 4B · 双出口渲染 (`studio/` + `pipeline/export_jianying.py`)**
   - `studio/`：Remotion 4.0 React 合成引擎渲染高清 `1080×1920` H.264 成片
   - `export_jianying.py`：生成 `jianying_export/`（`native_draft/` + `install_to_jianying.py` + `timeline.fcpxml` + `captions.srt`）

5. **Stage 5 · 成片验收单 (`pipeline/verify.py`)**
   - 全片解码完整性校验、EBU R128 响度复核、逐镜头中点 9:16 视觉验收板（`qa_portrait_sheet.jpg`）与高清封面图提取

---

## 常用命令

```bash
# 1. 扫描新拍摄的素材目录，生成多模态场记板与 catalog.json
python3 -m pipeline.cli scan --source 桌搭 --out edits/my-edit/analysis --interval 4.0

# 2. 单独校验 edit_spec.json 分镜表合法性
python3 -m pipeline.cli validate --spec edits/pet-douyin-v02/edit_spec.json --source 桌搭

# 3. 一键执行全流水线（质检 -> 切片与混音 -> 导出剪映工程 -> Remotion 渲染 MP4 -> 生成 QA 验收单）
python3 -m pipeline.cli build --spec edits/pet-douyin-v02/edit_spec.json --source 桌搭 --studio studio

# 4. （可选）退出剪映后，将生成的原生多轨草稿一键导入剪映专业版首页（自动备份索引）
python3 edits/pet-douyin-v02/jianying_export/install_to_jianying.py
```
