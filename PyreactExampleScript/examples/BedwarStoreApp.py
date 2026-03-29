# -*- coding: utf-8 -*-

from pyreact import *

CURRENCY_DATA = {
    "铁锭": "iron_ingot",
    "金锭": "gold_ingot",
    "钻石": "diamond",
    "绿宝石": "emerald",
}

CATEGORIES = [
    {
        "快捷列表": [
            "羊毛", "石剑", "锁链套装", "镐子", "普通弓", "床虱", "爆炸的TNT",
            "木板", "铁剑", "铁套装", "斧头", "金苹果",
            "硬化粘土", "钻石剑", "钻石套装", "剪刀", "箭", "水桶"
        ]
    },
    {
        "方块": [
            "羊毛", "樱花树叶", "硬化粘土", "防爆玻璃", "末地石", "梯子", "木板", "黑曜石"
        ]
    },
    {
        "利剑": [
            "石剑", "铁剑", "钻石剑", "击退棒"
        ]
    },
    {
        "弓箭": [
            "普通弓", "力量 附魔弓", "力量I 冲击I 附魔弓", "箭"
        ]
    },
    {
        "防具": [
            "锁链套装", "铁套装", "钻石套装"
        ]
    },
    {
        "工具": [
            "剪刀", "镐子", "斧头"
        ]
    },
    {
        "酿造": [
            "速度药水", "跳跃提升药水", "隐身药水"
        ]
    },
    {
        "道具": [
            "金苹果", "床虱", "梦境守护者", "烈焰弹", "爆炸的TNT", "末影珍珠",
            "水桶", "搭桥蛋", "神奇牛奶", "干海绵", "紧凑型防御塔"
        ]
    },
]

GOODS_DATA = {
    # === 方块 ===
    "羊毛": {"name": "羊毛", "count": 16, "price": 4, "currency": "铁锭", "identifier": "wool"},
    "樱花树叶": {"name": "樱花树叶", "count": 15, "price": 4, "currency": "铁锭", "identifier": "cherry_leaves"},
    "硬化粘土": {"name": "硬化粘土", "count": 16, "price": 12, "currency": "铁锭", "identifier": "terracotta"},
    "防爆玻璃": {"name": "防爆玻璃", "count": 8, "price": 12, "currency": "铁锭", "identifier": "glass"},
    "末地石": {"name": "末地石", "count": 12, "price": 24, "currency": "铁锭", "identifier": "end_stone"},
    "梯子": {"name": "梯子", "count": 16, "price": 4, "currency": "铁锭", "identifier": "ladder"},
    "木板": {"name": "木板", "count": 16, "price": 4, "currency": "金锭", "identifier": "oak_planks"},
    "黑曜石": {"name": "黑曜石", "count": 4, "price": 4, "currency": "绿宝石", "identifier": "obsidian"},

    # === 利剑 ===
    "石剑": {"name": "石剑", "price": 10, "currency": "铁锭", "identifier": "stone_sword"},
    "铁剑": {"name": "铁剑", "price": 7, "currency": "金锭", "identifier": "iron_sword"},
    "钻石剑": {"name": "钻石剑", "price": 3, "currency": "绿宝石", "identifier": "diamond_sword"},
    "击退棒": {"name": "击退棒", "price": 5, "currency": "金锭", "identifier": "stick"},

    # === 弓箭 ===
    "普通弓": {"name": "普通弓", "price": 12, "currency": "金锭", "identifier": "bow"},
    "力量 附魔弓": {"name": "力量 附魔弓", "price": 24, "currency": "金锭", "identifier": "bow"},
    "力量I 冲击I 附魔弓": {"name": "冲击附魔弓", "price": 6, "currency": "绿宝石", "identifier": "bow"},
    "箭": {"name": "箭", "count": 6, "price": 2, "currency": "金锭", "identifier": "arrow"},

    # === 防具 ===
    "锁链套装": {"name": "锁链套装", "price": 40, "currency": "铁锭", "identifier": "chainmail_leggings"},
    "铁套装": {"name": "铁套装", "price": 12, "currency": "金锭", "identifier": "iron_leggings"},
    "钻石套装": {"name": "钻石套装", "price": 6, "currency": "绿宝石", "identifier": "diamond_leggings"},

    # === 工具 ===
    "剪刀": {"name": "剪刀", "price": 20, "currency": "铁锭", "identifier": "shears"},
    "镐子": {"name": "镐子", "price": 10, "currency": "铁锭", "identifier": "wooden_pickaxe"},
    "斧头": {"name": "斧头", "price": 10, "currency": "铁锭", "identifier": "wooden_axe"},

    # === 酿造 ===
    "速度药水": {"name": "速度药水", "price": 1, "currency": "绿宝石", "identifier": "potion"},
    "跳跃提升药水": {"name": "跳跃提升药水", "price": 1, "currency": "绿宝石", "identifier": "potion"},
    "隐身药水": {"name": "隐身药水", "price": 2, "currency": "绿宝石", "identifier": "potion"},

    # === 道具 ===
    "金苹果": {"name": "金苹果", "price": 3, "currency": "金锭", "identifier": "golden_apple"},
    "床虱": {"name": "床虱", "price": 40, "currency": "铁锭", "identifier": "snowball"},
    "梦境守护者": {"name": "梦境守护者", "price": 120, "currency": "铁锭", "identifier": "iron_golem_spawn_egg"},
    "烈焰弹": {"name": "烈焰弹", "price": 40, "currency": "铁锭", "identifier": "fire_charge"},
    "爆炸的TNT": {"name": "爆炸的TNT", "price": 8, "currency": "金锭", "identifier": "tnt"},
    "末影珍珠": {"name": "末影珍珠", "price": 4, "currency": "绿宝石", "identifier": "ender_pearl"},
    "水桶": {"name": "水桶", "price": 3, "currency": "金锭", "identifier": "water_bucket"},
    "搭桥蛋": {"name": "搭桥蛋", "price": 1, "currency": "绿宝石", "identifier": "egg"},
    "神奇牛奶": {"name": "神奇牛奶", "price": 4, "currency": "金锭", "identifier": "milk_bucket"},
    "干海绵": {"name": "干海绵", "count": 4, "price": 6, "currency": "金锭", "identifier": "sponge"},
    "紧凑型防御塔": {"name": "紧凑型防御塔", "price": 24, "currency": "铁锭", "identifier": "chest"},
}


