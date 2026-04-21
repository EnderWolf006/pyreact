# -*- coding: utf-8 -*-

"""AnimationDemo — Pyreact 声明式动画分区演示。

8 个独立区块，每个演示一种能力；顶部 tab 切换；切 tab 时 section 整体
slideIn / slideOut；每个 section 顶部都有黄色 "预期" Label。

## 架构注意

Pyreact 所有嵌套组件共享同一个 fiber，hook 数量必须每次 render 完全一致。
因此这里把所有 section 的 state 都在 ``AnimationDemo`` 顶层声明（lift state up），
section 组件做成纯函数：只按 props 渲染，不调用 ``useState``。
"""

from pyreact import (
    Animated,
    Animation,
    AlignItems,
    Color,
    Colors,
    Component,
    Easing,
    FilledButton,
    FlexDirection,
    FlexWrap,
    FontSize,
    Image,
    JustifyContent,
    Label,
    Panel,
    Position,
    Style,
    TextAlign,
    Transition,
    fadeIn,
    fadeOut,
    slideInUp,
    slideInDown,
    slideInLeft,
    slideInRight,
    slideOutUp,
    slideOutDown,
    slideOutLeft,
    slideOutRight,
    useState,
)


# ---- 颜色常量（模块级） ----

C_BG = Color(0xFF0B1220)
C_PANEL = Color(0xEE0F172A)
C_CARD = Color(0xEE1E293B)
C_CARD_SOFT = Color(0xCC1E293B)
C_ACCENT = Color(0xFF60A5FA)
C_HEADER = Color(0xFFBFDBFE)
C_TEXT = Color(0xFFE2E8F0)
C_MUTED = Color(0xFF94A3B8)
C_EXPECT = Color(0xFFFDE68A)
C_TRACK = Color(0xAA334155)
C_SLIDER = Color(0xFFFACC15)
C_CARD_DOT = Color(0xFF0B1220)

PAL_BLUE = (Color(0xFF2563EB), Color(0xFF3B82F6), Color(0xFF1D4ED8))
PAL_GREEN = (Color(0xFF16A34A), Color(0xFF22C55E), Color(0xFF15803D))
PAL_ORANGE = (Color(0xFFEA580C), Color(0xFFF97316), Color(0xFFC2410C))
PAL_RED = (Color(0xFFDC2626), Color(0xFFEF4444), Color(0xFFB91C1C))
PAL_PURPLE = (Color(0xFF7C3AED), Color(0xFF8B5CF6), Color(0xFF6D28D9))
PAL_SLATE = (Color(0xFF475569), Color(0xFF64748B), Color(0xFF334155))
PAL_TEAL = (Color(0xFF0D9488), Color(0xFF14B8A6), Color(0xFF0F766E))


