---
name: video-master-pro
description: The house pipeline for cutting a broadcast-look product or brand film straight out of raw factory footage with FFmpeg + Python — no browser, no Remotion, no HyperFrames. Use when making a 30-90 s narrated film: industrial/equipment promos, factory or product showcase, bilingual (CN/EN) subtitled pieces, or when a previous browser-render pipeline failed and the film still has to ship. Portable by default: every path resolves from a flag or an environment variable, fonts are found by alias on Windows/macOS/Linux, both 16:9 and 9:16 come out of the same scripts. Covers scaffolding a project, shot planning, grade and aspect-safe cutting, PIL type overlays with a gradient scrim, edge-tts voiceover, procedurally synthesised royalty-free BGM, per-shot camera drift, progress rail, concat/mux, and the verify gate.
---

# FFmpeg Film Pipeline

一条纯 FFmpeg + Python 的成片流水线。产出可直接交付的 H.264 MP4，全流程无浏览器、
无 Node 渲染、无付费素材。横屏 16:9 与竖屏 9:16 共用同一套脚本。

脚本**不包含任何本机绝对路径**：所有位置按 `命令行参数 → 环境变量 → 当前目录默认` 解析，
字体按别名在全系统查找。换一台机器、换一个盘符、换一个使用者，都不需要改代码。

## 何时用它

- 用户给一批**原始拍摄素材**（工厂、产线、设备、产品），要 30–90 s 成片。
- 需要**中英双语字幕**（同字号）、**英文/中文配音**、**可商用 BGM**。
- 需要横屏 16:9 或竖屏 9:16 的常规投放片。
- 之前用 HyperFrames / Remotion 卡住（Chrome 探针、`missing_gsap_script`），但仍要交付。

**不要用**于：逐字字幕跟踪（走 `embedded-captions`）、纯数据动画（`motion-graphics`）、
文生视频（`video-prompt-guide`）、无拍摄素材的 AI 短片（`moneyprinterturbo-video` /
`pixelle-video`，见「备用链路」）。

## 前置（硬依赖）

| 依赖 | 说明 |
|---|---|
| `ffmpeg` / `ffprobe` | 必须在 PATH，且带 `libx264` + `aac` |
| Python ≥ 3.10 | 运行全部脚本 |
| `numpy`、`Pillow` | 调色统计、字幕卡绘制 |
| `edge-tts ≥ 7.3.1` | 配音；7.2.x 会 403 |
| 一套 CJK 字体 + 一套拉丁字体 | Windows `msyh.ttc`/`segoeui.ttf`，macOS `PingFang`，Linux `fonts-noto-cjk` |

可选（**不装也能出片**）：`node`（HyperFrames/Remotion）、`uv`（Pixelle / MoneyPrinterTurbo）。
本技能不打包这两个引擎，需要时按「备用链路」另装。

**第一次在这台机器上用，先跑 `firstrun.py`**：它补齐 Python 依赖，再跑完整预检，最后给 READY / NOT READY 结论。

```powershell
python scripts\firstrun.py --src "D:\footage" --work "D:\work" --out "D:\out"
python scripts\firstrun.py --check       # 只检查，不安装
```

之后单跑预检：

```powershell
python scripts\doctor.py --src "D:\footage" --work "D:\work" --out "D:\out"
python scripts\doctor.py --json          # 给 agent 读
```

`setup.py` 只负责 Python 侧依赖（numpy / Pillow / edge-tts），不碰系统软件。

## 位置参数

所有脚本都认这五个参数；不传就用环境变量，再不行用当前目录下的 `./source`、`./work`、`./out`。

| 参数 | 环境变量 | 默认 | 用途 |
|---|---|---|---|
| `--src` | `FILM_SRC` | `./source` | 原始素材根目录 |
| `--work` | `FILM_WORK` | `./work` | 工程目录，每片一个 `<proj>/assets` |
| `--out` | `FILM_OUT` | `./out` | 成片目录 |
| `--qa` | `FILM_QA` | `<work>/_qa` | verify.py 的九宫格 |
| `--logo` | `FILM_LOGO` | `<work>/logo_white.png` | 反白 logo；**缺失不报错**，落版改画字标 |

字体可用 `FILM_FONT_DIR` 指向自带字体目录。

## 四步走完一部片

```powershell
$S = "<skill>\scripts"
$P = "--src","D:\footage","--work","D:\work","--out","D:\out"

# 0 预检
python $S\doctor.py @P

# 1 脚手架：扫母版、按真实时长挑入点、写 spec_local.py
python $S\newfilm.py @P --proj film01 --shots 8 --duration 40 --aspect 16:9 --title "Film 01"

# 2 改文案（真人活）：打开的 spec_local.py 里填 cn / en / eyebrow / vo / rows
# 3 卡画面：每句词对不上画面就不许往下走
python $S\preview.py @P

# 4 出片
python $S\build.py A @P          # 切镜 + 调色 + 曝光匹配
python $S\overlay_gen.py A @P    # 透明字幕卡 / 落版
python $S\audio.py A @P          # 配音 + BGM + 混音
python $S\compose.py A @P        # 推镜 + 贴字 + 进度条 + 拼接 + 混音
python $S\verify.py "D:\out\film01_16x9.mp4" @P   # 验收 + 九宫格
```