@Component
def HorizontalItemCard(goods_data, onClick):
    return Button(
        style=Style(
            width=160,
            height=42,
            padding=8,
            alignItems=AlignItems.center,
            flexDirection=FlexDirection.row
        ),
        onClick=onClick,
        buttonBuilder=lambda state: Image(
            style=Style(
                height="100%",
                width="100%",
                opacity=0.3 if state == ButtonState.default else 0.6,
            ),
            color=Color.fromARGB(1.0, 39, 18, 19)
        ),
        children=[
            Item(
                style=Style(
                    height=22,
                    width=22,
                ),
                identifier="minecraft:" + goods_data["identifier"],
                children=[
                    Label(
                        style=Style(
                            position=Position.absolute,
                            right=-2,
                            bottom=-2,
                        ),
                        shadow=True,
                        content=str(goods_data.get("count", '') if goods_data.get("count", 0) > 1 else '')
                    )
                ]
            ),
            Panel(
                style=Style(
                    marginLeft=8
                ),
                children=[
                    Label(
                        style=Style(
                            marginBottom=2,
                        ),
                        content=str(goods_data["name"]),
                        fontSize=20,
                    ),
                    Label(
                        color=Colors.grey,
                        content="我是" + str(goods_data["name"]) + "的介绍"
                    )
                ]
            ),
            Panel(
                style=Style(
                    flex=1
                )
            ),
            Item(
                style=Style(height=16, width=16, marginRight=3, alignSelf=AlignItems.end),
                identifier="minecraft:" + CURRENCY_DATA[goods_data['currency']],
            ),
            Label(
                style=Style(alignSelf=AlignItems.end, marginBottom=3),
                content=str(goods_data["price"]),
                shadow=True,
            ),
        ]
    )

@Component
def VerticalItemCard(goods_data, onClick):
    return Button(
        style=Style(
            height=60,
            width=50,
            alignItems=AlignItems.center
        ),
        onClick=onClick,
        buttonBuilder=lambda state: Image(
            style=Style(
                height="100%",
                width="100%",
                opacity=0.3 if state == ButtonState.default else 0.6,
            ),
            color=Color.fromARGB(1.0, 39, 18, 19)
        ),
        children=[
            Panel(
                style=Style(
                    justifyContent=JustifyContent.center,
                    alignItems=AlignItems.center,
                    flex=1
                ),
                children=Item(
                    style=Style(
                        height=22,
                        width=22,
                    ),
                    identifier="minecraft:" + goods_data["identifier"],
                    children=[
                        Label(
                            style=Style(
                                position=Position.absolute,
                                right=-2,
                                bottom=-2,
                            ),
                            shadow=True,
                            content=str(goods_data.get("count", '') if goods_data.get("count", 0) > 1 else '')
                        )
                    ]
                )
            ),
            Image(
                style=Style(
                    width="100%",
                    height=16,
                    opacity=0.5,
                    justifyContent=JustifyContent.center,
                    alignItems=AlignItems.center,
                    flexDirection=FlexDirection.row,
                ),
                color=Colors.black,
                children=[
                    Item(
                        style=Style(height=14, width=14, marginRight=4),
                        identifier="minecraft:" + CURRENCY_DATA[goods_data["currency"]],
                    ),
                    Label(
                        content=str(goods_data["price"])
                    )
                ]
            )
        ]
    )


