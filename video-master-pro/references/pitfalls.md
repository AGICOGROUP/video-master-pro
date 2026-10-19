# Pitfalls — 全部踩过并验证过解法

## 画面

1. **裸 `scale=W:H` 会拉伸**，用户一眼看出来。必须
   `scale=W:H:force_original_aspect_ratio=increase:flags=lanczos,crop=W:H,setsar=1`；
   横竖比例差过大（如 4:3 素材进 9:16）改 `decrease` + `pad` 补边。
2. **`crop` 焦点要可调**：`align="50% 44%"` 这种写法映射成 `crop=...:(iw-ow)*0.5:(ih-oh)*0.44`，主体偏上时不要用居中默认值。
3. **iPhone/MOV 是 `yuvj420p` 全范围**，直接进 libx264 会报 “Non full-range YUV”。切镜时先 `format=yuvj420p` 再 `format=yuv420p`。
4. **几何表达式里的 `t`**：`drawbox w='iw*t/dur'` 逐帧求值没问题，但把表达式写进 `-vf` 之外的 JSON 时要转义单引号。

## 字幕与文字

5. **FFmpeg `subtitles` 滤镜在 Windows 上会因素材绝对路径的冒号解析失败**，且默认行高会让字号失控。要烧字幕就生成 **ASS**，显式写 `PlayResX: 1920` / `PlayResY: 1080` 和固定 `Fontsize`。本管线不用 SRT，直接用 PIL 出透明 PNG，绕开整类问题。
6. **中英双语必须同字号**，两个 Style 只换颜色/字重/透明度。用字号做层级会被判为缺陷。
7. **字距不能靠 PIL**：写 `draw_tracked()` 逐字画；`ImageDraw.text()` 的返回值不能当 x 坐标用，量宽度用 `textlength()`。
8. **f-string 里的 `{{KEY}}` 会变成 `{KEY}`**：做模板替换时双大括号、单大括号各替换一遍，否则画面出现字面占位符。

## 声音

9. **`edge-tts` 7.2.x 返回 403**，装 `>=7.3.1`。所有调用外包 `asyncio.wait_for(..., timeout=60)`，否则网络抖动会永久挂住。
10. **配音超时长**：不要用 `atempo > 1.3` 硬压（会变声）。改文案（缩短一句）后重跑，只允许 ≤3% 的语速微调。
11. **BGM 埋掉人声**：把 bed 定在旁白下方 12 LU 并加侧链 duck，而不是拍脑袋给 `-20 dB` 增益。
12. **版权**：只用 numpy 合成 BGM 与 edge-tts 商用音色；CC-BY-NC-ND 一票否决。

## 环境（Windows）

13. **PowerShell 里 `python -c` 多行脚本会被拆坏**：写成 `.py` 文件再跑。
14. **`Get-Content` 管道喂给原生 CLI 会破坏 UTF-8**：改用文件参数或 `-Encoding UTF8`。
15. **ffmpeg 的 `-stats` 输出会淹没日志**：统一 `-hide_banner -loglevel error`，失败时只读 stderr 末 1–2 KB。
16. **JPEG 抽帧无法用 read 工具可靠查看**（返回二进制截断）：验收一律抽 **PNG**。
17. **HyperFrames 渲染会拉起 Chrome 并可能挂死**：`chrome.exe --version` 超时（TIMEDOUT）时先清宿主注入的 `CHROME_CRASHPAD_PIPE_NAME`、`PHOENIX_BROWSER_RELAY_PORT`，再清残留 headless Chrome 与 `%TEMP%\HeadlessChrome*`；`missing_gsap_script` 要在动画脚本前补 GSAP CDN。两条都过不去就**放弃浏览器链路，走本管线**，不要反复试探。
18. **不要并发跑十几个 ffmpeg 渲染**：本机 16 核也扛不住 x264 medium，串行更快也更稳。

## 交付

19. **concat 用 `-c:v copy` 要求每段编码参数完全一致**（分辨率、fps、pix_fmt、SAR、GOP）。任何一段参数不同就会花屏或直接失败；每段都写 `-t dur` 定长。
20. **`-shortest` 必须在混音那一步**，否则音频比画面长会在结尾留黑。
21. **验收不能只看文件生成成功**：`verify.py` PASS 之后仍要读九宫格 PNG，逐格确认无黑帧、无变形、字幕可读、logo 在位。