@Component
def ColoredButton(text=u'', onClick=None, palette=None, width=72):
    default_c, hover_c, pressed_c = palette or PAL_BLUE
    return FilledButton(
        style=Style(
            width=width,
            height=24,
            marginLeft=3,
            marginRight=3,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        default=default_c,
        hover=hover_c,
        pressed=pressed_c,
        onClick=onClick,
        children=[Label(content=text, color=Colors.white, shadow=True)],
    )


@Component
def TabButton(text=u'', active=False, onClick=None):
    palette = PAL_BLUE if active else PAL_SLATE
    return FilledButton(
        style=Style(
            width=78, height=28,
            marginLeft=3, marginRight=3,
            marginTop=3, marginBottom=3,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        default=palette[0],
        hover=palette[1],
        pressed=palette[2],
        onClick=onClick,
        children=[Label(content=text, color=Colors.white, shadow=True)],
    )


@Component
def SectionCard(title=u'', expected=u'', body=None):
    if body is None:
        body = []
    return Panel(
        style=Style(
            width=560,
            marginTop=4,
            paddingTop=10,
            paddingBottom=12,
            paddingLeft=14,
            paddingRight=14,
        ),
        children=[
            Image(
                style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                color=C_PANEL,
            ),
            Label(content=title, color=C_ACCENT, fontSize=FontSize.large, shadow=True),
            Label(content=u'预期：' + expected, color=C_EXPECT),
            Panel(
                style=Style(marginTop=8, alignItems=AlignItems.center),
                children=body,
            ),
        ],
    )


# -------------------------------------------------------------
# §1 基础淡入淡出
# -------------------------------------------------------------

@Component
def DemoFade(visible=False, onToggle=None):
    card = None
    if visible:
        card = Animated(
            key='fade_card',
            enter=fadeIn(duration=300),
            exit=fadeOut(duration=250),
            children=Panel(
                style=Style(
                    width=300, height=50,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=[
                    Image(
                        style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                        color=C_CARD,
                    ),
                    Label(content=u'✓ 我 fadeIn 了，再点按钮看 fadeOut', color=C_TEXT),
                ],
            ),
        )
    slot_children = [card] if card is not None else [
        Label(content=u'（当前隐藏；点"显示"看 300ms 渐入）', color=C_MUTED),
    ]
    return SectionCard(
        title=u'§1 基础淡入淡出',
        expected=u'点击按钮 → 卡片 300ms fadeIn / 250ms fadeOut；出场期间节点保活直到动画结束',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, marginBottom=6),
                children=[
                    ColoredButton(
                        text=(u'点击隐藏' if visible else u'点击显示'),
                        onClick=onToggle,
                        palette=PAL_BLUE,
                        width=100,
                    ),
                ],
            ),
            Panel(
                style=Style(
                    width=320, height=60,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=slot_children,
            ),
        ],
    )


# -------------------------------------------------------------
# §2 四向滑入
# -------------------------------------------------------------

SLIDE_TABLE = (
    ('up',    slideInUp,    slideOutDown,  u'↑ 从下方滑入'),
    ('down',  slideInDown,  slideOutUp,    u'↓ 从上方滑入'),
    ('left',  slideInLeft,  slideOutRight, u'← 从右侧滑入'),
    ('right', slideInRight, slideOutLeft,  u'→ 从左侧滑入'),
)


def _slide_entry(direction):
    for name, in_fn, out_fn, label in SLIDE_TABLE:
        if name == direction:
            return in_fn, out_fn, label
    return slideInUp, slideOutDown, u'↑'


@Component
def DemoSlide(direction='up', onChange=None):
    in_fn, out_fn, desc = _slide_entry(direction)

    def make_handler(d):
        return lambda: onChange(d) if onChange else None

    return SectionCard(
        title=u'§2 四向滑入',
        expected=u'点方向键 → 面板先 slideOut 原方向、再 slideIn 新方向（key=direction 驱动 enter/exit）',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, marginBottom=6),
                children=[
                    ColoredButton(u'上', make_handler('up'), PAL_BLUE, 50),
                    ColoredButton(u'下', make_handler('down'), PAL_BLUE, 50),
                    ColoredButton(u'左', make_handler('left'), PAL_BLUE, 50),
                    ColoredButton(u'右', make_handler('right'), PAL_BLUE, 50),
                ],
            ),
            Panel(
                style=Style(
                    width=320, height=64,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=[
                    Animated(
                        key='slide_' + direction,
                        enter=in_fn(distance=30, duration=320, easing=Easing.easeOutCubic),
                        exit=out_fn(distance=30, duration=220, easing=Easing.easeInQuad),
                        children=Panel(
                            style=Style(
                                width=280, height=52,
                                alignItems=AlignItems.center,
                                justifyContent=JustifyContent.center,
                            ),
                            children=[
                                Image(
                                    style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                                    color=C_CARD,
                                ),
                                Label(content=desc, color=C_TEXT),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


# -------------------------------------------------------------
# §3 animate opacity
# -------------------------------------------------------------

@Component
def DemoAnimateOpacity(level=5, onInc=None, onDec=None):
    opacity = max(0.0, min(1.0, level * 0.2))
    return SectionCard(
        title=u'§3 连续过渡 opacity',
        expected=u'+ / − 调节 → opacity 从当前值 250ms easeOut 平滑过渡到目标值（非瞬切）',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center, marginBottom=6),
                children=[
                    ColoredButton(u'- 0.2', onDec, PAL_ORANGE, 60),
                    Label(
                        style=Style(width=80, height=24, marginLeft=6, marginRight=6),
                        content=u'α = %.1f' % opacity,
                        color=C_TEXT,
                        textAlign=TextAlign.center,
                    ),
                    ColoredButton(u'+ 0.2', onInc, PAL_GREEN, 60),
                ],
            ),
            Panel(
                style=Style(
                    width=320, height=54,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=[
                    Animated(
                        animate=Transition(
                            values={"opacity": opacity},
                            duration=250,
                            easing=Easing.easeOutQuad,
                        ),
                        children=Panel(
                            style=Style(
                                width=280, height=40,
                                alignItems=AlignItems.center,
                                justifyContent=JustifyContent.center,
                            ),
                            children=[
                                Image(
                                    style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                                    color=Color(0xFF2563EB),
                                ),
                                Label(content=u'调整上方按钮看平滑过渡', color=Colors.white, shadow=True),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


# -------------------------------------------------------------
# §4 animate translateX
# -------------------------------------------------------------

TRANSLATE_X_MAP = {'left': -100.0, 'center': 0.0, 'right': 100.0}


@Component
def DemoAnimateTranslate(pos='center', onChange=None):
    tx = TRANSLATE_X_MAP.get(pos, 0.0)

    def make_handler(p):
        return lambda: onChange(p) if onChange else None

    return SectionCard(
        title=u'§4 连续过渡 translateX',
        expected=u'点 左/中/右 → 滑块 translateX 400ms easeInOut 平滑过渡（叠加在 layout 位置上）',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, marginBottom=6),
                children=[
                    ColoredButton(u'← 左', make_handler('left'), PAL_PURPLE, 60),
                    ColoredButton(u'● 中', make_handler('center'), PAL_PURPLE, 60),
                    ColoredButton(u'右 →', make_handler('right'), PAL_PURPLE, 60),
                ],
            ),
            Panel(
                style=Style(
                    width=320, height=54,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=[
                    Image(
                        style=Style(
                            width=260, height=6,
                            position=Position.absolute, top=24, left=30,
                        ),
                        color=C_TRACK,
                    ),
                    Animated(
                        animate=Transition(
                            values={"translateX": tx},
                            duration=400,
                            easing=Easing.easeInOutQuad,
                        ),
                        children=Panel(
                            style=Style(
                                width=32, height=32,
                                alignItems=AlignItems.center,
                                justifyContent=JustifyContent.center,
                            ),
                            children=[
                                Image(
                                    style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                                    color=C_SLIDER,
                                ),
                                Label(content=u'●', color=C_CARD_DOT),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


# -------------------------------------------------------------
# §5 animate width
# -------------------------------------------------------------

WIDTH_MAP = (
    ('compact',  120, u'紧凑'),
    ('normal',   220, u'常规'),
    ('expanded', 320, u'展开'),
)


def _width_for(mode):
    for name, w, _ in WIDTH_MAP:
        if name == mode:
            return w
    return 220


@Component
def DemoAnimateWidth(mode='normal', onChange=None):
    cur_w = _width_for(mode)

    def make_handler(m):
        return lambda: onChange(m) if onChange else None

    buttons = []
    for name, _, label in WIDTH_MAP:
        palette = PAL_TEAL if name == mode else PAL_SLATE
        buttons.append(ColoredButton(label, make_handler(name), palette, 60))

    return SectionCard(
        title=u'§5 连续过渡 width',
        expected=u'切换紧凑/常规/展开 → Image 宽度 350ms easeOutCubic 拉伸（style.width 同步让 layout 一致）',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, marginBottom=6),
                children=buttons,
            ),
            Panel(
                style=Style(
                    width=340, height=50,
                    flexDirection=FlexDirection.row,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.flexStart,
                    paddingLeft=10,
                ),
                children=[
                    Animated(
                        animate=Transition(
                            values={"width": cur_w},
                            duration=350,
                            easing=Easing.easeOutCubic,
                        ),
                        children=Image(
                            style=Style(width=cur_w, height=30),
                            color=Color(0xFF14B8A6),
                        ),
                    ),
                ],
            ),
        ],
    )


# -------------------------------------------------------------
# §6 列表增删
# -------------------------------------------------------------

@Component
def DemoList(items=None, onAdd=None, onRemove=None, onClear=None):
    if items is None:
        items = []

    row_children = []
    for name in items:
        def make_remover(n):
            return lambda: onRemove(n) if onRemove else None
        row_children.append(
            Animated(
                key=u'item_' + name,
                enter=slideInUp(distance=16, duration=280),
                exit=fadeOut(duration=200),
                children=Panel(
                    style=Style(
                        width=280, height=28,
                        marginTop=3, marginBottom=3,
                        flexDirection=FlexDirection.row,
                        alignItems=AlignItems.center,
                        justifyContent=JustifyContent.spaceBetween,
                        paddingLeft=10, paddingRight=6,
                    ),
                    children=[
                        Image(
                            style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                            color=C_CARD_SOFT,
                        ),
                        Label(content=name, color=C_TEXT),
                        ColoredButton(u'✕', make_remover(name), PAL_RED, 32),
                    ],
                ),
            )
        )

    if not row_children:
        row_children.append(
            Label(content=u'（列表为空，点"添加"看 slideInUp）', color=C_MUTED),
        )

    return SectionCard(
        title=u'§6 列表增删 + key',
        expected=u'添加时每项 slideInUp(280ms)；删除时 fadeOut(200ms) 再移除；列表中间删除不会串动画（靠 key）',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, marginBottom=6),
                children=[
                    ColoredButton(u'添加一项', onAdd, PAL_GREEN, 80),
                    ColoredButton(u'全部清空', onClear, PAL_RED, 80),
                ],
            ),
            Panel(
                style=Style(
                    width=300,
                    alignItems=AlignItems.center,
                    paddingTop=2, paddingBottom=2,
                ),
                children=row_children,
            ),
        ],
    )


# -------------------------------------------------------------
# §7 自定义 Animation（回弹）
# -------------------------------------------------------------

@Component
def DemoBouncy(show=False, onToggle=None):
    card = None
    if show:
        card = Animated(
            key='bouncy_card',
            enter=Animation(
                duration=600,
                easing=Easing.easeOutBack,
                from_={"opacity": 0.0, "translateY": 40.0},
                to={"opacity": 1.0, "translateY": 0.0},
            ),
            exit=Animation(
                duration=300,
                easing=Easing.easeInQuad,
                from_={"opacity": 1.0, "translateY": 0.0},
                to={"opacity": 0.0, "translateY": 40.0},
            ),
            children=Panel(
                style=Style(
                    width=320, height=50,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=[
                    Image(
                        style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                        color=Color(0xFFFB923C),
                    ),
                    Label(content=u'easeOutBack 轻微过冲回弹', color=Colors.white, shadow=True),
                ],
            ),
        )
    slot_children = [card] if card is not None else [
        Label(content=u'（隐藏中；点按钮看 600ms 回弹入场）', color=C_MUTED),
    ]
    return SectionCard(
        title=u'§7 自定义 Animation + easeOutBack',
        expected=u'入场 600ms easeOutBack（有过冲）+ translateY 40→0；出场 300ms easeIn 快速收起',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, marginBottom=6),
                children=[
                    ColoredButton(
                        (u'点击收起' if show else u'点击弹出'),
                        onToggle, PAL_ORANGE, 100,
                    ),
                ],
            ),
            Panel(
                style=Style(
                    width=340, height=64,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=slot_children,
            ),
        ],
    )


# -------------------------------------------------------------
# §8 级联 stagger
# -------------------------------------------------------------

STAGGER_COUNT = 5
STAGGER_COLORS = (
    Color(0xFFEF4444),
    Color(0xFFF97316),
    Color(0xFFFACC15),
    Color(0xFF22C55E),
    Color(0xFF60A5FA),
)


@Component
def DemoStagger(seed=0, onReplay=None):
    cards = []
    i = 0
    while i < STAGGER_COUNT:
        delay_ms = i * 90
        color = STAGGER_COLORS[i]
        cards.append(
            Animated(
                key=u'stagger_%d_%d' % (seed, i),
                enter=Animation(
                    duration=420,
                    delay=delay_ms,
                    easing=Easing.easeOutCubic,
                    from_={"opacity": 0.0, "translateY": 24.0},
                    to={"opacity": 1.0, "translateY": 0.0},
                ),
                children=Panel(
                    style=Style(
                        width=50, height=50,
                        marginLeft=4, marginRight=4,
                        alignItems=AlignItems.center,
                        justifyContent=JustifyContent.center,
                    ),
                    children=[
                        Image(
                            style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                            color=color,
                        ),
                        Label(content=u'%d' % (i + 1), color=Colors.white, shadow=True, fontSize=FontSize.large),
                    ],
                ),
            )
        )
        i += 1

    return SectionCard(
        title=u'§8 级联 stagger',
        expected=u'点重播 → 5 张卡片按 delay 依次入场（每张 +90ms）：1 先出现，随后 2/3/4/5 波浪式跟上',
        body=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, marginBottom=6),
                children=[
                    ColoredButton(u'重新播放', onReplay, PAL_BLUE, 90),
                ],
            ),
            Panel(
                style=Style(
                    width=340, height=60,
                    flexDirection=FlexDirection.row,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=cards,
            ),
        ],
    )


# -------------------------------------------------------------
# 根组件 —— 顶层持有所有 state；section 无状态、按 props 渲染
# -------------------------------------------------------------

_TAB_LABELS = (
    ('fade',    u'§1 淡入'),
    ('slide',   u'§2 滑入'),
    ('opacity', u'§3 α 过渡'),
    ('tx',      u'§4 位移'),
    ('width',   u'§5 尺寸'),
    ('list',    u'§6 列表'),
    ('bouncy',  u'§7 回弹'),
    ('stagger', u'§8 stagger'),
)


@Component
def AnimationDemo():
    # ---- 所有 section 的 state 都提到顶层（固定 9 个 useState） ----
    tab, set_tab = useState('fade')
    fade_visible, set_fade_visible = useState(False)
    slide_dir, set_slide_dir = useState('up')
    opacity_level, set_opacity_level = useState(5)
    tx_pos, set_tx_pos = useState('center')
    width_mode, set_width_mode = useState('normal')
    list_state, set_list_state = useState({
        'items': [u'苹果', u'香蕉', u'樱桃'],
        'next_id': 4,
    })
    bouncy_show, set_bouncy_show = useState(False)
    stagger_seed, set_stagger_seed = useState(0)

    # ---- 事件回调 ----
    def toggle_fade():
        set_fade_visible(lambda v: not v)

    def change_slide(d):
        set_slide_dir(d)

    def opacity_inc():
        set_opacity_level(lambda v: min(5, v + 1))

    def opacity_dec():
        set_opacity_level(lambda v: max(0, v - 1))

    def change_tx(p):
        set_tx_pos(p)

    def change_width(m):
        set_width_mode(m)

    def list_add():
        def updater(prev):
            nid = prev.get('next_id', 1)
            new_items = list(prev.get('items') or [])
            new_items.append(u'水果 #%d' % nid)
            return {'items': new_items, 'next_id': nid + 1}
        set_list_state(updater)

    def list_remove(name):
        def updater(prev):
            out = []
            for v in prev.get('items') or []:
                if v != name:
                    out.append(v)
            return {'items': out, 'next_id': prev.get('next_id', 1)}
        set_list_state(updater)

    def list_clear():
        set_list_state(lambda prev: {'items': [], 'next_id': prev.get('next_id', 1)})

    def toggle_bouncy():
        set_bouncy_show(lambda v: not v)

    def replay_stagger():
        set_stagger_seed(lambda v: v + 1)

    # ---- Tab 按钮 ----
    tab_buttons = []
    for key, label in _TAB_LABELS:
        def make_select(k):
            return lambda: set_tab(k)
        tab_buttons.append(
            TabButton(text=label, active=(tab == key), onClick=make_select(key), key=u'tab_' + key)
        )

    # ---- 当前 section ----
    if tab == 'fade':
        section_node = DemoFade(visible=fade_visible, onToggle=toggle_fade)
    elif tab == 'slide':
        section_node = DemoSlide(direction=slide_dir, onChange=change_slide)
    elif tab == 'opacity':
        section_node = DemoAnimateOpacity(level=opacity_level, onInc=opacity_inc, onDec=opacity_dec)
    elif tab == 'tx':
        section_node = DemoAnimateTranslate(pos=tx_pos, onChange=change_tx)
    elif tab == 'width':
        section_node = DemoAnimateWidth(mode=width_mode, onChange=change_width)
    elif tab == 'list':
        section_node = DemoList(
            items=list_state.get('items') or [],
            onAdd=list_add,
            onRemove=list_remove,
            onClear=list_clear,
        )
    elif tab == 'bouncy':
        section_node = DemoBouncy(show=bouncy_show, onToggle=toggle_bouncy)
    elif tab == 'stagger':
        section_node = DemoStagger(seed=stagger_seed, onReplay=replay_stagger)
    else:
        section_node = DemoFade(visible=fade_visible, onToggle=toggle_fade)

    return Panel(
        style=Style(
            width='100%', height='100%',
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.flexStart,
            paddingTop=10, paddingBottom=10,
        ),
        children=[
            Image(
                style=Style(width='100%', height='100%', position=Position.absolute, top=0, left=0),
                color=C_BG,
            ),
            Animated(
                enter=fadeIn(duration=360),
                children=Panel(
                    style=Style(
                        width=640,
                        alignItems=AlignItems.center,
                    ),
                    children=[
                        Label(
                            content=u'Pyreact 声明式动画演示',
                            color=C_HEADER,
                            fontSize=FontSize.extraLarge,
                            shadow=True,
                        ),
                        Label(
                            content=u'点击上方 tab 切换 · 黄色是预期效果',
                            color=C_MUTED,
                        ),
                        Panel(
                            style=Style(
                                width=640,
                                flexDirection=FlexDirection.row,
                                flexWrap=FlexWrap.wrap,
                                alignItems=AlignItems.center,
                                justifyContent=JustifyContent.center,
                                marginTop=8,
                                marginBottom=6,
                            ),
                            children=tab_buttons,
                        ),
                        # 不再给整个 section 包 Animated(enter=slideInRight,exit=slideOutLeft)
                        # —— 之前的 section 级 exit 会在快速切 tab 时导致多个 section 的
                        # widget 同时 visible 重叠显示。section 内部仍然保留各自的 enter /
                        # exit（fadeCard / listItem / bouncy / stagger 等），切 tab 时旧
                        # section 瞬间消失、新 section 内部自己的动画接管。
                        Panel(
                            style=Style(
                                width=600, height=400,
                                alignItems=AlignItems.center,
                                justifyContent=JustifyContent.flexStart,
                                marginTop=4,
                            ),
                            children=[section_node],
                        ),
                    ],
                ),
            ),
        ],
    )
