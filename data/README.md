# 素材中心 (Data Directory)

该目录是剪辑流水线的**原始素材输入区**。

> [!NOTE]
> 为避免仓库膨胀，所有多吉字节（GB 级别）的视频大文件（`*.mp4`, `*.mov`, `*.mkv` 等）均已被 [`.gitignore`](file:///Users/luo/Projects/cutcut/.gitignore) 全局排除，不会上传到 Git。

---

## 📁 目录约定

```text
data/
└── raw/                         # 原始实拍摄材区
    ├── desk_setup/              # 示例：桌搭原片素材库 (内附 README.md 规格说明)
    └── <你的新素材文件夹>/         # 新增拍摄素材时，直接在此新建文件夹存放
```

## 🎬 如何使用？
1. **新建素材集**：在 `data/raw/` 下为你的拍摄主题新建一个文件夹，例如 `data/raw/camping/`、`data/raw/coffee/`；
2. **拷入视频**：将手机或相机拍摄的原始文件（横屏、竖屏、4K 均可）直接放进去；
3. **运行流水线**：
   ```bash
   python3 -m pipeline.cli auto \
     --source data/raw/coffee \
     --prompt "咖啡馆沉浸式制作流程，快节奏" \
     --out-dir projects/coffee-douyin-v01
   ```