@Component
def BedwarStoreApp():
    selected_category_index, set_selected_category_index = useState(0)

    inv_currency = {
        "铁锭": 124,
        "金锭": 15,
        "钻石": 5,
        "绿宝石": 2
    }

    inv_currency_ui = []
    for key, value in inv_currency.items():
        inv_currency_ui.append(
            Item(
                style=Style(
                    height=16,
                    width=16
                ),
                identifier="minecraft:" + CURRENCY_DATA[key]
            )
        )
        inv_currency_ui.append(
            Label(
                style=Style(
                    marginLeft=4,
                    marginRight=6,
                ),
                fontSize=14,
                shadow=True,
                content=str(value),
            )
        )

    category_list_ui = []
    for i, category in enumerate(CATEGORIES):
        key = category.keys()[0]
        category_list_ui.append(
            Button(
                style=Style(
                    marginBottom=6,
                    height=28,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                buttonBuilder=lambda state, selected=CATEGORIES[selected_category_index].keys()[0] == key: Image(
                    style=Style(
                        height="100%",
                        width="100%",
                        opacity=0.3 if state == ButtonState.default else 0.6,
                    ),
                    color=Color.fromARGB(1.0, 152, 86, 86) if selected else Colors.black,
                ),
                onClick=lambda index=i: set_selected_category_index(index),
                children=[
                    Label(content=key),
                ]
            )
        )

    goods_ui = []
    if selected_category_index == 0:
        for i, goods in enumerate(CATEGORIES[selected_category_index].values()[0]):
            goods_data = GOODS_DATA[goods]
            goods_ui.append(
                Panel(
                    key="v-" + goods,
                    style=Style(
                        paddingRight=10,
                        paddingBottom=10,
                    ),
                    children=VerticalItemCard(
                        goods_data=goods_data,
                        onClick=lambda: None
                    )
                )
            )
    else:
        for i, goods in enumerate(CATEGORIES[selected_category_index].values()[0]):
            goods_data = GOODS_DATA[goods]
            goods_ui.append(
                Panel(
                    key="h-" + goods,
                    style=Style(
                        paddingRight=10,
                        paddingBottom=10,
                    ),
                    children=HorizontalItemCard(
                        goods_data=goods_data,
                        onClick=lambda: None
                    )
                )
            )


    return Image(
        style=Style(
            width="100%",
            height="100%",
            padding=8
        ),
        color=Color.fromARGB(1.0, 82, 71, 98),
        children=[
            # Appbar
            Panel(
                style=Style(
                    height=30,
                    width="100%",
                    flexDirection=FlexDirection.row,
                    alignItems=AlignItems.center,
                ),
                children=[
                    # Appbar 左侧
                    Panel(
                        children=[
                            # logo+title
                            Panel(
                                style=Style(
                                    flexDirection=FlexDirection.row,
                                ),
                                children=[
                                    # logo
                                    Item(
                                        style=Style(
                                            height=20,
                                            width=20,
                                        ),
                                        identifier="minecraft:bed"
                                    ),
                                    # title
                                    Label(
                                        content="装备&道具 商店",
                                        fontSize=FontSize.large,
                                    )
                                ]
                            ),
                            # UI设置按钮
                            Button(
                                style=Style(
                                    marginLeft=20,
                                ),
                                buttonBuilder=lambda state: Panel(),
                                children=[
                                    Label(
                                        content="UI设置 >"
                                    )
                                ]
                            )
                        ]
                    ),
                    Panel(
                        style=Style(
                            flex=1
                        )
                    ),
                    # Appbar 右侧
                    Panel(
                        style=Style(
                            flexDirection=FlexDirection.row,
                            alignItems=AlignItems.center,
                        ),
                        children=inv_currency_ui + [
                            Button(
                                style=Style(
                                    width=22,
                                    height=22,
                                    alignItems=AlignItems.center,
                                    justifyContent=JustifyContent.center
                                ),
                                buttonBuilder=lambda state: Image(
                                    style=Style(width='100%', height='100%', opacity=0.5 if state == ButtonState.default else 0.2),
                                    color=Colors.black,
                                ),
                                children=[
                                    Label(
                                        content="x"
                                    )
                                ],
                            ),
                        ]
                    )
                ]
            ),
            # 主页面部分
            Panel(
                style=Style(
                    flexDirection=FlexDirection.row,
                    marginTop=8,
                    flex=1
                ),
                children=[
                    # 主页面左侧分类标签列表
                    Panel(
                        style=Style(
                            width=80,
                            marginLeft=16,
                            marginRight=18,
                            alignItems=AlignItems.stretch,
                        ),
                        children=category_list_ui
                    ),

                    # 主页面右侧商品界面
                    Panel(
                        style=Style(
                            flex=1,
                            height="100%",
                            marginRight=12
                        ),
                        children=[
                            Label(
                                content=CATEGORIES[selected_category_index].keys()[0],
                                linePadding=4
                            ),
                            Scroll(
                                style=Style(
                                    width="100%",
                                    flex=1,
                                    flexWrap=FlexWrap.wrap,
                                    flexDirection=FlexDirection.row,
                                ),
                                children=goods_ui
                            ),
                        ]

                    )
                ]
            )
        ]
    )