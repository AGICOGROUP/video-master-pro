## Patch 2026-10-19 — 团队分发版

本文件记录相对初版（GEMCO 单机版）的改动，全部已在 16:9 与 9:16 上跑通全链路。

- **paths.py**：新增统一的位置解析（`--src/--work/--out/--qa/--logo` → 同名 `FILM_*` → `./source` 等相对默认），去掉所有本机绝对路径；字体按别名 glob 在全系统查找（Windows/macOS/Linux 同一套调用）。
- **spec.py**：项目定义改为 `$FILM_WORK/spec_local.py` → `./spec_local.py` → 自带 `spec_example.py`；项目文件语法错误直接退出并报原因，不再静默变成"没有镜头"；回退到示例时打印提示。
- **newfilm.py（新）**：扫素材、按真实时长挑入点、生成 `spec_local.py` 脚手架；`--aspect 9:16` 直接把画布写成 1080×1920。修复 `--out` 曾被误当作成片文件名的问题（它是输出目录，由 paths.py 消费）。
- **build.py**：自动创建 `<proj>/assets` 与 `compositions/`（新工程首跑不再因缺目录报 rc=-2）；调色表改用 `.get()` 兜底，任意自定义 key 不再 KeyError；竖屏按 spec 画布等比裁切。
- **overlay_gen.py**：改为「1920 宽逻辑画布绘制 → 等比缩放到目标尺寸」，一套坐标同时服务 16:9 与 9:16，避免竖屏落版溢出；logo 缺失不再抛异常，落版与角标退化为 `brand` 字标。
- **compose.py**：合成前创建输出目录（`FILM_OUT` 不存在时不再报 "No such file or directory"）。
- **verify.py**：目标画布与时长从工程文件读取，不再硬编码 1920×1080/60 s；同名画布多片时按时长任一匹配判定；自动剥离 `--src/--work/--out/--qa/--logo` 参数（修复 ffprobe 收到 `-work` 报错）；找不到工程文件时明确提示时长未校验。
- **doctor.py**：`footage:src` 显示解析后的真实路径与缺失状态。
- **SKILL.md**：重写为可移植版（四步流程、位置参数表、spec 字段、硬规则、换机器自检）。

未打包：node / uv / HyperFrames / Pixelle-Video / MoneyPrinterTurbo（约 2.4 GB），属可选链路，见 SKILL.md「备用链路」。
