#!/usr/bin/env python3
"""Generate seven chat-grounded strategy diagrams for the briefing.

The diagrams intentionally contain no repository experiment results.  Every
claim, example, and proposed mechanism comes from the archived 11-turn chat.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


BRIEFING_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BRIEFING_ROOT / "figures" / "story"

FIGSIZE = (16, 9)
PNG_DPI = 150
FONT = "Hiragino Sans GB"

BACKGROUND = "#FFFFFF"
TEXT = "#172033"
MUTED = "#5B6472"
BORDER = "#C9D1DC"
GRID = "#DDE3EA"

# Stable semantic mapping across all seven figures.
GRAY = "#6B7280"  # related work / elements outside Barcarolle
GRAY_LIGHT = "#EEF1F4"
BLUE = "#2463D4"  # Barcarolle
BLUE_DARK = "#174A9C"
BLUE_LIGHT = "#EAF2FF"
ORANGE = "#D96A1D"  # risk / unresolved gap
ORANGE_LIGHT = "#FFF0E5"
GREEN = "#15845B"  # later real work / external anchor
GREEN_LIGHT = "#E7F6EF"


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": BACKGROUND,
            "savefig.facecolor": BACKGROUND,
            "font.family": FONT,
            "font.sans-serif": [FONT, "Heiti SC", "Arial Unicode MS"],
            "font.weight": 300,
            "text.color": TEXT,
            "axes.unicode_minus": False,
            "svg.fonttype": "none",
        }
    )


def new_canvas(
    number: int,
    title: str,
    question: str,
    status: str,
    status_color: str,
) -> tuple[Figure, Axes]:
    fig = plt.figure(figsize=FIGSIZE, dpi=PNG_DPI)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(
        0.65,
        8.48,
        f"{number:02d}",
        fontsize=13,
        fontweight=600,
        color=BLUE,
        va="center",
        ha="center",
        bbox={
            "boxstyle": "round,pad=0.38,rounding_size=0.18",
            "facecolor": BLUE_LIGHT,
            "edgecolor": BLUE,
            "linewidth": 1.2,
        },
    )
    ax.text(1.18, 8.56, title, fontsize=23, fontweight=600, va="center")
    ax.text(1.18, 8.08, f"这张图回答：{question}", fontsize=12.5, color=MUTED)
    ax.text(
        15.35,
        8.5,
        status,
        fontsize=11,
        fontweight=600,
        color=status_color,
        ha="right",
        va="center",
        bbox={
            "boxstyle": "round,pad=0.42,rounding_size=0.18",
            "facecolor": BACKGROUND,
            "edgecolor": status_color,
            "linewidth": 1.4,
        },
    )
    ax.plot([0.65, 15.35], [7.78, 7.78], color=GRID, linewidth=1.0)
    return fig, ax


def footer(ax: Axes, note: str, turns: str, color: str) -> None:
    ax.plot([0.65, 15.35], [0.72, 0.72], color=GRID, linewidth=1.0)
    ax.text(0.65, 0.36, note, fontsize=10.5, color=color, va="center")
    ax.text(
        15.35,
        0.36,
        f"对应原始对话：{turns}",
        fontsize=10.5,
        color=MUTED,
        va="center",
        ha="right",
    )


def rounded_rect(
    ax: Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    facecolor: str = BACKGROUND,
    edgecolor: str = BORDER,
    linewidth: float = 1.3,
    radius: float = 0.16,
    zorder: int = 2,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def box(
    ax: Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str = "",
    *,
    facecolor: str = BACKGROUND,
    edgecolor: str = BORDER,
    title_color: str = TEXT,
    body_color: str = MUTED,
    title_size: float = 13,
    body_size: float = 10.5,
    linewidth: float = 1.3,
    radius: float = 0.16,
    zorder: int = 3,
) -> None:
    rounded_rect(
        ax,
        x,
        y,
        width,
        height,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        radius=radius,
        zorder=zorder,
    )
    title_y = y + height * (0.64 if body else 0.5)
    ax.text(
        x + width / 2,
        title_y,
        title,
        ha="center",
        va="center",
        fontsize=title_size,
        fontweight=600,
        color=title_color,
        linespacing=1.25,
        zorder=zorder + 1,
    )
    if body:
        ax.text(
            x + width / 2,
            y + height * 0.27,
            body,
            ha="center",
            va="center",
            fontsize=body_size,
            color=body_color,
            linespacing=1.3,
            zorder=zorder + 1,
        )


def arrow(
    ax: Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = GRAY,
    linewidth: float = 1.7,
    mutation_scale: float = 13,
    connectionstyle: str = "arc3,rad=0",
    linestyle: str = "-",
    zorder: int = 1,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=linewidth,
            color=color,
            linestyle=linestyle,
            connectionstyle=connectionstyle,
            shrinkA=2,
            shrinkB=2,
            zorder=zorder,
        )
    )


def tag(
    ax: Axes,
    x: float,
    y: float,
    text: str,
    *,
    color: str,
    facecolor: str,
    fontsize: float = 10.5,
    ha: str = "center",
) -> None:
    ax.text(
        x,
        y,
        text,
        ha=ha,
        va="center",
        fontsize=fontsize,
        color=color,
        fontweight=600,
        bbox={
            "boxstyle": "round,pad=0.32,rounding_size=0.14",
            "facecolor": facecolor,
            "edgecolor": "none",
        },
        zorder=8,
    )


def save(fig: Figure, stem: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / f"{stem}.png"
    svg_path = OUTPUT_DIR / f"{stem}.svg"
    fig.savefig(png_path, dpi=PNG_DPI)
    fig.savefig(svg_path, format="svg")
    # Matplotlib emits spaces after multiline SVG path coordinates.  Strip
    # them so generated assets pass the repository's whitespace check.
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)


def diagram_01() -> None:
    fig, ax = new_canvas(
        1,
        "评测为什么从“尺子”变成“方向盘”",
        "为什么 Agent 自动优化以后，原本可用的固定评测会变得危险？",
        "机制示意",
        ORANGE,
    )

    columns = [
        (0.75, "今天", "评测只是尺子", GRAY, GRAY_LIGHT),
        (5.85, "变化", "评测进入优化闭环", BLUE, BLUE_LIGHT),
        (10.95, "风险", "小偏差被主动放大", ORANGE, ORANGE_LIGHT),
    ]
    for x, heading, caption, color, fill in columns:
        rounded_rect(ax, x, 1.65, 4.3, 5.6, facecolor=fill, edgecolor=color)
        ax.text(x + 0.28, 6.88, heading, fontsize=14, fontweight=600, color=color)
        ax.text(x + 0.28, 6.5, caption, fontsize=11, color=MUTED)

    box(ax, 1.35, 5.15, 3.1, 0.85, "工程师提出改动", facecolor=BACKGROUND)
    box(ax, 1.35, 3.8, 3.1, 0.85, "少量候选版本", facecolor=BACKGROUND)
    box(ax, 1.35, 2.45, 3.1, 0.85, "固定基准评测", facecolor=BACKGROUND)
    arrow(ax, (2.9, 5.13), (2.9, 4.68), color=GRAY)
    arrow(ax, (2.9, 3.78), (2.9, 3.33), color=GRAY)

    box(
        ax,
        6.45,
        5.15,
        3.1,
        0.85,
        "自动改进系统",
        facecolor=BACKGROUND,
        edgecolor=BLUE,
        title_color=BLUE_DARK,
    )
    box(ax, 6.45, 3.8, 3.1, 0.85, "大量新版本", facecolor=BACKGROUND)
    box(ax, 6.45, 2.45, 3.1, 0.85, "反复读取同一评测", facecolor=BACKGROUND)
    arrow(ax, (8.0, 5.13), (8.0, 4.68), color=BLUE)
    arrow(ax, (8.0, 3.78), (8.0, 3.33), color=BLUE)

    box(
        ax,
        11.55,
        5.05,
        3.1,
        1.0,
        "真实能力  +  评测偏差",
        facecolor=BACKGROUND,
        edgecolor=ORANGE,
        title_color=ORANGE,
        title_size=12.5,
    )
    box(
        ax,
        11.55,
        3.65,
        3.1,
        0.9,
        "优化器同时搜索两者",
        facecolor=BACKGROUND,
        edgecolor=ORANGE,
        title_color=ORANGE,
        title_size=12.5,
    )
    arrow(ax, (13.1, 5.02), (13.1, 4.58), color=ORANGE)
    arrow(ax, (13.1, 3.63), (12.15, 3.06), color=ORANGE)
    arrow(ax, (13.1, 3.63), (14.05, 3.06), color=ORANGE)
    box(
        ax,
        11.05,
        2.15,
        2.2,
        0.8,
        "评测继续涨",
        facecolor=ORANGE_LIGHT,
        edgecolor=ORANGE,
        title_color=ORANGE,
        title_size=11.5,
    )
    box(
        ax,
        13.35,
        2.15,
        1.95,
        0.8,
        "真实提升停滞",
        facecolor=GREEN_LIGHT,
        edgecolor=GREEN,
        title_color=GREEN,
        title_size=11.2,
    )

    arrow(ax, (5.08, 4.45), (5.72, 4.45), color=BLUE, linewidth=2.2)
    arrow(ax, (10.18, 4.45), (10.82, 4.45), color=ORANGE, linewidth=2.2)
    tag(
        ax,
        8.0,
        1.22,
        "候选越多，越容易选中评测偏差最大的版本",
        color=ORANGE,
        facecolor=ORANGE_LIGHT,
        fontsize=12,
    )

    footer(
        ax,
        "机制示意：说明风险如何产生，不表示 Barcarolle 已观察到该结果",
        "第 6、7、10、11 轮",
        ORANGE,
    )
    save(fig, "01-evaluation-becomes-objective")


def diagram_02() -> None:
    fig, ax = new_canvas(
        2,
        "领域地图：Barcarolle 要补哪个空位",
        "相关工作覆盖了哪些区域，Barcarolle 的研究起点和目标分别在哪里？",
        "相关工作事实 + 位置归纳",
        GRAY,
    )

    left, right, bottom, top = 1.75, 14.65, 1.45, 7.2
    ax.add_patch(
        FancyBboxPatch(
            (8.2, 4.35),
            right - 8.2,
            top - 4.35,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=BLUE_LIGHT,
            edgecolor="none",
            alpha=0.7,
            zorder=0,
        )
    )
    ax.text(14.35, 6.86, "待补的空位", color=BLUE, fontsize=11, ha="right")

    ax.plot([left, right], [bottom, bottom], color=TEXT, linewidth=1.4)
    ax.plot([left, left], [bottom, top], color=TEXT, linewidth=1.4)
    arrow(ax, (right - 0.35, bottom), (right, bottom), color=TEXT, linewidth=1.4)
    arrow(ax, (left, top - 0.35), (left, top), color=TEXT, linewidth=1.4)
    ax.plot([8.2, 8.2], [bottom, top], color=GRID, linewidth=1.0, linestyle="--")
    ax.plot([left, right], [4.35, 4.35], color=GRID, linewidth=1.0, linestyle="--")

    ax.text(left, 1.05, "旁观测量", fontsize=11.5, color=MUTED, ha="left")
    ax.text(right, 1.05, "进入连续优化闭环", fontsize=11.5, color=MUTED, ha="right")
    ax.text(
        0.72,
        bottom,
        "固定题或生成题",
        fontsize=11.5,
        color=MUTED,
        rotation=90,
        va="bottom",
        ha="center",
    )
    ax.text(
        0.72,
        top,
        "后来真实工作对账",
        fontsize=11.5,
        color=MUTED,
        rotation=90,
        va="top",
        ha="center",
    )

    box(
        ax,
        2.35,
        2.0,
        2.15,
        0.95,
        "SWE-bench",
        "固定任务",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=12,
        body_size=9.5,
    )
    box(
        ax,
        4.7,
        2.85,
        2.65,
        1.05,
        "SWE-Interact / Together",
        "交互与重放",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=10.8,
        body_size=9.4,
    )
    box(
        ax,
        4.75,
        4.45,
        2.25,
        1.0,
        "SWE-Future",
        "未来需求方向",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=11.8,
        body_size=9.4,
    )
    box(
        ax,
        9.15,
        2.05,
        2.25,
        0.95,
        "ADAS / DGM",
        "自动提出版本",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=11.8,
        body_size=9.4,
    )
    box(
        ax,
        10.25,
        4.0,
        2.4,
        1.05,
        "RQGM",
        "可变评估 + 固定锚",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=12,
        body_size=9.4,
    )

    box(
        ax,
        4.15,
        6.0,
        3.05,
        0.95,
        "Barcarolle 研究起点",
        "固定 Agent，对账后来任务",
        facecolor=BLUE_LIGHT,
        edgecolor=BLUE,
        title_color=BLUE_DARK,
        body_color=BLUE_DARK,
        title_size=12,
        body_size=9.3,
        linewidth=1.7,
    )
    box(
        ax,
        11.55,
        5.85,
        2.8,
        1.15,
        "Barcarolle 研究目标",
        "连续优化后，仍对账后来任务",
        facecolor=BLUE,
        edgecolor=BLUE_DARK,
        title_color=BACKGROUND,
        body_color=BACKGROUND,
        title_size=11.8,
        body_size=9.2,
        linewidth=1.8,
    )
    arrow(
        ax,
        (7.25, 6.47),
        (11.48, 6.43),
        color=BLUE,
        linewidth=2.4,
        mutation_scale=16,
    )
    ax.text(9.35, 6.67, "研究推进方向", fontsize=10.5, color=BLUE, ha="center")

    footer(
        ax,
        "相关工作的能力描述来自对话引用；二维位置是战略归纳，不是定量排名",
        "第 2、8、9 轮",
        GRAY,
    )
    save(fig, "02-landscape-and-position")


def diagram_03() -> None:
    fig, ax = new_canvas(
        3,
        "相关工作各补一块，为什么仍未闭环",
        "每项工作带来了什么，又各自留下了哪一段缺口？",
        "相关工作事实 + 缺口归纳",
        GRAY,
    )

    center = (5.65, 3.18, 4.7, 1.55)
    outer_boxes = [
        (0.7, 5.65, 4.35, 1.45, "SWE-bench", "带来：真实任务、可执行判分\n仍缺：连续优化后的失真"),
        (5.82, 5.65, 4.35, 1.45, "SWE-Interact / Together", "带来：交互、纠正等结果\n仍缺：未来工作来源"),
        (10.95, 5.65, 4.35, 1.45, "ADAS / DGM", "带来：自动提出新版本\n仍缺：不会失真的评估"),
        (1.75, 1.15, 4.75, 1.5, "SWE-Future", "带来：未来需求方向\n仍缺：具体成题的外部校准"),
        (9.5, 1.15, 4.75, 1.5, "RQGM", "带来：分阶段冻结、真值锚\n仍缺：延迟到来的真实工作"),
    ]

    center_points = [
        (6.1, 4.7),
        (8.0, 4.75),
        (9.9, 4.7),
        (6.5, 3.18),
        (9.5, 3.18),
    ]
    outer_points = [
        (4.3, 5.62),
        (8.0, 5.62),
        (11.7, 5.62),
        (5.4, 2.68),
        (10.6, 2.68),
    ]
    for start, end in zip(outer_points, center_points, strict=True):
        arrow(ax, start, end, color=GRAY, linewidth=1.4, zorder=1)

    for x, y, width, height, title, body in outer_boxes:
        box(
            ax,
            x,
            y,
            width,
            height,
            title,
            body,
            facecolor=GRAY_LIGHT,
            edgecolor=GRAY,
            title_size=12,
            body_size=9.5,
        )

    box(
        ax,
        *center,
        "仍缺的一环",
        "反复优化后，今天的提升\n仍对应后来真实工作的提升",
        facecolor=ORANGE_LIGHT,
        edgecolor=ORANGE,
        title_color=ORANGE,
        body_color=TEXT,
        title_size=13,
        body_size=11,
        linewidth=2.0,
    )

    footer(
        ax,
        "覆盖图：外圈是相关工作提供的能力；中央是这些工作尚未共同闭合的问题",
        "第 7、8、9 轮",
        GRAY,
    )
    save(fig, "03-related-work-gap")


def diagram_04() -> None:
    fig, ax = new_canvas(
        4,
        "任务生成最难的一步：从需求方向到具体题，谁说了算",
        "怎样避免任务生成模块用自己的成题偏好定义评测结论？",
        "拟研究方法",
        BLUE,
    )

    box(
        ax,
        0.65,
        4.0,
        2.25,
        1.35,
        "历史与项目状态",
        "不看当前 Agent 的弱点",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=12,
        body_size=9.2,
    )
    box(
        ax,
        3.35,
        4.0,
        2.5,
        1.35,
        "预测需求方向",
        "支持新的序列化类型",
        facecolor=BLUE_LIGHT,
        edgecolor=BLUE,
        title_color=BLUE_DARK,
        body_color=BLUE_DARK,
        title_size=12,
        body_size=9.5,
    )
    arrow(ax, (2.93, 4.68), (3.32, 4.68), color=BLUE)

    materializations = [
        (6.55, 5.65, "具体任务 A", "类型不同"),
        (6.55, 4.0, "具体任务 B", "接口不同"),
        (6.55, 2.35, "具体任务 C", "边界条件不同"),
    ]
    for x, y, title, body in materializations:
        box(
            ax,
            x,
            y,
            2.05,
            1.05,
            title,
            body,
            facecolor=BACKGROUND,
            edgecolor=BLUE,
            title_size=10.8,
            body_size=9,
        )
        arrow(ax, (5.88, 4.68), (x - 0.03, y + 0.52), color=BLUE, linewidth=1.4)

    box(
        ax,
        9.4,
        3.75,
        2.25,
        1.85,
        "同一组多样化 Agent",
        "运行 A、B、C 三种成题",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=11.5,
        body_size=9.2,
    )
    for _, y, _, _ in materializations:
        arrow(ax, (8.63, y + 0.52), (9.37, 4.68), color=GRAY, linewidth=1.2)

    box(
        ax,
        12.3,
        3.85,
        2.4,
        1.65,
        "相对表现稳定？",
        "A、B、C 是否得出近似排序",
        facecolor=ORANGE_LIGHT,
        edgecolor=ORANGE,
        title_color=ORANGE,
        title_size=12,
        body_size=9.2,
    )
    arrow(ax, (11.68, 4.68), (12.27, 4.68), color=ORANGE)

    box(
        ax,
        12.45,
        6.05,
        2.1,
        0.85,
        "进入候选评测",
        facecolor=BLUE_LIGHT,
        edgecolor=BLUE,
        title_color=BLUE_DARK,
        title_size=11,
    )
    box(
        ax,
        12.45,
        2.05,
        2.1,
        0.85,
        "降权或暂不使用",
        facecolor=ORANGE_LIGHT,
        edgecolor=ORANGE,
        title_color=ORANGE,
        title_size=10.8,
    )
    arrow(ax, (13.5, 5.53), (13.5, 6.02), color=BLUE)
    arrow(ax, (13.5, 3.82), (13.5, 2.93), color=ORANGE)
    tag(ax, 14.75, 5.76, "是", color=BLUE, facecolor=BLUE_LIGHT, fontsize=9.5)
    tag(ax, 14.75, 3.35, "否", color=ORANGE, facecolor=ORANGE_LIGHT, fontsize=9.5)

    box(
        ax,
        3.35,
        1.15,
        2.5,
        0.95,
        "后来真实任务",
        facecolor=GREEN_LIGHT,
        edgecolor=GREEN,
        title_color=GREEN,
        title_size=11.5,
    )
    box(
        ax,
        6.55,
        1.15,
        2.65,
        0.95,
        "比较 Agent 相对表现",
        facecolor=GREEN_LIGHT,
        edgecolor=GREEN,
        title_color=GREEN,
        title_size=11,
    )
    box(
        ax,
        9.9,
        1.15,
        2.65,
        0.95,
        "校准方向与成题方法",
        facecolor=GREEN_LIGHT,
        edgecolor=GREEN,
        title_color=GREEN,
        title_size=10.8,
    )
    arrow(ax, (5.88, 1.62), (6.52, 1.62), color=GREEN)
    arrow(ax, (9.23, 1.62), (9.87, 1.62), color=GREEN)
    arrow(
        ax,
        (11.2, 2.13),
        (5.05, 3.97),
        color=GREEN,
        linewidth=1.5,
        connectionstyle="arc3,rad=0.23",
        linestyle="--",
    )

    tag(ax, 4.6, 3.45, "方向是否对", color=BLUE_DARK, facecolor=BLUE_LIGHT, fontsize=9.5)
    tag(ax, 7.58, 7.1, "成题是否走偏", color=BLUE_DARK, facecolor=BLUE_LIGHT, fontsize=9.5)
    tag(ax, 8.0, 0.95, "相对表现能否对上未来", color=GREEN, facecolor=GREEN_LIGHT, fontsize=9.5)

    footer(
        ax,
        "拟研究方法：任务生成模块不能自证正确，后来真实任务始终是外部校准锚",
        "第 8、9、10、11 轮",
        BLUE,
    )
    save(fig, "04-generator-validation")


def diagram_05() -> None:
    fig, ax = new_canvas(
        5,
        "Barcarolle 做什么：提供持续可对账的选择信号",
        "在 Agent 自动改进闭环里，Barcarolle 负责什么，不负责什么？",
        "拟议系统边界",
        BLUE,
    )

    # Inner optimization loop.
    box(
        ax,
        0.75,
        4.2,
        2.1,
        1.15,
        "当前 Agent",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=12,
    )
    box(
        ax,
        3.55,
        5.55,
        2.45,
        1.25,
        "自动改进系统",
        "提出新的 Agent 版本",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=11.5,
        body_size=9.2,
    )
    box(
        ax,
        6.7,
        5.55,
        2.3,
        1.25,
        "多个候选版本",
        "内容和数量可变化",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=11.5,
        body_size=9.2,
    )
    box(
        ax,
        9.7,
        5.35,
        3.1,
        1.65,
        "Barcarolle",
        "用本阶段冻结的评测比较",
        facecolor=BLUE,
        edgecolor=BLUE_DARK,
        title_color=BACKGROUND,
        body_color=BACKGROUND,
        title_size=13,
        body_size=9.8,
        linewidth=1.8,
    )
    box(
        ax,
        12.85,
        3.65,
        2.25,
        1.15,
        "选择下一版本",
        facecolor=BLUE_LIGHT,
        edgecolor=BLUE,
        title_color=BLUE_DARK,
        title_size=11.5,
    )
    box(
        ax,
        7.0,
        2.35,
        2.25,
        1.15,
        "进入下一轮",
        facecolor=BLUE_LIGHT,
        edgecolor=BLUE,
        title_color=BLUE_DARK,
        title_size=11.5,
    )

    arrow(ax, (2.88, 4.78), (3.52, 6.12), color=GRAY, connectionstyle="arc3,rad=-0.15")
    arrow(ax, (6.03, 6.18), (6.67, 6.18), color=GRAY)
    arrow(ax, (9.03, 6.18), (9.67, 6.18), color=BLUE)
    arrow(ax, (12.35, 5.32), (13.42, 4.83), color=BLUE, connectionstyle="arc3,rad=-0.12")
    arrow(ax, (13.0, 3.63), (9.28, 2.93), color=BLUE, connectionstyle="arc3,rad=0.13")
    arrow(ax, (6.97, 2.93), (2.82, 4.3), color=BLUE, connectionstyle="arc3,rad=0.14")
    ax.text(7.95, 4.2, "内层：连续优化", fontsize=11, color=BLUE, ha="center", fontweight=600)

    # External reality anchor and epoch refresh.
    rounded_rect(ax, 0.75, 0.95, 14.35, 0.95, facecolor=GREEN_LIGHT, edgecolor=GREEN, linewidth=1.5)
    ax.text(2.8, 1.42, "后来真实工作", fontsize=12, color=GREEN, fontweight=600, ha="center")
    ax.text(6.45, 1.42, "优化器不可见", fontsize=10.5, color=GREEN, ha="center")
    ax.text(9.35, 1.42, "审计与校准", fontsize=10.5, color=GREEN, ha="center")
    ax.text(12.65, 1.42, "阶段边界刷新评测", fontsize=10.5, color=GREEN, ha="center")
    arrow(ax, (7.45, 1.42), (8.05, 1.42), color=GREEN)
    arrow(ax, (10.35, 1.42), (11.02, 1.42), color=GREEN)
    arrow(
        ax,
        (12.65, 1.94),
        (11.6, 5.32),
        color=GREEN,
        linewidth=1.8,
        connectionstyle="arc3,rad=-0.18",
        linestyle="--",
    )
    tag(ax, 13.95, 2.65, "只在阶段边界", color=GREEN, facecolor=GREEN_LIGHT, fontsize=9.5)

    ax.text(
        1.0,
        3.1,
        "Barcarolle 负责：评价、选择、刷新",
        fontsize=11,
        color=BLUE,
        fontweight=600,
    )
    ax.text(1.0, 2.72, "不负责：替自动改进系统提出改动", fontsize=11, color=GRAY)

    footer(
        ax,
        "拟议系统边界：改动由外部系统提出；后来真实工作不能进入优化内环",
        "第 7、8、9 轮",
        BLUE,
    )
    save(fig, "05-barcarolle-loop")


def draw_schematic_curve(
    ax: Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    eval_color: str,
    future_points: list[tuple[float, float]],
) -> None:
    rounded_rect(ax, x, y, width, height, facecolor=BACKGROUND, edgecolor=BORDER, linewidth=1.0)
    ax.text(x + 0.18, y + height - 0.24, title, fontsize=10.5, fontweight=600, va="top")
    x0, y0 = x + 0.55, y + 0.42
    x1, y1 = x + width - 0.25, y + height - 0.62
    ax.plot([x0, x1], [y0, y0], color=GRID, linewidth=1.0)
    ax.plot([x0, x0], [y0, y1], color=GRID, linewidth=1.0)
    eval_x = [x0, x0 + (x1 - x0) * 0.32, x0 + (x1 - x0) * 0.67, x1]
    eval_y = [y0 + 0.16, y0 + (y1 - y0) * 0.45, y0 + (y1 - y0) * 0.72, y1 - 0.08]
    fut_x = [x0 + (x1 - x0) * px for px, _ in future_points]
    fut_y = [y0 + (y1 - y0) * py for _, py in future_points]
    ax.plot(eval_x, eval_y, color=eval_color, linewidth=2.4)
    ax.plot(fut_x, fut_y, color=GREEN, linewidth=2.4)
    ax.text(x1 - 0.02, eval_y[-1], "评测", color=eval_color, fontsize=9.2, ha="right", va="bottom")
    ax.text(x1 - 0.02, fut_y[-1], "真实", color=GREEN, fontsize=9.2, ha="right", va="top")
    ax.text((x0 + x1) / 2, y + 0.08, "优化轮数", color=MUTED, fontsize=8.8, ha="center")


def diagram_06() -> None:
    fig, ax = new_canvas(
        6,
        "怎样证明价值：只更换评测器",
        "怎样用一个对照实验同时验证问题、方法和预计效果？",
        "拟议实验 + 待验证目标",
        ORANGE,
    )

    box(
        ax,
        2.25,
        6.55,
        11.5,
        0.75,
        "同一初始 Agent  ·  同一自动优化器  ·  同样轮数与预算",
        facecolor=GRAY_LIGHT,
        edgecolor=GRAY,
        title_size=12,
    )
    tag(
        ax,
        8.0,
        6.15,
        "唯一变量：评测器",
        color=ORANGE,
        facecolor=ORANGE_LIGHT,
        fontsize=10,
    )

    tag(ax, 1.1, 5.38, "A 组", color=GRAY, facecolor=GRAY_LIGHT, fontsize=10)
    box(ax, 1.7, 5.0, 2.4, 0.9, "固定基准评测", facecolor=GRAY_LIGHT, edgecolor=GRAY, title_size=11)
    box(ax, 4.8, 5.0, 2.4, 0.9, "连续优化若干轮", facecolor=GRAY_LIGHT, edgecolor=GRAY, title_size=11)
    box(ax, 7.9, 5.0, 1.8, 0.9, "版本 A", facecolor=GRAY_LIGHT, edgecolor=GRAY, title_size=11)
    arrow(ax, (4.13, 5.45), (4.77, 5.45), color=GRAY)
    arrow(ax, (7.23, 5.45), (7.87, 5.45), color=GRAY)

    tag(ax, 1.1, 3.93, "B 组", color=BLUE, facecolor=BLUE_LIGHT, fontsize=10)
    box(
        ax,
        1.7,
        3.55,
        2.4,
        0.9,
        "Barcarolle",
        facecolor=BLUE_LIGHT,
        edgecolor=BLUE,
        title_color=BLUE_DARK,
        title_size=11.5,
    )
    box(ax, 4.8, 3.55, 2.4, 0.9, "连续优化若干轮", facecolor=BLUE_LIGHT, edgecolor=BLUE, title_color=BLUE_DARK, title_size=11)
    box(ax, 7.9, 3.55, 1.8, 0.9, "版本 B", facecolor=BLUE_LIGHT, edgecolor=BLUE, title_color=BLUE_DARK, title_size=11)
    arrow(ax, (4.13, 4.0), (4.77, 4.0), color=BLUE)
    arrow(ax, (7.23, 4.0), (7.87, 4.0), color=BLUE)

    box(
        ax,
        10.45,
        4.15,
        3.25,
        1.45,
        "最后一次性打开",
        "此前隐藏的后来真实任务",
        facecolor=GREEN_LIGHT,
        edgecolor=GREEN,
        title_color=GREEN,
        body_color=GREEN,
        title_size=12,
        body_size=10,
        linewidth=1.8,
    )
    arrow(ax, (9.73, 5.45), (10.42, 5.1), color=GREEN, connectionstyle="arc3,rad=0.1")
    arrow(ax, (9.73, 4.0), (10.42, 4.65), color=GREEN, connectionstyle="arc3,rad=-0.1")

    box(
        ax,
        14.05,
        3.4,
        1.35,
        2.9,
        "比较",
        "真实提升转化\n是否选对版本\n可靠指导轮数",
        facecolor=BACKGROUND,
        edgecolor=GREEN,
        title_color=GREEN,
        body_color=TEXT,
        title_size=11.5,
        body_size=9.2,
    )
    arrow(ax, (13.73, 4.86), (14.02, 4.86), color=GREEN)

    draw_schematic_curve(
        ax,
        1.15,
        0.95,
        6.3,
        2.0,
        "固定评测：可能较早脱钩",
        ORANGE,
        [(0.0, 0.18), (0.32, 0.38), (0.67, 0.43), (1.0, 0.36)],
    )
    draw_schematic_curve(
        ax,
        8.55,
        0.95,
        6.3,
        2.0,
        "Barcarolle 目标：更长时间同向",
        BLUE,
        [(0.0, 0.17), (0.32, 0.42), (0.67, 0.67), (1.0, 0.79)],
    )
    tag(
        ax,
        8.0,
        3.0,
        "目标效果，不是已有结果",
        color=ORANGE,
        facecolor=ORANGE_LIGHT,
        fontsize=10.5,
    )

    footer(
        ax,
        "拟议对照实验与目标走势：曲线无实验数值，不构成结果声明",
        "第 7、8、10、11 轮",
        ORANGE,
    )
    save(fig, "06-controlled-evaluator-test")


def diagram_07() -> None:
    fig, ax = new_canvas(
        7,
        "从研究起点到长期愿景：四个可证伪关卡",
        "怎样把长期愿景拆成逐步可验证的研究问题？",
        "拟议分阶段路线",
        BLUE,
    )

    stages = [
        (0.75, 1.65, "1  固定 Agent", "分数能代表\n后来真实任务？"),
        (4.45, 2.65, "2  候选版本池", "候选越多时\n能否少选错？"),
        (8.15, 3.65, "3  连续优化", "评测提升能否\n持续转成真实提升？"),
        (11.85, 4.65, "4  持续刷新", "可靠指导的轮数\n能否延长？"),
    ]
    for index, (x, y, title, body) in enumerate(stages):
        face = BLUE_LIGHT if index > 0 else GRAY_LIGHT
        edge = BLUE if index > 0 else GRAY
        title_color = BLUE_DARK if index > 0 else TEXT
        box(
            ax,
            x,
            y,
            3.0,
            1.8,
            title,
            body,
            facecolor=face,
            edgecolor=edge,
            title_color=title_color,
            body_color=TEXT,
            title_size=12,
            body_size=10.2,
            linewidth=1.6,
        )
        if index < len(stages) - 1:
            next_x, next_y, _, _ = stages[index + 1]
            arrow(
                ax,
                (x + 3.03, y + 0.9),
                (next_x - 0.03, next_y + 0.9),
                color=BLUE,
                linewidth=2.0,
                connectionstyle="arc3,rad=-0.05",
            )

    rounded_rect(ax, 0.75, 0.9, 14.1, 0.55, facecolor=GREEN_LIGHT, edgecolor=GREEN, linewidth=1.3)
    ax.text(
        7.8,
        1.18,
        "每一阶段最终都由后来真实工作对账",
        fontsize=11,
        color=GREEN,
        fontweight=600,
        ha="center",
        va="center",
    )
    for x, y, _, _ in stages:
        arrow(
            ax,
            (x + 1.5, 1.48),
            (x + 1.5, y - 0.03),
            color=GREEN,
            linewidth=1.3,
            linestyle="--",
        )

    box(
        ax,
        11.85,
        6.75,
        3.0,
        0.72,
        "自我演化 Agent 的现实校验",
        facecolor=BLUE,
        edgecolor=BLUE_DARK,
        title_color=BACKGROUND,
        title_size=10.8,
        linewidth=1.8,
    )
    arrow(ax, (13.35, 6.48), (13.35, 6.72), color=BLUE, linewidth=2.0)

    tag(
        ax,
        5.65,
        6.75,
        "第一阶段只测任务成败；时间、成本、交互结果后置",
        color=GRAY,
        facecolor=GRAY_LIGHT,
        fontsize=10.2,
    )

    footer(
        ax,
        "拟议研究路线：四级是验证关卡，不代表当前完成度",
        "第 6、8、9、11 轮",
        BLUE,
    )
    save(fig, "07-research-roadmap")


def main() -> None:
    configure_style()
    builders: tuple[Callable[[], None], ...] = (
        diagram_01,
        diagram_02,
        diagram_03,
        diagram_04,
        diagram_05,
        diagram_06,
        diagram_07,
    )
    for builder in builders:
        builder()


if __name__ == "__main__":
    main()
