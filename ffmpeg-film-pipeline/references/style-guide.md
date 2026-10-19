# Style guide — 已交付数值，改风格从这里抄

## 画布与编码

| 项 | 值 |
|---|---|
| 画布 | 1920×1080（竖屏改 1080×1920，所有 x 坐标镜像，`scrim` 的 side 改竖直） |
| 帧率 | 30 fps，`-g 30` |
| 编码 | `libx264 -preset medium -crf 17 -pix_fmt yuv420p` |
| 音频 | AAC 192k / 48 kHz / 立体声，`-movflags +faststart -shortest` |
| 成片体积参考 | 60 s ≈ 75–105 MB（车间实拍纹理多，码率自然高） |

## 调色（build.py 内 GRADE_A / GRADE_B）

```
A  #E8A33D 暖金工业感
  curves=all='0/0 0.20/0.155 0.50/0.505 0.80/0.855 1/1'
  eq=contrast=1.105:saturation=0.84:gamma=0.98
  colorbalance=rs=-0.030:bs=0.055:rm=0.004:bm=0.010:rh=0.040:gh=0.006:bh=-0.028
  vignette=PI/4.6, unsharp=5:5:0.55, noise=alls=3:allf=t

B  #3FCB74 冷静绿
  curves=all='0/0 0.20/0.17 0.50/0.53 0.82/0.865 1/1'
  eq=contrast=1.065:saturation=1.02:gamma=1.01
  colorbalance=rs=0.020:gs=0.008:bs=-0.026:rm=0.010:bm=-0.004:rh=0.018:gh=0.010:bh=-0.006
  vignette=PI/5.2, unsharp=5:5:0.45, noise=alls=3:allf=t
```

调色前先 `measure_yavg()` 把各镜曝光拉到同一水平，否则跳镜会“忽明忽暗”。

## 版式（overlay_gen.py）

通用：左边距 96 px，右上 logo 宽 292 px 放在 `(W-96-292, 56)`。

| layout | 排版 |
|---|---|
| `hero`（片头） | 居中竖排：eyebrow 23 px / 字距 9（accent）→ 250 px 细横线(白 35%)→ 中文 112 px 加粗 → 英文 42 px 字距 6（ink）→ 64 px accent 短横线(2 px) |
| `left` / `right` | 底部对齐：左上章节号 30 px（accent）+ 22 px 短横线 + eyebrow 21 px 字距 7（白 93%）；主体 92 px accent 短线(2 px) → 中文 42 px → 英文 42 px 字距 1（ink）；`right` 时整块贴右边 |
| `side` | 同 left，但主体放在左侧垂直居中（`H*0.5-60`），配合右侧大景 |
| `endcard` | 全屏压 232/255 黑底；logo 352 px @(96,88)；eyebrow 22 px 字距 8；中文 76 px；英文 40 px；规格行 27 px×2，1120 px 细分割线(白 15%)；CTA 中文 28 px 加粗 + 英文 28 px（accent） |

**中英同字号是硬规则**：`left/right/side` 全部 42 px，只靠白色/半透明 ink 分层。

## 遮罩 scrim（亮画面上字幕可读的关键）

用 numpy 画灰度 alpha 再合成为 RGBA，不要用纯色半透明矩形（会有硬边）。

- `hero`：径向，中心 0.30 → 边缘 0.86
- `side`：左侧 0.965 起，x=620→920 线性衰减到 0
- 其他（bottom）：从 `H*0.52` 起 `((y-0.52H)/(0.48H))^1.25 * 0.80`，底部约 0.86；顶部 `0~0.10H` 补 0.45 保证章节号可读

## 运动（compose.py）

| 元素 | 曲线 |
|---|---|
| 推镜 `in` | `zoompan z='1+0.045*on/(frames-1)'` |
| 推镜 `out` | `z='1.050-0.046*on/(frames-1)'` |
| 字幕浮入 | `fade=t=in:st=0.12:d=0.60:alpha=1` |
| 片头淡入 | `fade=t=in:st=0:d=0.85` |
| 片尾淡出 | `fade=t=out:st=dur-1.0:d=1.0` |
| 进度条 | `drawbox y=ih-2 h=2 color=accent@0.95 w='iw*t/dur'` |
| 切镜 | 硬切（不加转场），靠 `drift` 方向交替制造节奏 |

## 音频（audio.py）

- 旁白：edge-tts，`rate=-3%`，逐镜一句；生成用 `asyncio.wait_for(timeout=60)`；失败换句式重试。
- BGM：`music_promo()` numpy 合成（大三和弦 pad + 琶音 + 轻打击 + 低通底鼓），`root`/`bpm`/`seed`/`bright`/`perc` 控制性格；无第三方采样。
- 混音：bed 实测 LUFS 后固定压到旁白下方 **12 LU**（`BED_BELOW_LU`），侧链 duck（阈值 0.05 / 比 3:1），末段 `loudnorm I=-16:TP=-1.5`。
- 交付实测：A −16.41 LUFS / TP −1.23；B −16.29 / −1.24。

## 文案规格

- `eyebrow`：全大写英文 + `·` 分隔，如 `GEMCO ENERGY · FEED PELLET MILLS`
- `cn`：≤14 字，动宾短句，不写形容词堆砌
- `en`：≤6 词，与中文同义不同字
- `vo`：一句 ≤12 词，口语，具体（数字、动作、结果）
