# Remotion Studio 视频渲染套件

本目录是 CutCut 的**代码化视觉渲染引擎**，基于 [Remotion](https://www.remotion.dev/) (React 18 + TypeScript) 构建。

---

## 🎨 核心组件结构

```text
studio/src/
├── layouts/                     # 核心画幅版式
│   └── ShotRenderer.tsx         # cinema_frame(电影画幅), triptych(三联屏), split_2(双分屏), full_bleed(全屏)
├── components/                  # 动效与视觉元素
│   ├── VideoSlot.tsx            # Ken Burns 平滑推拉运镜、焦点裁剪
│   └── Overlays.tsx             # 磨砂玻璃动态字幕、高亮关键词、工位头部标签
├── EditComposition.tsx          # 统一主合成入口 (接收 active_props.json)
└── Root.tsx                     # Remotion 根配置 (1080x1920 @ 30fps)
```

---

## 💻 本地预览与调试

在本地可以启动 Remotion 的图形化调试器，实时预览每一帧画面与 CSS 动画效果：

```bash
cd studio
npm install
npm start
```
> 浏览器会自动打开 `http://localhost:3000`，可以自由拖拽时间滑块、审查文字样式与多联屏排版。
