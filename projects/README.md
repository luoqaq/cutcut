# 剪辑工程目录 (Projects Directory)

该目录存放具体的**剪辑工程规范与描述文件**。每个子文件夹代表一个独立的成片项目。

---

## 📁 目录规范与文件清单

每个工程文件夹（如 `pet-douyin-v02`）在执行流水线时包含以下内容：

| 文件 / 子目录 | 类型 | Git 追踪？ | 说明 |
| :--- | :--- | :--- | :--- |
| `edit_spec.json` | 核心配置 | ✅ 是 | **声明式剪辑描述文件**（定义镜头分段、版式、缩放、原声与字幕） |
| `analysis/catalog.json` | 元数据 | ✅ 是 | 素材扫描生成的视频规格、音频分贝与高频敲击点特征表 |
| `analysis/*_sheet_*.jpg` | 视觉接触图 | ❌ 否（已忽略） | 自动采样的关键帧多宫格，供 AI/人工观察选镜 |
| `prepared/manifest.json` | 切片清单 | ✅ 是 | 记录切片时长、分辨率与音画对齐信息的元数据清单 |
| `prepared/clips/` | 视频切片 | ❌ 否（已忽略） | 音画归一化预处理切片 |
| `prepared/audio/` | 音频分轨 | ❌ 否（已忽略） | 侧链闪避后的伴奏、环境声母带 WAV |
| `jianying_export/` | 剪映草稿 | ✅ 是 (代码/配置) | 可选导出的剪映专业版原生草稿工程及一键安装脚本 |
| `qa/verification.json` | 质检报告 | ✅ 是 | 包含全片解码状态、EBU R128 响度与 SHA-256 校验和 |
| `qa/qa_portrait_sheet.jpg` | QA 连环画 | ❌ 否（已忽略） | 自动截取每个镜头中点的竖屏长图 |
| `cover.jpg` | 视频封面 | ❌ 否（已忽略） | 自动截取的高清封面图 |
| `*.mp4` | 最终成片 | ❌ 否（已忽略） | Remotion 渲染直出的 1080×1920 竖屏成品视频 |

---

## 🚀 如何使用现有项目进行复刻渲染？

克隆本仓库后，只要将原始素材放入 `data/raw/desk_setup/`，即可一键重新构建该工程：

```bash
python3 -m pipeline.cli build \
  --spec projects/pet-douyin-v02/edit_spec.json \
  --source data/raw/desk_setup
```
