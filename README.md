# video-expert

用 FFmpeg + Python 把原始拍摄素材剪成可交付成片。无浏览器、无 Node、无付费素材。
横屏 16:9 与竖屏 9:16 共用同一套脚本，中英双语字幕同字号，配音与 BGM 全部可商用。

内容只有一个技能：`ffmpeg-film-pipeline`。

---

## 首次使用（团队成员照抄这一段）

在 PowerShell 里逐行执行（第一行换成你的工作目录）：

```powershell
mkdir C:\video -Force; cd C:\video
git clone <仓库地址> .
python .\ffmpeg-film-pipeline\scripts\firstrun.py --check
```

`firstrun.py --check` 只检查不安装，会逐项报告 ffmpeg / Python / numpy / Pillow / edge-tts / 字体，
并给出缺项的安装命令。确认无误后去掉 `--check` 会自动装好 Python 依赖：

```powershell
python .\ffmpeg-film-pipeline\scripts\firstrun.py
```

看到 `READY` 就说明这台机器可以出片了。

---

## 做第一部片

```powershell
$S = ".\ffmpeg-film-pipeline\scripts"
$P = "--src","D:\footage","--work","D:\work","--out","D:\out"

python $S\newfilm.py @P --proj film01 --shots 8 --duration 40 --aspect 16:9 --title "Film 01"
#   -> 生成 D:\work\spec_local.py，入点按素材真实时长算好
#   打开它，把 cn / en / eyebrow / vo / rows 换成真文案
python $S\preview.py @P          # 卡画面：每句话必须对得上画面
python $S\build.py A @P
python $S\overlay_gen.py A @P
python $S\audio.py A @P
python $S\compose.py A @P
python $S\verify.py "D:\out\film01_16x9.mp4" @P
```

竖屏只改一处：`newfilm.py --aspect 9:16`。

---

## 依赖

硬依赖（缺一不可）：

| 依赖 | 检查 |
|---|---|
| ffmpeg / ffprobe（含 libx264、aac） | `ffmpeg -version` |
| Python ≥ 3.10 | `python -V` |
| numpy、Pillow、edge-tts ≥ 7.3.1 | `firstrun.py` 自动装 |
| 一套 CJK 字体 + 一套拉丁字体 | `doctor.py` 自动查找 |

可选（不装也能出片）：`node`、`uv`、HyperFrames、Pixelle-Video、MoneyPrinterTurbo。

---

## 三条硬规则

1. **等比不放**：素材必须 `force_original_aspect_ratio=increase` + `crop`，禁止裸 `scale=W:H`。
2. **多片不许同质**：同素材 + 同文案 + 同 BGM 只是换了名字，等于没做。每片至少换脚本语气、镜数节奏、音色、BGM。
3. **版权干净**：BGM 由脚本内 numpy 合成；配音只用 edge-tts 商用音色；中英同字号，只靠颜色/字重分层。

---

## 结构

```
ffmpeg-film-pipeline/
  SKILL.md              完整说明（流程、参数、spec 字段、验收）
  SKILL.patch.md        版本改动记录
  references/           调色配方、坑位清单
  scripts/
    firstrun.py         首次环境检查 + 安装
    doctor.py           环境诊断
    newfilm.py          生成项目定义 spec_local.py
    preview.py          切点九宫格预览
    build.py            切镜 + 调色 + 曝光匹配
    overlay_gen.py      字幕卡 / 落版
    audio.py            配音 + BGM + 混音
    compose.py          推镜 + 贴字 + 进度条 + 拼接
    verify.py           验收 + 九宫格
    paths.py / spec.py  路径与项目定义的唯一来源
```

路径全部按 `参数 → 环境变量 → 相对默认` 解析，不含任何本机绝对路径，换机器不需要改代码。
