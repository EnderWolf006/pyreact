# -*- coding: utf-8 -*-

from pyreact import *


CURRENCY_ICON_MAP = {
    'diamond': 'minecraft:diamond',
    'emerald': 'minecraft:emerald',
}


PLAYER_BALANCE = {
    'diamond': 1280,
    'emerald': 36,
}


SKIN_GOODS = [
    {
        'id': 'forest_ranger',
        'name': '林地巡游者',
        'subtitle': '狼族主题皮肤',
        'entityIdentifier': 'minecraft:wolf',
        'price': 320,
        'currency': 'diamond',
        'scale': 1.2,
        'renderDepth': -18,
        'initRotY': 160,
        'accent': Color(0xFF22C55E),
        'rarity': '稀有',
        'desc': '以森林斥候为灵感的轻甲套装，适合做野外与冒险主题皮肤。',
        'tags': ['侦察', '轻甲', '森林'],
    },
    {
        'id': 'night_guard',
        'name': '夜幕守卫',
        'subtitle': '幻翼主题皮肤',
        'entityIdentifier': 'minecraft:phantom',
        'price': 18,
        'currency': 'emerald',
        'scale': 0.72,
        'renderDepth': -20,
        'initRotY': 160,
        'accent': Color(0xFF8B5CF6),
        'rarity': '史诗',
        'desc': '深色披风与蓝紫辉光的组合，适合夜行者、刺客或守卫题材。',
        'tags': ['夜行', '披风', '暗色'],
    },
    {
        'id': 'marsh_alchemist',
        'name': '沼泽药剂师',
        'subtitle': '青蛙主题皮肤',
        'entityIdentifier': 'minecraft:frog',
        'price': 240,
        'currency': 'diamond',
        'scale': 1.75,
        'renderDepth': -14,
        'initRotY': 160,
        'accent': Color(0xFFF59E0B),
        'rarity': '精选',
        'desc': '偏实验风格的配色，适合炼金、沼泽或魔法学徒类角色。',
        'tags': ['炼金', '轻喜剧', '冒险'],
    },
    {
        'id': 'snow_postman',
        'name': '雪境信使',
        'subtitle': '北极熊主题皮肤',
        'entityIdentifier': 'minecraft:polar_bear',
        'price': 12,
        'currency': 'emerald',
        'scale': 0.78,
        'renderDepth': -24,
        'initRotY': 160,
        'accent': Color(0xFF38BDF8),
        'rarity': '限定',
        'desc': '高亮白蓝配色，适合冬季活动、冰原阵营和节庆主题皮肤。',
        'tags': ['冬季', '信使', '清爽'],
    },
    {
        'id': 'redstone_helper',
        'name': '红石助手',
        'subtitle': '悦灵主题皮肤',
        'entityIdentifier': 'minecraft:allay',
        'price': 450,
        'currency': 'diamond',
        'scale': 2.2,
        'renderDepth': -10,
        'initRotY': 160,
        'accent': Color(0xFF60A5FA),
        'rarity': '传说',
        'desc': '轻盈灵动的科技精灵风格，适合红石、工坊和助手题材。',
        'tags': ['科技', '助手', '灵动'],
    },
]


def _button_fill(default_color, hover_color, pressed_color):
    def builder(state):
        color_map = {
            ButtonState.default: default_color,
            ButtonState.hover: hover_color,
            ButtonState.pressed: pressed_color,
        }
        return Image(
            style=Style(width='100%', height='100%'),
            color=color_map.get(state, default_color),
        )
    return builder


def _currency_label(currency_key):
    if currency_key == 'diamond':
        return '钻石'
    return '绿宝石'


@Component
def BalanceBadge(currency_key, amount):
    return Image(
        key='balance_%s' % currency_key,
        style=Style(
            height=24,
            width=72,
            marginLeft=6,
            paddingLeft=8,
            paddingRight=8,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.flexStart,
            flexDirection=FlexDirection.row,
        ),
        color=Color(0x66233455),
        children=[
            Item(
                style=Style(width=14, height=14, marginRight=4),
                identifier=CURRENCY_ICON_MAP[currency_key],
            ),
            Label(
                color=Colors.white,
                content='%s %s' % (_currency_label(currency_key), amount),
            ),
        ],
    )


