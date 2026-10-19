"""Specs for the two GEMCO product films (60 s each).

Every shot is described by an in-point inside a source clip, a fixed slot
duration, a typographic layout, and the narration written for that slot.
The narration is fitted into its slot by audio2.py (rate is only raised when
a slower read would overflow the slot).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SRC  # noqa: E402

# Long single-take recordings that hold the real production footage.
R1 = "11fb159c334c71527f13a4e75ec0908b.mp4"   # installed line: cooler, silos, conveyors
R2 = "9fe2ffb3b5707a20c16da18aaa12ce6d.mp4"   # flat die mill demos, pellets, inverter
R3 = "f8e5852016600e9bc923812227fee855.mp4"   # blue line: feeding, pellets pouring, bagging

S1 = "2月13日拍摄"
S2 = "2月21日拍摄/2月21日拍摄"
S3 = "3月1日拍摄/3月1日拍摄"

RINGDIE = dict(
    key="A",
    proj="gemco-ringdie",
    title="GEMCO 环模颗粒机 60s",
    out="01_GEMCO环模颗粒机_60s_中英字幕_英文配音.mp4",
    voice="en-US-AndrewMultilingualNeural",
    duration=60.0,
    accent="#E8A33D",
    base="#0A0D0F",
    ink="#C3CDD3",
    music=dict(root=130.81, bpm=104, seed=11, bright=1.0, perc=1.0),
    shots=[
        dict(layout="hero", src=R1, start=88.0, dur=6.6, align="50% 50%", drift="in",
             ch="01", eyebrow="GEMCO ENERGY  ·  FEED PELLET MILLS",
             cn="环模颗粒机", en="Ring Die Pellet Mill",
             vo="One job: turn feed into pellets, shift after shift."),
        dict(layout="left", src="2623/IMG_1884.MOV", start=1.0, dur=6.6, align="52% 46%", drift="out",
             ch="02", eyebrow="THE MACHINE",
             cn="环模转动，压辊挤粒", en="A turning die, rollers pressing meal",
             vo="The die turns, and rollers press meal through every hole."),
        dict(layout="right", src=R3, start=30.0, dur=6.4, align="52% 45%", drift="in", dim=0.16,
             ch="03", eyebrow="DRIVE & CONTROL",
             cn="一屏掌控转速与负载", en="Speed and load, on one panel",
             vo="Speed, current and safety sit on one panel, readable at a glance."),
        dict(layout="left", src=f"{S2}/IMG_6533.MOV", start=1.5, dur=7.0, align="50% 46%", drift="in",
             ch="04", eyebrow="DIE MACHINING",
             cn="环模自制，逐孔钻削", en="Dies machined in-house, hole by hole",
             vo="We machine the die ourselves: drilled, finished, and checked hole by hole."),
        dict(layout="side", src=R3, start=790.0, dur=6.8, align="50% 44%", drift="out", dim=0.10,
             ch="05", eyebrow="OUTPUT",
             cn="入料即出粒", en="Meal in, pellets out",
             vo="Meal in. Dense, uniform pellets out, the same size bag after bag."),
        dict(layout="left", src=R1, start=112.0, dur=6.6, align="50% 48%", drift="in", dim=0.06,
             ch="06", eyebrow="COMPLETE LINE",
             cn="嵌入整条生产线", en="Part of a complete line",
             vo="It works inside a full line: grinding, mixing, pelleting, bagging."),
        dict(layout="right", src=f"{S2}/IMG_6548.MOV", start=8.0, dur=6.8, align="44% 50%", drift="out",
             ch="07", eyebrow="LOAD TEST",
             cn="逐台装配，带载试机", en="Assembled and load-tested",
             vo="Every machine is assembled, wired, and run under load before it ships."),
        dict(layout="left", src=f"{S1}/IMG_6420.MOV", start=8.0, dur=6.4, align="50% 46%", drift="in",
             ch="08", eyebrow="EXPORT PACKING",
             cn="木箱加固，整柜发运", en="Crated, braced, shipped",
             vo="Then crated, braced, and loaded for export from our own yard."),
        dict(layout="endcard", src="2623/IMG_1890.MOV", start=40.0, dur=6.8, align="50% 50%", drift="in",
             ch="09", eyebrow="GEMCO ENERGY  ·  RING DIE PELLET MILLS",
             cn="环模颗粒机", en="Ring Die Pellet Mill",
             rows=[("环模与备件", "Ring dies & spare parts"),
                   ("整机装配", "Complete machine assembly"),
                   ("带载试机", "Load testing before shipment")],
             cta_cn="欢迎来厂考察与选型", cta_en="Visit our factory, or send your inquiry",
             vo="GEMCO Energy. Ring die pellet mills, and the dies they run on."),
    ],
)

FLATDIE = dict(
    key="B",
    proj="gemco-flatdie",
    title="GEMCO 平模颗粒机 60s",
    out="02_GEMCO平模颗粒机_60s_中英字幕_英文配音.mp4",
    voice="en-US-BrianMultilingualNeural",
    duration=60.0,
    accent="#3FCB74",
    base="#08100C",
    ink="#BFD2C8",
    music=dict(root=146.83, bpm=96, seed=23, bright=1.18, perc=0.8),
    shots=[
        dict(layout="hero", src=R2, start=620.0, dur=6.4, align="50% 46%", drift="in", dim=0.10,
             ch="01", eyebrow="GEMCO ENERGY  ·  COMPACT PELLETING",
             cn="平模颗粒机", en="Flat Die Pellet Mill",
             vo="Not every farm needs a plant. Some just need to start."),
        dict(layout="left", src=R2, start=106.0, dur=6.8, align="48% 48%", drift="out",
             ch="02", eyebrow="THE MACHINE",
             cn="一机一电机", en="One motor, one die",
             vo="A flat die pellet mill: one motor, one die, and little to learn."),
        dict(layout="right", src=R2, start=740.0, dur=7.0, align="50% 42%", drift="in",
             ch="03", eyebrow="FLAT DIE",
             cn="平模在上，压辊直压", en="Flat die, rollers on top",
             vo="The die lies flat; rollers press the feed straight through."),
        dict(layout="left", src=R2, start=202.0, dur=6.6, align="50% 50%", drift="in", dim=0.12,
             ch="04", eyebrow="INVERTER CONTROL",
             cn="变频调速，电流可视", en="Inverter speed, visible load",
             vo="Speed is set on the inverter. The amps sit right in front of you."),
        dict(layout="side", src=R3, start=225.0, dur=6.8, align="46% 46%", drift="out", dim=0.09,
             ch="05", eyebrow="FEEDING",
             cn="自有原料，就地制粒", en="Your grain, your mix",
             vo="Load your own grain or your own mix. No specialist operator needed."),
        dict(layout="left", src=R3, start=830.0, dur=6.6, align="50% 40%", drift="in",
             ch="06", eyebrow="OUTPUT",
             cn="出粒均匀，即冷即装", en="Even pellets, ready to bag",
             vo="Pellets come out warm and even, ready to cool and bag."),
        dict(layout="right", src=R2, start=862.0, dur=6.8, align="50% 50%", drift="out",
             ch="07", eyebrow="PELLET QUALITY",
             cn="颗粒密实，粉化少", en="Dense and even, all the way through",
             vo="Dense and even, all the way through, bag after bag."),
        dict(layout="left", src=f"{S3}/IMG_6679.MOV", start=2.0, dur=6.0, align="50% 44%", drift="in",
             ch="08", eyebrow="SHIPPING",
             cn="占地小，整机发运", en="Compact, shipped assembled",
             vo="A small footprint, and it ships assembled and tested."),
        dict(layout="endcard", src=R2, start=275.0, dur=7.0, align="50% 48%", drift="in", dim=0.05,
             ch="09", eyebrow="GEMCO ENERGY  ·  FLAT DIE PELLET MILLS",
             cn="从一台机器开始", en="Start with one machine",
             rows=[("平模与压辊", "Flat dies & rollers"),
                   ("变频控制", "Inverter control"),
                   ("整机发运", "Shipped fully assembled")],
             cta_cn="告诉我们你的产量，我们帮你选型", cta_en="Tell us your output, we will size it",
             vo="GEMCO Energy. Tell us your capacity, and we will size the machine."),
    ],
)

SPECS = {"A": RINGDIE, "B": FLATDIE}
