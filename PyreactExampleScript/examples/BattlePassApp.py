# -*- coding: utf-8 -*-

from pyreact import *


PASS_PLANS = [
    {
        'id': 'free',
        'name': '普通版',
        'price': '免费',
        'accent': Color(0xFF60A5FA),
        'banner': Color(0xFF1D4ED8),
        'panel': Color(0xFF172554),
        'hint': '免费领取普通版奖励',
    },
    {
        'id': 'elite',
        'name': '进阶版',
        'price': '1200钻石',
        'accent': Color(0xFFFBBF24),
        'banner': Color(0xFFB45309),
        'panel': Color(0xFF78350F),
        'hint': '同时领取普通版与进阶专属奖励',
    },
]


MISSIONS = [
    {'id': 'daily_sign', 'title': '每日签到', 'desc': '主城签到 1 次', 'xp': 80, 'status': '已完成'},
    {'id': 'rank_win', 'title': '排位获胜', 'desc': '完成 2 场胜利', 'xp': 120, 'status': '进行中'},
    {'id': 'break_block', 'title': '资源采集', 'desc': '挖掘 96 个矿石', 'xp': 150, 'status': '进行中'},
    {'id': 'dungeon', 'title': '遗迹探索', 'desc': '通关 1 次地下城', 'xp': 180, 'status': '未开始'},
    {'id': 'team_up', 'title': '组队远征', 'desc': '组队完成 3 场对局', 'xp': 200, 'status': '未开始'},
    {'id': 'fishing', 'title': '渔获时间', 'desc': '钓起 12 个物品', 'xp': 90, 'status': '已完成'},
    {'id': 'boss', 'title': '首领挑战', 'desc': '击败 1 次世界首领', 'xp': 260, 'status': '进行中'},
    {'id': 'trade', 'title': '商队交易', 'desc': '完成 4 笔交易', 'xp': 110, 'status': '未开始'},
]


