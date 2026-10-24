# 剪映本机操作验证 · 2026-10-22

结论：已通过真实剪映界面完成一次素材导入、时间线分割、片段删除和本地视频导出。此次验证覆盖基础操作，不代表复杂长片、会员 AI 功能或无人值守批量剪辑已验收。

## 本机环境

- 应用：`/Applications/VideoFusion-macOS.app`，窗口名称“剪映专业版”。
- Bundle ID：`com.lemon.lvpro`。
- `CFBundleShortVersionString`：`11.3.13090`；`CFBundleVersion`：`11.4.0-beta5`。两个字段不同，保留原值，不合并成未经核实的版本号。
- 首页显示账户已登录，SVIP 有效期至 `2027.08.04`。本次未消费付费 AI 点数、未验证每项会员权益。
- 控制方式：Codex Computer Use，通过原生菜单、可访问性控件及画面坐标操作。

## 已执行步骤

1. 从 `桌搭/C0408.MP4` 的第 10 秒截取 6 秒，使用 FFmpeg 生成独立输入 `input-6s.mp4`（1280×720、25 fps、H.264/AAC）。原始视频未改动。
2. 剪映中新建独立草稿“10月22日”，导入该输入。
3. 使用素材右键菜单“根据选中素材新建时间线”，创建“时间线02”，素材进入主轨道。
4. 将播放头定位到 `00:00:03:00`，通过“编辑 → 分割”切成两段，界面显示各 3 秒。
5. 选中后半段并删除，导出面板显示剩余时长 3 秒。
6. 在剪映中导出至本验证目录；界面明确显示“导出成功”。云空间自动备份未勾选，未点击发布。
7. 使用 ffprobe 检查落盘文件，并通过 FFmpeg 完整解码验证。

## 导出结果

- 文件：`10月22日.mov`。
- 大小：2,716,906 字节。
- 时长：`3.000000` 秒。
- 视频：HEVC，1280×720，30 fps。
- 音频：AAC。
- 完整解码：退出码 `0`，无错误输出。

复核命令：

```sh
ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate -of json '/Users/luo/Projects/cutcut/verification/jianying-2026-10-22/10月22日.mov'
ffmpeg -v error -i '/Users/luo/Projects/cutcut/verification/jianying-2026-10-22/10月22日.mov' -f null -
```

## 操作限制与未验证项目

- Qt 自绘控件的可访问性动作并非都有效。多次控件点击未产生操作，改用原生菜单或画面定位才完成，因此当前不宜承诺无人值守批量稳定性。
- 素材拖入空轨道没有在本轮成功；素材右键菜单的新建时间线方法成功。不能概括为所有拖拽操作都不可用。
- 本轮最终使用剪映默认 MOV 导出；MP4 菜单切换未验证成功。
- 未验证自动字幕、智能粗剪、会员素材、AI 消耗、转场、调色、复杂多轨和 4K 长片导出。
- 自建测试草稿中的 `draft_info.json`、`draft_meta_info.json` 不能按普通 JSON 解析。此项只能说明格式不是明文 JSON，不单凭这个现象断定加密实现。
- 未安装第三方剪映 MCP、skill 或新外部依赖，未更改用户已有草稿。
- 测试草稿由剪映自动保存在 `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/10月22日`，包含空的“时间线01”和验证用“时间线02”。