`A` 是投影 key，可写 `AB` 或 `AB` 里的任意组合。竖屏把 `--aspect 9:16` 传给 `newfilm.py`
即可，后续四步完全一样；`verify.py` 会按工程文件里的画布校验尺寸与时长。

## 工程文件：spec_local.py

`spec.py` 按顺序找项目定义：`$FILM_WORK/spec_local.py` → `./spec_local.py` → 自带的
`spec_example.py`（GEMCO 参考片，只读）。项目文件语法错误会直接退出并报行号，不会静默变成
"没有镜头"。

| 字段 | 含义 |
|---|---|
| `key` / `proj` / `out` | 投影 key、工程目录名、交付文件名 |
| `voice` | edge-tts 音色，如 `en-US-AndrewMultilingualNeural`（商用可用） |
| `duration` | 目标总长；**各 shot 的 `dur` 之和必须等于它** |
| `w` / `h` / `fps` | 画布；16:9 = 1920×1080，9:16 = 1080×1920 |
| `accent` / `base` / `ink` | 强调色 / 底色 / 正文色 |
| `brand` / `logo` | 可选；没有 logo 文件时落版画 `brand` 字标 |
| `music` | `root`(Hz) `bpm` `seed` `bright` `perc`，程序化 BGM 参数 |
| `shots[]` | 每镜一条，见下 |

每镜字段：`layout`(`hero`/`left`/`right`/`side`/`endcard`)、`src`(相对 `--src` 的文件)、
`start`(源内秒数)、`dur`(时长)、`align`(裁切焦点 `"50% 44%"`)、`drift`(`in`/`out`)、
`dim`(额外压暗)、`ch`(章节号)、`eyebrow`、`cn`、`en`、`vo`(英文口播)；
落版另有 `rows[(cn,en)…]`、`cta_cn`、`cta_en`。

**多片要真的不同**：同一个素材包、同一份文案、同一首 BGM 出来的片子只是换了名字，等于没做。
每片至少换掉脚本语气、镜数与节奏、音色、BGM 的速度与调性。

## 硬规则（违反即返工）

1. **等比不放**：一切素材归一必须 `scale=W:H:force_original_aspect_ratio=increase:flags=lanczos,crop=W:H,setsar=1`。禁止裸 `scale=W:H`。比例差过大时改 `decrease` + `pad`。
2. **中英同字号**：两个 Style 只靠颜色/字重/透明度分层，字号必须一致。
3. **素材可商用**：BGM 用脚本内 numpy 合成；配音只用 edge-tts 的商用音色。禁止 CC-BY-NC-ND。
4. **BGM 让人声**：bed 比旁白低约 12 LU，成片整体 ≈ −16 LUFS，TP ≤ −1.5 dBTP。
5. **定长对齐**：每镜 `-t dur` 硬切，各镜时长相加必须精确等于 `duration`。
6. **交付不带浏览器**：任何需要 Chrome 的步骤都不要放进主链路。

## 验收门槛

`verify.py` 必须 PASS：时长与工程文件一致（±0.05 s）、画布尺寸与工程一致、30 fps、
有音轨、−18～−14 LUFS、无 ≥2.2 s 空档。随后**读九宫格 PNG** 逐格确认：无黑帧、无变形、
字幕可读、logo 或字标在位。JPEG 抽帧无法可靠读取，统一用 PNG。

## 换机器时的自检

1. `doctor.py` 全绿（node/uv 显示 `skip` 属正常）。
2. 随便挑一部旧工程 `build.py` → `compose.py`，确认 `ffmpeg` 报错里没有路径问题。
3. 竖屏必须单独跑一次：`newfilm.py --aspect 9:16` 走完整链路，`verify.py` 报 1080×1920。

技术细节（调色配方、遮罩、字体、推镜曲线、坑位）见
[references/style-guide.md](references/style-guide.md) 与
[references/pitfalls.md](references/pitfalls.md)。

## 备用链路

主链做不到时按此降级，不要硬堆主链：

| 场景 | 技能 | 说明 |
|---|---|---|
| 需要 AI 生成画面 / 从主题直接成片 | `moneyprinterturbo-video` | 主题→文案→素材→配音→成片，需 LLM 与素材源 Key |
| 需要 ComfyUI 工作流、数字人、可换 HTML 模板 | `pixelle-video` | `mode=fixed` 可把定稿文案原样切分镜 |
| 浏览器渲染必须参与（HTML 动效、三维） | `hyperframes` 系 | 会拉起 Chrome，先确认环境可用 |