REWARD_ROWS = [
    {
        'level': 1,
        'xp': 100,
        'tag': '启程',
        'free': [
            {'id': 'bread', 'identifier': 'minecraft:bread', 'count': 12, 'name': '面包补给'},
            {'id': 'torch', 'identifier': 'minecraft:torch', 'count': 24, 'name': '火把箱'},
        ],
        'elite': [
            {'id': 'golden_apple', 'identifier': 'minecraft:golden_apple', 'count': 2, 'name': '金苹果'},
            {'id': 'lapis', 'identifier': 'minecraft:lapis_lazuli', 'count': 16, 'name': '青金石'},
        ],
    },
    {
        'level': 2,
        'xp': 180,
        'tag': '热门',
        'free': [
            {'id': 'iron_ingot', 'identifier': 'minecraft:iron_ingot', 'count': 18, 'name': '铁锭'},
            {'id': 'bow', 'identifier': 'minecraft:bow', 'count': 1, 'name': '战术弓'},
        ],
        'elite': [
            {'id': 'diamond', 'identifier': 'minecraft:diamond', 'count': 6, 'name': '钻石'},
            {'id': 'arrow', 'identifier': 'minecraft:arrow', 'count': 32, 'name': '箭矢包'},
        ],
    },
    {
        'level': 3,
        'xp': 360,
        'tag': '当前',
        'free': [
            {'id': 'cooked_beef', 'identifier': 'minecraft:cooked_beef', 'count': 16, 'name': '熟牛排'},
            {'id': 'shield', 'identifier': 'minecraft:shield', 'count': 1, 'name': '盾牌'},
        ],
        'elite': [
            {'id': 'emerald', 'identifier': 'minecraft:emerald', 'count': 8, 'name': '绿宝石'},
            {'id': 'totem', 'identifier': 'minecraft:totem_of_undying', 'count': 1, 'name': '不死图腾'},
        ],
    },
    {
        'level': 4,
        'xp': 540,
        'tag': '收藏',
        'free': [
            {'id': 'diamond_pickaxe', 'identifier': 'minecraft:diamond_pickaxe', 'count': 1, 'name': '钻石镐'},
            {'id': 'book', 'identifier': 'minecraft:book', 'count': 6, 'name': '附魔手册'},
        ],
        'elite': [
            {'id': 'amethyst', 'identifier': 'minecraft:amethyst_shard', 'count': 12, 'name': '紫水晶'},
            {'id': 'goat_horn', 'identifier': 'minecraft:goat_horn', 'count': 1, 'name': '山羊号角'},
        ],
    },
    {
        'level': 5,
        'xp': 720,
        'tag': '稀有',
        'free': [
            {'id': 'ender_pearl', 'identifier': 'minecraft:ender_pearl', 'count': 4, 'name': '末影珍珠'},
            {'id': 'obsidian', 'identifier': 'minecraft:obsidian', 'count': 10, 'name': '黑曜石'},
        ],
        'elite': [
            {'id': 'elytra', 'identifier': 'minecraft:elytra', 'count': 1, 'name': '鞘翅'},
            {'id': 'firework', 'identifier': 'minecraft:firework_rocket', 'count': 18, 'name': '烟花火箭'},
        ],
    },
    {
        'level': 6,
        'xp': 960,
        'tag': '终章',
        'free': [
            {'id': 'diamond_sword', 'identifier': 'minecraft:diamond_sword', 'count': 1, 'name': '钻石剑'},
            {'id': 'experience_bottle', 'identifier': 'minecraft:experience_bottle', 'count': 10, 'name': '经验瓶'},
        ],
        'elite': [
            {'id': 'netherite_ingot', 'identifier': 'minecraft:netherite_ingot', 'count': 1, 'name': '下界合金锭'},
            {'id': 'enchanted_golden_apple', 'identifier': 'minecraft:enchanted_golden_apple', 'count': 1, 'name': '附魔金苹果'},
        ],
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


def _reward_state_for_track(level, current_level, track_id, preview_plan_id):
    if track_id == 'elite' and preview_plan_id != 'elite':
        return '未解锁'
    if level < current_level:
        return '已领取'
    if level == current_level:
        return '可领取'
    return '未解锁'


def _reward_card_palette(track_id, reward_state, preview_plan_id):
    if reward_state == '已领取':
        if preview_plan_id == 'elite':
            return Color(0x99D97706), Colors.white
        return Color(0xCC3B82F6), Colors.white

    if track_id == 'free':
        if reward_state == '可领取':
            return Color(0xCC1d4ed8), Colors.white
        return Color(0x88607AA6), Color(0xFFE0F2FE)

    if reward_state == '可领取':
        return Color(0xCCF59E0B), Colors.white
    return Color(0x665B3A16), Color(0xFFF5E7B7)


def _mission_status_color(status):
    if status == '已完成':
        return Color(0xFF34D399)
    if status == '进行中':
        return Color(0xFFFBBF24)
    return Color(0xFF94A3B8)


def _claim_button_palette(track_id, reward_state):
    if reward_state == '已领取':
        return Color(0xFF166534), Color(0xFF15803D), Color(0xFF14532D), Colors.white
    if reward_state == '可领取':
        if track_id == 'elite':
            return Color(0xFFD97706), Color(0xFFF59E0B), Color(0xFFB45309), Colors.white
        return Color(0xFF2563EB), Color(0xFF3B82F6), Color(0xFF1D4ED8), Colors.white
    return Color(0xFF334155), Color(0xFF475569), Color(0xFF1F2937), Color(0xFFE2E8F0)


@Component
def RewardItemCard(card_key, reward, track_id, reward_state, preview_plan_id, width=26, height=26, item_size=15, margin_right=4):
    count_text = ''
    if reward.get('count', 0) > 1:
        count_text = str(reward.get('count', ''))

    card_bg, text_color = _reward_card_palette(track_id, reward_state, preview_plan_id)

    return Image(
        key=card_key,
        style=Style(
            width=width,
            height=height,
            marginRight=margin_right,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        color=card_bg,
        children=[
            Item(
                style=Style(width=item_size, height=item_size),
                identifier=reward['identifier'],
            ),
            Label(
                style=Style(position=Position.absolute, right=1, bottom=0),
                content=count_text,
                color=text_color,
                shadow=True,
            ),
        ],
    )


@Component
def RewardClaimButton(track_id, reward_state):
    default_color, hover_color, pressed_color, text_color = _claim_button_palette(track_id, reward_state)
    button_text = reward_state

    return Button(
        style=Style(
            width=44,
            height=22,
            marginLeft=12,
            marginRight=5,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        onClick=lambda: None,
        buttonBuilder=_button_fill(default_color, hover_color, pressed_color),
        children=[
            Label(content=button_text, color=text_color, shadow=True),
        ],
    )


@Component
def UnlockPreviewButton(is_elite, onClick):
    if is_elite:
        default_color = Color(0xCC7C3F12)
        hover_color = Color(0xCCD97706)
        pressed_color = Color(0xCC92400E)
        subtitle_nodes = [
            Label(content='已解锁 · 预览普通版', color=Color(0xFFFFF3C4), shadow=True),
        ]
        title_text = '预览普通版'
    else:
        default_color = Color(0xCCB45309)
        hover_color = Color(0xCCF59E0B)
        pressed_color = Color(0xCC92400E)
        subtitle_nodes = [
            Panel(
                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center, justifyContent=JustifyContent.center),
                children=[
                    Label(content='1200', color=Color(0xFFFFF3C4), shadow=True),
                    Item(
                        style=Style(width=12, height=12, marginLeft=3),
                        identifier='minecraft:diamond',
                    ),
                ],
            )
        ]
        title_text = '解锁进阶版'

    return Button(
        style=Style(
            width=124,
            height=36,
            marginRight=2,
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        onClick=onClick,
        buttonBuilder=_button_fill(default_color, hover_color, pressed_color),
        children=[
            Label(content=title_text, color=Colors.white, shadow=True),
        ] + subtitle_nodes,
    )


@Component
def MissionCard(mission):
    status_color = _mission_status_color(mission['status'])

    return Image(
        key=mission['id'],
        style=Style(
            width='100%',
            height=42,
            marginTop=6,
            paddingLeft=6,
            paddingRight=10,
            justifyContent=JustifyContent.center,
        ),
        color=Color(0xCC163456),
        children=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, justifyContent=JustifyContent.spaceBetween, alignItems=AlignItems.center),
                children=[
                    Label(content=mission['title'], color=Colors.white, shadow=True),
                    Label(content='+%s XP' % mission['xp'], color=Color(0xFFBAE6FD), shadow=True),
                ],
            ),
            Panel(
                style=Style(marginTop=2, flexDirection=FlexDirection.row, justifyContent=JustifyContent.spaceBetween, alignItems=AlignItems.center),
                children=[
                    Label(content=mission['desc'], color=Color(0xFFBFDBFE)),
                    Label(content=mission['status'], color=status_color),
                ],
            ),
        ],
    )


@Component
def RewardTrackRow(row, preview_plan_id, current_level, is_selected, onClick):
    selected_accent = PASS_PLANS[1]['accent'] if preview_plan_id == 'elite' else PASS_PLANS[0]['accent']
    row_color = selected_accent.withAlpha(60) if is_selected else Color(0xCC0F172A)

    free_state = _reward_state_for_track(row['level'], current_level, 'free', preview_plan_id)
    elite_state = _reward_state_for_track(row['level'], current_level, 'elite', preview_plan_id)
    row_claim_state = free_state
    if preview_plan_id == 'elite':
        row_claim_state = elite_state

    free_reward_nodes = []
    for reward in row['free']:
        free_reward_nodes.append(
            RewardItemCard(
                card_key='free_%s_%s' % (row['level'], reward['id']),
                reward=reward,
                track_id='free',
                reward_state=free_state,
                preview_plan_id=preview_plan_id,
                width=26,
                height=26,
                item_size=15,
                margin_right=4,
            )
        )

    elite_reward_nodes = []
    for reward in row['elite']:
        elite_reward_nodes.append(
            RewardItemCard(
                card_key='elite_%s_%s' % (row['level'], reward['id']),
                reward=reward,
                track_id='elite',
                reward_state=elite_state,
                preview_plan_id=preview_plan_id,
                width=26,
                height=26,
                item_size=15,
                margin_right=4,
            )
        )

    return Image(
        key='reward_row_%s' % row['level'],
        style=Style(
            width='100%',
            height=56,
            marginTop=6,
            paddingLeft=6,
            paddingRight=6,
            justifyContent=JustifyContent.center,
        ),
        onClick=onClick,
        color=row_color,
        children=[
            Panel(
                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                children=[
                    Image(
                        style=Style(width=34, height=38, alignItems=AlignItems.center, justifyContent=JustifyContent.center),
                        color=Color(0xCC020617),
                        children=[
                            Label(content='Lv.%s' % row['level'], color=Colors.white, shadow=True),
                            Label(style=Style(marginTop=1), content=row['tag'], color=selected_accent),
                        ],
                    ),
                    Panel(
                        style=Style(flex=1, marginLeft=7),
                        children=[
                            Panel(
                                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=[
                                    Label(content='XP %s' % row['xp'], color=Color(0xFFCBD5E1), shadow=True),
                                    Label(style=Style(marginLeft=12), content='普通', color=PASS_PLANS[0]['accent'], shadow=True),
                                    Panel(
                                        style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center, marginLeft=7, marginRight=6),
                                        children=free_reward_nodes,
                                    ),
                                    Label(style=Style(marginLeft=16), content='进阶', color=PASS_PLANS[1]['accent'], shadow=True),
                                    Panel(
                                        style=Style(flex=1, marginLeft=7, marginRight=8, flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                        children=elite_reward_nodes,
                                    ),
                                    RewardClaimButton(track_id=preview_plan_id, reward_state=row_claim_state),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


@Component
def BattlePassApp():
    preview_plan_id, set_preview_plan_id = useState('free')
    selected_level, set_selected_level = useState(5)

    current_level = 5
    current_xp = 860
    next_level_xp = 960

    progress_percent = int((current_xp * 100) / next_level_xp)
    if progress_percent < 0:
        progress_percent = 0
    if progress_percent > 100:
        progress_percent = 100

    preview_plan = PASS_PLANS[0]
    for plan in PASS_PLANS:
        if plan['id'] == preview_plan_id:
            preview_plan = plan
            break

    header_subtitle = '普通免费 · 进阶 1200 钻石'
    plan_hint = preview_plan['hint']

    mission_nodes = []
    for mission in MISSIONS:
        mission_nodes.append(MissionCard(mission=mission))

    reward_track_nodes = []
    for row in REWARD_ROWS:
        reward_track_nodes.append(
            RewardTrackRow(
                row=row,
                preview_plan_id=preview_plan_id,
                current_level=current_level,
                is_selected=row['level'] == selected_level,
                onClick=lambda level=row['level']: set_selected_level(level),
            )
        )

    return Image(
        style=Style(
            width='100%',
            height='100%',
            padding=6,
        ),
        color=Color(0xFF020617),
        children=[
            Image(
                style=Style(
                    width='100%',
                    height='100%',
                    padding=6,
                ),
                color=Color(0xFF111827),
                children=[
                    Image(
                        style=Style(
                            width='100%',
                            height=82,
                            padding=6,
                        ),
                        color=preview_plan['banner'],
                        children=[
                            Panel(
                                style=Style(width='100%', height='100%', flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=[
                                    Panel(
                                        style=Style(flex=1, paddingRight=8),
                                        children=[
                                            Label(content='S3 星穹远征战令', color=Colors.white, fontSize=13, shadow=True),
                                            Label(style=Style(marginTop=2), content='剩余 12 天 · 当前 Lv.%s' % current_level, color=Color(0xFFFFF3C4), shadow=True),
                                            Label(style=Style(marginTop=2), content=header_subtitle, color=Color(0xFFFDE68A)),
                                            Image(
                                                style=Style(width='100%', height=6, marginTop=6),
                                                color=Color(0x80334155),
                                                children=[
                                                    Image(
                                                        style=Style(width='%s%%' % progress_percent, height='100%'),
                                                        color=preview_plan['accent'],
                                                    )
                                                ],
                                            ),
                                        ],
                                    ),
                                    UnlockPreviewButton(
                                        is_elite=preview_plan_id == 'elite',
                                        onClick=lambda: set_preview_plan_id('free' if preview_plan_id == 'elite' else 'elite'),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    Panel(
                        style=Style(
                            marginTop=4,
                            flex=1,
                            flexDirection=FlexDirection.row,
                        ),
                        children=[
                            Image(
                                style=Style(
                                    width=144,
                                    height='100%',
                                    padding=4,
                                ),
                                color=Color(0xFF07111E),
                                children=[
                                    Label(style=Style(marginTop=2, marginLeft=2), content='任务看板', color=Colors.white, fontSize=12, shadow=True),
                                    Label(style=Style(marginTop=3, marginLeft=2), content=plan_hint, color=preview_plan['accent']),
                                    Scroll(
                                        style=Style(
                                            width='100%',
                                            marginTop=6,
                                            flex=1,
                                        ),
                                        children=mission_nodes,
                                    ),
                                ],
                            ),
                            Image(
                                style=Style(
                                    flex=1,
                                    height='100%',
                                    marginLeft=4,
                                    padding=4,
                                ),
                                color=Color(0xFF0B1220),
                                children=[
                                    Panel(
                                        style=Style(flexDirection=FlexDirection.row, justifyContent=JustifyContent.spaceBetween, alignItems=AlignItems.center),
                                        children=[
                                            Label(content='奖励轨道', color=Colors.white, fontSize=12, shadow=True),
                                            Label(content='当前预览：%s' % preview_plan['name'], color=preview_plan['accent'], shadow=True),
                                        ],
                                    ),
                                    Scroll(
                                        style=Style(
                                            width='100%',
                                            marginTop=6,
                                            flex=1,
                                        ),
                                        children=reward_track_nodes,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        ],
    )
