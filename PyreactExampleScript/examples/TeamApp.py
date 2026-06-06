# -*- coding: utf-8 -*-

from pyreact import *

MAX_SLOTS = 4

GAME_MODES = [
    {'id': 'bedwar',  'name': '起床战争', 'desc': '摧毁敌方床·4人'},
    {'id': 'skywar',  'name': '空岛战争', 'desc': '最后生还·4人'},
    {'id': 'build',   'name': '建筑大师', 'desc': '主题创作·4人'},
    {'id': 'hunger',  'name': '饥饿游戏', 'desc': '荒野求生·4人'},
]

AVATAR_TEXTURES = [
    'textures/ui/Friend1',
    'textures/ui/Friend2',
    'textures/ui/icon_steve',
    'textures/ui/icon_alex',
]

# 主题色
C_BG        = Color(0xFF110A2A)   # 最深背景
C_SURFACE   = Color(0xFF1C1040)   # 面板底
C_CARD      = Color(0xFF241550)   # 卡片
C_CARD2     = Color(0xFF1A0E3A)   # 右侧卡片
C_BORDER    = Color(0xFF3B2270)   # 边框/分割线
C_PRIMARY   = Color(0xFF7C3AED)   # 主色 紫
C_PRIMARY_H = Color(0xFF6D28D9)
C_PRIMARY_P = Color(0xFF5B21B6)
C_SUCCESS   = Color(0xFF10B981)
C_SUCCESS_H = Color(0xFF059669)
C_DANGER    = Color(0xFFDC2626)
C_DANGER_H  = Color(0xFFB91C1C)
C_WARN      = Color(0xFFF59E0B)
C_MUTED     = Color(0xFF6D5B9A)
C_TEXT      = Colors.white
C_TEXT2     = Color(0xFFB8A8D8)
C_TEXT3     = Color(0xFF7C6CA8)
C_GOLD      = Color(0xFFFBBF24)

STATUS_COLOR = {'online': C_SUCCESS, 'away': C_WARN, 'offline': C_MUTED}
STATUS_TEXT  = {'online': '在线',    'away': '离开',  'offline': '离线'}


def _avatar(idx):
    return AVATAR_TEXTURES[abs(idx) % len(AVATAR_TEXTURES)]


# 细分割线
def _divider():
    return Image(
        style=Style(width='100%', height=1, marginTop=6, marginBottom=2),
        color=C_BORDER,
    )


# 小标签徽章
def _badge(text, color):
    return Image(
        style=Style(
            paddingLeft=5, paddingRight=5, paddingTop=1, paddingBottom=1,
            alignItems=AlignItems.center, justifyContent=JustifyContent.center,
        ),
        color=color.withAlpha(0.18),
        children=[Label(content=text, color=color)],
    )


