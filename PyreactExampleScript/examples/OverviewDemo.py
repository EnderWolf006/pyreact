# -*- coding: utf-8 -*-

from pyreact import *


C_BG = Color(0xFF101828)
C_PANEL = Color(0xEE182235)
C_CARD = Color(0xFF243247)
C_TEXT = Color(0xFFE5ECF8)
C_MUTED = Color(0xFF9AA8BE)
C_ACCENT = Color(0xFF3DDC97)
C_BLUE = Color(0xFF3B82F6)
C_YELLOW = Color(0xFFF5C542)


@Component
def DemoCard(title=u'', body=None):
    if body is None:
        body = []
    return Panel(
        style=Style(width=280, height=122, margin=6, padding=10),
        children=[
            Image(
                style=Style(position=Position.absolute, top=0, right=0, bottom=0, left=0),
                color=C_PANEL,
            ),
            Label(content=title, color=C_ACCENT, fontSize=FontSize.large, shadow=True),
            Panel(style=Style(marginTop=8), children=body),
        ],
    )


@Component
def FilledButtonDemo(count=0, onClick=None):
    return DemoCard(
        title=u'FilledButton',
        body=[
            Label(content=u'纯色三态按钮', color=C_MUTED),
            FilledButton(
                style=Style(
                    width=150,
                    height=34,
                    marginTop=10,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                default=C_BLUE,
                hover=Color(0xFF2563EB),
                pressed=Color(0xFF1D4ED8),
                onClick=onClick,
                children=[Label(content=u'点击 %s' % count, color=Colors.white, shadow=True)],
            ),
        ],
    )


@Component
def ImageButtonDemo(onClick=None):
    def image_builder(src, state):
        return Image(
            src=src,
            nineSlice=(4, 4, 4, 4),
            color=Colors.white,
        )

    return DemoCard(
        title=u'ImageButton',
        body=[
            Label(content=u'图片三态按钮', color=C_MUTED),
            ImageButton(
                style=Style(
                    width=160,
                    height=34,
                    marginTop=10,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                default='textures/netease/common/button/default',
                hover='textures/netease/common/button/hover',
                pressed='textures/netease/common/button/pressed',
                imageBuilder=image_builder,
                onClick=onClick,
                children=[Label(content=u'图片按钮', color=Colors.white, shadow=True)],
            ),
        ],
    )


@Component
def AnimatedDemo(show=False, onToggle=None):
    sample = Label(content=u'点击显示动画', color=C_MUTED)
    if show:
        sample = Animated(
            key='overview_animated_block',
            enter=slideInUp(distance=16, duration=260),
            exit=fadeOut(duration=180),
            children=Panel(
                style=Style(
                    width=170,
                    height=32,
                    marginTop=8,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                children=[
                    Image(
                        style=Style(position=Position.absolute, top=0, right=0, bottom=0, left=0),
                        color=C_YELLOW,
                    ),
                    Label(content=u'Animated', color=Color(0xFF111827), shadow=True),
                ],
            ),
        )
    return DemoCard(
        title=u'Animated',
        body=[
            FilledButton(
                style=Style(
                    width=92,
                    height=26,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                default=Color(0xFF475569),
                hover=Color(0xFF64748B),
                pressed=Color(0xFF334155),
                onClick=onToggle,
                children=[Label(content=(u'隐藏' if show else u'显示'), color=Colors.white)],
            ),
            sample,
        ],
    )


@Component
def SliderDemo(value=36, onChange=None):
    return DemoCard(
        title=u'Slider',
        body=[
            Label(content=u'基础组件 + ref 触摸拖动', color=C_MUTED),
            Slider(
                style=Style(width=210, height=32, marginTop=8),
                value=value,
                min=0,
                max=100,
                step=10,
                onChange=onChange,
            ),
        ],
    )


@Component
def OverviewDemo():
    click_count, set_click_count = useState(0)
    animated_show, set_animated_show = useState(True)
    slider_value, set_slider_value = useState(36)

    def inc_count():
        set_click_count(lambda v: v + 1)

    def toggle_animated():
        set_animated_show(lambda v: not v)

    return Panel(
        style=Style(
            width='100%',
            height='100%',
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
            padding=14,
        ),
        children=[
            Image(
                style=Style(position=Position.absolute, top=0, right=0, bottom=0, left=0),
                color=C_BG,
            ),
            Panel(
                style=Style(width=620, alignItems=AlignItems.center),
                children=[
                    Label(
                        content=u'Composites Overview',
                        color=C_TEXT,
                        fontSize=FontSize.extraLarge,
                        shadow=True,
                    ),
                    Label(content=u'FilledButton / ImageButton / Animated / Slider', color=C_MUTED),
                    Panel(
                        style=Style(
                            width=600,
                            marginTop=12,
                            flexDirection=FlexDirection.row,
                            flexWrap=FlexWrap.wrap,
                            justifyContent=JustifyContent.center,
                        ),
                        children=[
                            FilledButtonDemo(count=click_count, onClick=inc_count),
                            ImageButtonDemo(onClick=inc_count),
                            AnimatedDemo(show=animated_show, onToggle=toggle_animated),
                            SliderDemo(value=slider_value, onChange=set_slider_value),
                        ],
                    ),
                ],
            ),
        ],
    )