@Component
def SkinListItem(goods_data, is_selected, onClick):
    if is_selected:
        default_color = Color(0xCC1D4ED8)
        hover_color = Color(0xCC2563EB)
        pressed_color = Color(0xCC1E40AF)
    else:
        default_color = Color(0x99334155)
        hover_color = Color(0x99475569)
        pressed_color = Color(0x991E293B)

    return Button(
        key=goods_data['id'],
        style=Style(
            width='100%',
            height=56,
            marginBottom=8,
            paddingLeft=10,
            paddingRight=10,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.spaceBetween,
            flexDirection=FlexDirection.row,
        ),
        buttonBuilder=_button_fill(default_color, hover_color, pressed_color),
        onClick=onClick,
        children=[
            Panel(
                style=Style(flexDirection=FlexDirection.column),
                children=[
                    Label(
                        color=Colors.white,
                        fontSize=13,
                        content=goods_data['name'],
                    ),
                    Label(
                        style=Style(marginTop=2),
                        color=Color(0xFFBFDBFE),
                        content=goods_data['subtitle'],
                    ),
                ],
            ),
            Panel(
                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                children=[
                    Item(
                        style=Style(width=14, height=14, marginRight=4),
                        identifier=CURRENCY_ICON_MAP[goods_data['currency']],
                    ),
                    Label(
                        color=Colors.white,
                        shadow=True,
                        content=str(goods_data['price']),
                    ),
                ],
            ),
        ],
    )


