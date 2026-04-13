# -*- coding: utf-8 -*-

from pyreact import *


@Component
def ActionButton(text, default_color, hover_color, pressed_color, onClick):
    return FilledButton(
        style=Style(
            width=68,
            height=28,
            marginLeft=4,
            marginRight=4,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        default=default_color,
        hover=hover_color,
        pressed=pressed_color,
        onClick=onClick,
        children=[
            Label(
                content=text,
                color=Colors.white,
                shadow=True,
            )
        ],
    )


@Component
def CounterApp():
    count, set_count = useState(0)

    if count > 0:
        trend_text = '状态：正在累加'
        trend_color = Color(0xFF4ADE80)
    elif count < 0:
        trend_text = '状态：低于基线'
        trend_color = Color(0xFFF97316)
    else:
        trend_text = '状态：回到初始值'
        trend_color = Color(0xFF93C5FD)

    return Panel(
        style=Style(
            width='100%',
            height='100%',
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        children=[
            Image(
                style=Style(
                    width=220,
                    height=146,
                    paddingTop=16,
                    paddingBottom=16,
                    paddingLeft=16,
                    paddingRight=16,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.spaceBetween,
                ),
                color=Color(0xCC0F172A),
                children=[
                    Label(
                        color=Color(0xFFBFDBFE),
                        content='Pyreact Counter Demo',
                    ),
                    Label(
                        color=Colors.white,
                        fontSize=FontSize.large,
                        content=str(count),
                    ),
                    Label(
                        color=trend_color,
                        content=trend_text,
                    ),
                    Label(
                        style=Style(position=Position.relative, left=10, top=-2),
                        color=Color(0xFFFDE68A),
                        content='relative 偏移示例',
                    ),
                    Panel(
                        style=Style(
                            flexDirection=FlexDirection.row,
                            alignItems=AlignItems.center,
                            justifyContent=JustifyContent.center,
                        ),
                        children=[
                            ActionButton(
                                text='-1',
                                default_color=Color(0xFFB45309),
                                hover_color=Color(0xFFD97706),
                                pressed_color=Color(0xFF92400E),
                                onClick=lambda: set_count(count - 1),
                            ),
                            ActionButton(
                                text='重置',
                                default_color=Color(0xFF475569),
                                hover_color=Color(0xFF64748B),
                                pressed_color=Color(0xFF334155),
                                onClick=lambda: set_count(0),
                            ),
                            ActionButton(
                                text='+1',
                                default_color=Color(0xFF2563EB),
                                hover_color=Color(0xFF3B82F6),
                                pressed_color=Color(0xFF1D4ED8),
                                onClick=lambda: set_count(count + 1),
                            ),
                        ],
                    ),
                    Label(
                        color=Color(0xFF94A3B8),
                        content='演示 useState 与按钮事件联动',
                    ),
                ],
            )
        ],
    )