@Component
def TeamApp():
    selected_mode, set_selected_mode = useState('bedwar')
    self_ready,    set_self_ready    = useState(False)
    room_code,     _                 = useState('MC-7749-XKQZ')
    copied,        set_copied        = useState(False)
    search_text,   set_search_text   = useState('')

    members, set_members = useState([
        {'id': 'me',      'name': '你',       'level': 38, 'leader': True,  'ready': False, 'avatar': 0},
        {'id': 'm_neko',  'name': 'Neko_77',  'level': 63, 'leader': False, 'ready': True,  'avatar': 1},
        {'id': 'm_luna',  'name': 'Luna',     'level': 51, 'leader': False, 'ready': False, 'avatar': 2},
    ])
    invites, set_invites = useState([
        {'id': 'f_yeyu',    'name': '夜雨',    'level': 42, 'status': 'online',  'avatar': 1},
        {'id': 'f_windfox', 'name': 'WindFox', 'level': 35, 'status': 'away',    'avatar': 2},
        {'id': 'f_nova',    'name': 'Nova',    'level': 48, 'status': 'online',  'avatar': 3},
        {'id': 'f_redstone','name': 'RedStone','level': 55, 'status': 'online',  'avatar': 0},
        {'id': 'f_pixel',   'name': 'PixelArt','level': 30, 'status': 'online',  'avatar': 1},
        {'id': 'f_maoboh',  'name': '猫薄荷',  'level': 19, 'status': 'offline', 'avatar': 2},
        {'id': 'f_shadow',  'name': 'Shadow',  'level': 60, 'status': 'away',    'avatar': 3},
    ])

    invite_scroll = useRef(None)

    current_mode = GAME_MODES[0]
    for mode in GAME_MODES:
        if mode['id'] == selected_mode:
            current_mode = mode
            break

    ready_count = sum(1 for m in members if m.get('ready'))
    all_ready   = ready_count == len(members) and len(members) >= 2

    # 筛选好友
    filtered_invites = []
    for f in invites:
        if search_text and search_text.lower() not in str(f['name']).lower():
            continue
        filtered_invites.append(f)

    def toggle_self_ready():
        new_r = not self_ready
        set_self_ready(new_r)
        set_members([dict(m, ready=new_r) if m['id'] == 'me' else m for m in members])

    def kick_member(mid):
        set_members([m for m in members if m['id'] != mid])

    def transfer_leader(mid):
        def _do():
            next_m = []
            for m in members:
                copy = dict(m)
                copy['leader'] = (m['id'] == mid)
                next_m.append(copy)
            set_members(next_m)
        _do()

    def invite_friend(friend):
        if len(members) >= MAX_SLOTS:
            return
        set_members(list(members) + [{
            'id': friend['id'], 'name': friend['name'],
            'level': friend['level'], 'leader': False,
            'ready': False, 'avatar': friend['avatar'],
        }])
        set_invites([f for f in invites if f['id'] != friend['id']])

    def copy_room_code():
        set_copied(True)

    # ---------- 模式 Tab ----------
    mode_nodes = []
    for mode in GAME_MODES:
        mid = mode['id']
        active = mid == selected_mode
        mode_nodes.append(
            FilledButton(
                key='mode_%s' % mid,
                style=Style(
                    flex=1, height=28, marginRight=4,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                default=C_PRIMARY   if active else C_CARD,
                hover  =C_PRIMARY_H if active else C_BORDER,
                pressed=C_PRIMARY_P if active else C_BG,
                onClick=(lambda m=mid: set_selected_mode(m)),
                children=[Label(content=mode['name'], color=C_TEXT if active else C_TEXT2)],
            )
        )

    # ---------- 队员槽 ----------
    slot_nodes = []
    for si in range(MAX_SLOTS):
        if si < len(members):
            m = members[si]
            is_me     = m['id'] == 'me'
            is_leader = m.get('leader')
            ready     = m.get('ready')
            ready_col = C_SUCCESS if ready else C_TEXT3

            badges = []
            if is_leader:
                badges.append(_badge('队长', C_GOLD))
            badges.append(_badge('已准备' if ready else '未准备', ready_col))

            action_btns = []
            if not is_me:
                if not is_leader:
                    action_btns.append(
                        FilledButton(
                            key='kick_%s' % m['id'],
                            style=Style(width=36, height=22, marginLeft=4,
                                        alignItems=AlignItems.center,
                                        justifyContent=JustifyContent.center),
                            default=C_DANGER, hover=C_DANGER_H, pressed=C_DANGER_H,
                            onClick=(lambda mid=m['id']: kick_member(mid)),
                            children=[Label(content='踢', color=C_TEXT)],
                        )
                    )
                action_btns.append(
                    FilledButton(
                        key='tl_%s' % m['id'],
                        style=Style(width=36, height=22, marginLeft=4,
                                    alignItems=AlignItems.center,
                                    justifyContent=JustifyContent.center),
                        default=C_BORDER, hover=C_PRIMARY, pressed=C_PRIMARY_P,
                        onClick=(lambda mid=m['id']: transfer_leader(mid)),
                        children=[Label(content='授权', color=C_TEXT)],
                    )
                )

            slot_nodes.append(
                Animated(
                    key='slot_%s' % m['id'],
                    enter=slideInLeft(distance=14, duration=160),
                    exit=fadeOut(duration=120),
                    children=Image(
                        style=Style(
                            width='100%', height=44, marginTop=5,
                            paddingLeft=8, paddingRight=8,
                            flexDirection=FlexDirection.row,
                            alignItems=AlignItems.center,
                            justifyContent=JustifyContent.spaceBetween,
                        ),
                        color=C_CARD,
                        children=[
                            # 头像 + 名字
                            Panel(
                                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=[
                                    Image(style=Style(width=28, height=28, marginRight=8),
                                          src=_avatar(m.get('avatar', si))),
                                    Panel(style=Style(flexDirection=FlexDirection.column), children=[
                                        Label(color=C_TEXT, content=m['name']),
                                        Label(style=Style(marginTop=1), color=C_MUTED,
                                              content='Lv.%s' % m['level']),
                                    ]),
                                ],
                            ),
                            # 右侧：徽章 + 操作
                            Panel(
                                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=badges + action_btns,
                            ),
                        ],
                    ),
                )
            )
        else:
            slot_nodes.append(
                Image(
                    key='slot_empty_%s' % si,
                    style=Style(
                        width='100%', height=44, marginTop=5,
                        alignItems=AlignItems.center, justifyContent=JustifyContent.center,
                    ),
                    color=C_BG,
                    children=[Label(color=C_TEXT3, content='· 空位  邀请好友加入 ·')],
                )
            )

    # ---------- 邀请好友列表 ----------
    invite_nodes = []
    for idx, f in enumerate(filtered_invites):
        sk = f['status']
        can = (sk != 'offline') and (len(members) < MAX_SLOTS)
        invite_nodes.append(
            Animated(
                key='inv_%s' % f['id'],
                enter=slideInRight(distance=14, duration=160),
                exit=fadeOut(duration=120),
                children=Image(
                    style=Style(
                        width='100%', height=40, marginTop=5,
                        paddingLeft=8, paddingRight=8,
                        flexDirection=FlexDirection.row,
                        alignItems=AlignItems.center,
                        justifyContent=JustifyContent.spaceBetween,
                    ),
                    color=C_CARD2,
                    children=[
                        Panel(
                            style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                            children=[
                                Image(style=Style(width=26, height=26, marginRight=7),
                                      src=_avatar(f.get('avatar', idx))),
                                Panel(style=Style(flexDirection=FlexDirection.column), children=[
                                    Label(color=C_TEXT, content='%s  §7Lv.%s' % (f['name'], f['level'])),
                                    Label(style=Style(marginTop=1),
                                          color=STATUS_COLOR.get(sk, C_MUTED),
                                          content=STATUS_TEXT.get(sk, '未知')),
                                ]),
                            ],
                        ),
                        FilledButton(
                            style=Style(width=48, height=24,
                                        alignItems=AlignItems.center,
                                        justifyContent=JustifyContent.center),
                            default=C_PRIMARY   if can else C_BORDER,
                            hover  =C_PRIMARY_H if can else C_BORDER,
                            pressed=C_PRIMARY_P if can else C_BORDER,
                            onClick=(lambda fr=f, ok=can: invite_friend(fr) if ok else None),
                            children=[Label(color=C_TEXT,
                                            content='邀请' if can else ('离线' if sk == 'offline' else '满员'))],
                        ),
                    ],
                ),
            )
        )

    # ---------- 底部操作按钮 ----------
    if all_ready:
        act_d, act_h, act_p = C_SUCCESS, C_SUCCESS_H, C_SUCCESS_H
        act_text  = '▶  开始游戏'
        act_click = lambda: None
    elif self_ready:
        act_d, act_h, act_p = Color(0xFF92400E), Color(0xFF78350F), Color(0xFF78350F)
        act_text  = '取消准备'
        act_click = toggle_self_ready
    else:
        act_d, act_h, act_p = C_PRIMARY, C_PRIMARY_H, C_PRIMARY_P
        act_text  = '✔  准备'
        act_click = toggle_self_ready

    copy_color = C_SUCCESS if copied else C_PRIMARY

    # ===================== 根布局 =====================
    return Image(
        style=Style(
            position=Position.absolute, top=0, right=0, bottom=0, left=0,
            flexDirection=FlexDirection.row,
        ),
        color=C_BG,
        children=[
            # ===== 左侧主面板 =====
            Panel(
                style=Style(flex=1, height='100%', padding=12),
                children=[
                    # 顶栏：标题 + 房间码
                    Panel(
                        style=Style(flexDirection=FlexDirection.row,
                                    alignItems=AlignItems.center,
                                    justifyContent=JustifyContent.spaceBetween),
                        children=[
                            Panel(
                                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=[
                                    Label(color=C_TEXT, fontSize=FontSize.large, shadow=True,
                                          content='⚔  组队大厅'),
                                    Image(
                                        style=Style(marginLeft=8, paddingLeft=6, paddingRight=6,
                                                    paddingTop=1, paddingBottom=1,
                                                    alignItems=AlignItems.center,
                                                    justifyContent=JustifyContent.center),
                                        color=C_PRIMARY.withAlpha(0.25),
                                        children=[
                                            Label(color=C_PRIMARY,
                                                  content='%s/%s' % (len(members), MAX_SLOTS))
                                        ],
                                    ),
                                ],
                            ),
                            # 房间码
                            Panel(
                                style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=[
                                    Label(color=C_TEXT3, content='房间码 '),
                                    Label(color=C_GOLD, content=room_code),
                                    FilledButton(
                                        style=Style(marginLeft=6, width=42, height=20,
                                                    alignItems=AlignItems.center,
                                                    justifyContent=JustifyContent.center),
                                        default=copy_color.withAlpha(0.2),
                                        hover=copy_color.withAlpha(0.35),
                                        pressed=copy_color.withAlpha(0.5),
                                        onClick=copy_room_code,
                                        children=[Label(color=copy_color,
                                                        content='已复制' if copied else '复制')],
                                    ),
                                ],
                            ),
                        ],
                    ),

                    _divider(),

                    # 游戏模式
                    Label(style=Style(marginTop=4, marginBottom=5),
                          color=C_TEXT3, content='游戏模式'),
                    Panel(style=Style(flexDirection=FlexDirection.row), children=mode_nodes),
                    Label(style=Style(marginTop=5),
                          color=C_TEXT2,
                          content='%s  ·  %s' % (current_mode['name'], current_mode['desc'])),

                    _divider(),

                    # 队伍成员
                    Panel(
                        style=Style(marginTop=4, flexDirection=FlexDirection.row,
                                    alignItems=AlignItems.center,
                                    justifyContent=JustifyContent.spaceBetween),
                        children=[
                            Label(color=C_TEXT3, content='队伍成员'),
                            Label(color=C_SUCCESS if all_ready else C_TEXT3,
                                  content='已准备 %s/%s' % (ready_count, len(members))),
                        ],
                    ),
                    Scroll(
                        style=Style(marginTop=4, flex=1, width='100%'),
                        children=slot_nodes,
                    ),

                    # 底部操作
                    FilledButton(
                        style=Style(
                            marginTop=10, width='100%', height=36,
                            alignItems=AlignItems.center,
                            justifyContent=JustifyContent.center,
                        ),
                        default=act_d, hover=act_h, pressed=act_p,
                        onClick=act_click,
                        children=[Label(color=C_TEXT, shadow=True, content=act_text)],
                    ),
                ],
            ),

            # 竖分割线
            Image(style=Style(width=1, height='100%'), color=C_BORDER),

            # ===== 右侧邀请面板 =====
            Panel(
                style=Style(width=240, height='100%', padding=12),
                children=[
                    Label(color=C_TEXT, fontSize=FontSize.large, shadow=True, content='邀请好友'),
                    Label(style=Style(marginTop=3), color=C_TEXT3,
                          content='在线 · 可加入你的队伍'),

                    # 搜索框
                    Panel(
                        style=Style(marginTop=8, flexDirection=FlexDirection.row,
                                    alignItems=AlignItems.center),
                        children=[
                            Label(color=C_TEXT3, content='搜索  '),
                            Input(
                                style=Style(flex=1, height=24),
                                value=search_text,
                                onChange=set_search_text,
                                placeholder='输入名字...',
                            ),
                        ],
                    ),

                    _divider(),

                    Scroll(
                        ref=invite_scroll,
                        style=Style(marginTop=4, flex=1, width='100%'),
                        children=invite_nodes if invite_nodes else [
                            Label(style=Style(marginTop=10),
                                  color=C_TEXT3, content='没有匹配的好友')
                        ],
                    ),
                ],
            ),
        ],
    )