@Component
def TagChip(chip_key, text, accent):
    return Image(
        key=chip_key,
        style=Style(
            height=18,
            marginRight=6,
            marginBottom=6,
            paddingLeft=6,
            paddingRight=6,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        color=accent.withOpacity(0.35),
        children=[
            Label(
                color=Colors.white,
                content=text,
            ),
        ],
    )


@Component
def SkinShopApp():
    selected_goods_id, set_selected_goods_id = useState(SKIN_GOODS[0]['id'])

    current_goods = SKIN_GOODS[0]
    for goods in SKIN_GOODS:
        if goods['id'] == selected_goods_id:
            current_goods = goods
            break

    skin_list_nodes = []
    for goods in SKIN_GOODS:
        skin_list_nodes.append(
            SkinListItem(
                key=goods['id'],
                goods_data=goods,
                is_selected=(goods['id'] == current_goods['id']),
                onClick=(lambda goods_id=goods['id']: set_selected_goods_id(goods_id)),
            )
        )

    balance_nodes = [
        BalanceBadge(currency_key='diamond', amount=PLAYER_BALANCE['diamond']),
        BalanceBadge(currency_key='emerald', amount=PLAYER_BALANCE['emerald']),
    ]

    tag_nodes = []
    for index, tag in enumerate(current_goods['tags']):
        tag_nodes.append(
            TagChip(
                key='%s_%s' % (current_goods['id'], index),
                chip_key='%s_%s' % (current_goods['id'], index),
                text=tag,
                accent=current_goods['accent'],
            )
        )

    can_afford = PLAYER_BALANCE[current_goods['currency']] >= current_goods['price']
    if can_afford:
        afford_text = '库存充足，可直接购买'
        afford_color = Color(0xFF4ADE80)
        buy_default = current_goods['accent']
        buy_hover = current_goods['accent'].withOpacity(0.85)
        buy_pressed = current_goods['accent'].withOpacity(0.7)
    else:
        afford_text = '余额不足，先去赚一点吧'
        afford_color = Color(0xFFF87171)
        buy_default = Color(0xFF475569)
        buy_hover = Color(0xFF64748B)
        buy_pressed = Color(0xFF334155)

    return Image(
        style=Style(
            width='100%',
            height='100%',
            paddingLeft=18,
            paddingRight=18,
            paddingTop=16,
            paddingBottom=16,
        ),
        color=Color(0xFF0F172A),
        children=[
            Panel(
                style=Style(
                    width='100%',
                    height='100%',
                ),
                children=[
                    Panel(
                        style=Style(
                            width='100%',
                            height=42,
                            flexDirection=FlexDirection.row,
                            alignItems=AlignItems.center,
                        ),
                        children=[
                            Panel(
                                style=Style(width=220, flexDirection=FlexDirection.column),
                                children=[
                                    Label(
                                        color=Colors.white,
                                        fontSize=FontSize.large,
                                        content='自定义皮肤商城',
                                    ),
                                    Label(
                                        style=Style(marginTop=2),
                                        color=Color(0xFF93C5FD),
                                        content='右侧为 PaperDoll 模型预览',
                                    ),
                                ],
                            ),
                            Panel(style=Style(flex=1)),
                            Panel(
                                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center, justifyContent=JustifyContent.flexEnd),
                                children=balance_nodes,
                            ),
                        ],
                    ),
                    Panel(
                        style=Style(
                            width='100%',
                            flex=1,
                            marginTop=12,
                            flexDirection=FlexDirection.row,
                        ),
                        children=[
                            Image(
                                style=Style(
                                    width=180,
                                    height='100%',
                                    padding=12,
                                ),
                                color=Color(0x66334155),
                                children=[
                                    Label(
                                        color=Color(0xFFE2E8F0),
                                        content='商品列表',
                                    ),
                                    Scroll(
                                        style=Style(width='100%', flex=1, marginTop=8),
                                        children=skin_list_nodes,
                                    ),
                                ],
                            ),
                            Panel(style=Style(width=12)),
                            Image(
                                style=Style(
                                    flex=1,
                                    height='100%',
                                    padding=14,
                                ),
                                color=Color(0x6633485F),
                                children=[
                                    Panel(
                                        style=Style(
                                            width='100%',
                                            flexDirection=FlexDirection.row,
                                            alignItems=AlignItems.center,
                                        ),
                                        children=[
                                            Panel(
                                                style=Style(flex=1),
                                                children=[
                                                    Label(
                                                        color=Colors.white,
                                                        fontSize=FontSize.large,
                                                        content=current_goods['name'],
                                                    ),
                                                    Label(
                                                        style=Style(marginTop=2),
                                                        color=current_goods['accent'],
                                                        content='%s · %s' % (current_goods['rarity'], current_goods['subtitle']),
                                                    ),
                                                ],
                                            ),
                                            Panel(
                                                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                                children=[
                                                    Item(
                                                        style=Style(width=16, height=16, marginRight=4),
                                                        identifier=CURRENCY_ICON_MAP[current_goods['currency']],
                                                    ),
                                                    Label(
                                                        color=Colors.white,
                                                        shadow=True,
                                                        content=str(current_goods['price']),
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    Panel(
                                        style=Style(
                                            width='100%',
                                            marginTop=8,
                                            alignItems=AlignItems.center,
                                            justifyContent=JustifyContent.center,
                                        ),
                                        children=[
                                            Image(
                                                style=Style(
                                                    width=132,
                                                    height=132,
                                                    alignItems=AlignItems.center,
                                                    justifyContent=JustifyContent.center,
                                                ),
                                                color=Color(0x551E293B),
                                                children=[
                                                    PaperDoll(
                                                        style=Style(width=120, height=120),
                                                        renderType='entity',
                                                        entityIdentifier=current_goods['entityIdentifier'],
                                                        scale=current_goods['scale'],
                                                        renderDepth=current_goods['renderDepth'],
                                                        initRotY=current_goods['initRotY'],
                                                        initRotX=20
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    Label(
                                        style=Style(marginTop=8),
                                        color=Color(0xFFE2E8F0),
                                        linePadding=2,
                                        content=current_goods['desc'],
                                    ),
                                    Panel(
                                        style=Style(
                                            marginTop=8,
                                            flexDirection=FlexDirection.row,
                                            flexWrap=FlexWrap.wrap,
                                        ),
                                        children=tag_nodes,
                                    ),
                                    Label(
                                        style=Style(marginTop=4),
                                        color=afford_color,
                                        content=afford_text,
                                    ),
                                    Panel(
                                        style=Style(
                                            marginTop=8,
                                            flexDirection=FlexDirection.row,
                                            alignItems=AlignItems.center,
                                        ),
                                        children=[
                                            Button(
                                                style=Style(
                                                    width=92,
                                                    height=32,
                                                    alignItems=AlignItems.center,
                                                    justifyContent=JustifyContent.center,
                                                    marginRight=8,
                                                ),
                                                buttonBuilder=_button_fill(buy_default, buy_hover, buy_pressed),
                                                onClick=lambda: None,
                                                children=[
                                                    Label(color=Colors.white, content='立即购买'),
                                                ],
                                            ),
                                            Button(
                                                style=Style(
                                                    width=92,
                                                    height=32,
                                                    alignItems=AlignItems.center,
                                                    justifyContent=JustifyContent.center,
                                                ),
                                                buttonBuilder=_button_fill(Color(0x99334155), Color(0x99475569), Color(0x991E293B)),
                                                onClick=lambda: None,
                                                children=[
                                                    Label(color=Colors.white, content='加入愿望单'),
                                                ],
                                            ),
                                        ],
                                    ),
                                    Label(
                                        style=Style(marginTop=6),
                                        color=Color(0xFF94A3B8),
                                        content='占位: %s' % current_goods['entityIdentifier'],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
