# -*- coding: utf-8 -*-

import random

import mod.client.extraClientApi as clientApi
from pyreact import *

ScreenNode = clientApi.GetScreenNodeCls()
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()


@Component
def FriendName(content, color=None):
    # Demonstrate @Component: no need to declare key/ref params.
    return Label(content=content, color=color)


class PyreactExampleScreen(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)

    def Create(self):
        print('=====> PyreactExampleUi Created <=====')
        self.app_id = 'pyreact_example_counter'
        self._mount_pyreact_app()

    def _mount_pyreact_app(self):
        bind = {
            'screen': self,
            'root': '/root',
            'app_id': self.app_id,
            'base_namespace': 'PyreactBase',
        }
        render_app(root=PyreactExampleApp, bind=bind)

    def Destroy(self):
        runtime_system = clientApi.GetSystem('PyreactRuntimeMod', 'PyreactRuntimeClientSystem')
        if runtime_system is not None:
            runtime_system.UnmountApp({'app_id': self.app_id})
        print('=====> PyreactExampleUi Destroyed <=====')


@Component
def PyreactExampleApp():
    selected_tab, set_selected_tab = useState('all')
    selected_friend_id, set_selected_friend_id = useState(None)
    search_text, set_search_text = useState('')
    scroll_node = useRef(None)

    def scroll_to_top():
        scroll_node.current.asScrollView().SetScrollViewPercentValue(0)

    friends = [
        {'id': 'friend_yeyu', 'name': '夜雨', 'level': 42, 'status': 'online', 'mode': '排位-四排', 'ping': 32, 'lastSeen': '在线', 'note': '擅长突击位'},
        {'id': 'friend_windfox', 'name': 'WindFox', 'level': 35, 'status': 'away', 'mode': '大厅挂机', 'ping': 58, 'lastSeen': '2分钟前', 'note': '麦克风开着'},
        {'id': 'friend_yanjiangmianbao', 'name': '岩浆面包', 'level': 27, 'status': 'online', 'mode': '天空对决', 'ping': 41, 'lastSeen': '在线', 'note': '常用弓箭'},
        {'id': 'friend_luna', 'name': 'Luna', 'level': 51, 'status': 'busy', 'mode': '副本中', 'ping': 76, 'lastSeen': '在线', 'note': '勿打扰'},
        {'id': 'friend_maoboh', 'name': '猫薄荷', 'level': 19, 'status': 'offline', 'mode': '-', 'ping': 0, 'lastSeen': '1小时前', 'note': '喜欢建造'},
        {'id': 'friend_neko77', 'name': 'Neko_77', 'level': 63, 'status': 'online', 'mode': '匹配中', 'ping': 24, 'lastSeen': '在线', 'note': '输出位'},
        {'id': 'friend_aze', 'name': '阿泽', 'level': 16, 'status': 'offline', 'mode': '-', 'ping': 0, 'lastSeen': '昨天', 'note': '新手玩家'},
        {'id': 'friend_nova', 'name': 'Nova', 'level': 48, 'status': 'online', 'mode': '自定义房间', 'ping': 35, 'lastSeen': '在线', 'note': '房主'},
        {'id': 'friend_pixelart', 'name': 'PixelArt', 'level': 30, 'status': 'online', 'mode': '创造模式', 'ping': 15, 'lastSeen': '在线', 'note': '像素画大师'},
        {'id': 'friend_redstone', 'name': 'RedStone', 'level': 55, 'status': 'online', 'mode': '生存模式', 'ping': 45, 'lastSeen': '在线', 'note': '红石大佬'},
        {'id': 'friend_builderguy', 'name': 'BuilderGuy', 'level': 22, 'status': 'away', 'mode': '正在建造', 'ping': 60, 'lastSeen': '5分钟前', 'note': '建筑师'},
        {'id': 'friend_miner01', 'name': 'Miner_01', 'level': 12, 'status': 'offline', 'mode': '-', 'ping': 0, 'lastSeen': '3小时前', 'note': '快乐挖矿'},
        {'id': 'friend_shadow', 'name': 'Shadow', 'level': 60, 'status': 'busy', 'mode': '末地探索', 'ping': 88, 'lastSeen': '在线', 'note': '独行侠'},
    ]

    tabs = [
        {'id': 'all', 'name': '全部'},
        {'id': 'online', 'name': '在线'},
        {'id': 'offline', 'name': '离线'},
    ]

    filtered = []
    for f in friends:
        if selected_tab == 'online' and f['status'] not in ('online', 'away', 'busy'):
            continue
        if selected_tab == 'offline' and f['status'] != 'offline':
            continue
        if search_text:
            name = f.get('name', '')
            note = f.get('note', '')
            if (search_text not in name) and (search_text not in note):
                continue
        filtered.append(f)

    selected_index = 0
    current_friend = None
    for idx, friend in enumerate(filtered):
        if friend.get('id') == selected_friend_id:
            selected_index = idx
            current_friend = friend
            break

    if current_friend is None and filtered:
        current_friend = filtered[0]
        selected_index = 0

    def tab_btn_bg_builder(state):
        color_map = {
            ButtonState.default: Color(0xFF334155),
            ButtonState.hover: Color(0xFF475569),
            ButtonState.pressed: Color(0xFF1E293B),
        }
        return Image(
            style=Style(width='100%', height='100%'),
            color=color_map.get(state, color_map[ButtonState.default]),
        )

    def action_btn_bg_builder(state):
        color_map = {
            ButtonState.default: Color(0xFF2563EB),
            ButtonState.hover: Color(0xFF1D4ED8),
            ButtonState.pressed: Color(0xFF1E40AF),
        }
        return Image(
            style=Style(width='100%', height='100%'),
            color=color_map.get(state, color_map[ButtonState.default]),
        )

    status_color_map = {
        'online': Color(0xFF22C55E),
        'away': Color(0xFFF59E0B),
        'busy': Color(0xFFEF4444),
        'offline': Color(0xFF6B7280),
    }
    status_text_map = {
        'online': '在线',
        'away': '离开',
        'busy': '忙碌',
        'offline': '离线',
    }

    avatar_textures = [
        'textures/ui/Friend1',
        'textures/ui/Friend2',
        'textures/ui/icon_steve',
        'textures/ui/icon_alex',
    ]
    status_icon_map = {
        'online': 'textures/ui/player_online_icon',
        'away': 'textures/ui/onlineLight',
        'busy': 'textures/ui/Ping_Red',
        'offline': 'textures/ui/player_offline_icon',
    }

    def _avatar_texture(idx):
        if idx < 0:
            idx = 0
        return avatar_textures[idx % len(avatar_textures)]

    def _ping_texture(friend):
        ping = friend.get('ping', 0)
        if ping <= 0:
            return 'textures/ui/Ping_Offline_Red'
        if ping <= 45:
            return 'textures/ui/Ping_Green'
        if ping <= 80:
            return 'textures/ui/Ping_Yellow'
        return 'textures/ui/Ping_Red'

    tab_nodes = []
    for tab in tabs:
        tab_id = tab['id']
        tab_nodes.append(
            Button(
                key='tab_%s' % tab_id,
                style=Style(
                    width=76,
                    height=30,
                    marginRight=8,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.center,
                ),
                buttonBuilder=tab_btn_bg_builder,
                onClick=(lambda tid=tab_id: (set_selected_tab(tid), set_selected_friend_id(None))),
                children=[
                    FriendName(
                        color=Colors.white,
                        content=tab['name'],
                    )
                ],
            )
        )

    friend_nodes = []
    for idx, f in enumerate(filtered):
        is_selected = idx == selected_index
        status_key = f['status']

        if is_selected:
            row_default = Color(0xFF1D4ED8)
            row_hover = Color(0xFF1E40AF)
            row_pressed = Color(0xFF1E3A8A)
        else:
            row_default = Color(0xFF111827)
            row_hover = Color(0xFF1F2937)
            row_pressed = Color(0xFF0B1220)

        def _row_builder(state, d=row_default, h=row_hover, p=row_pressed):
            color_map = {
                ButtonState.default: d,
                ButtonState.hover: h,
                ButtonState.pressed: p,
            }
            return Image(
                style=Style(width='100%', height='100%'),
                color=color_map.get(state, d),
            )

        friend_nodes.append(
            Button(
                key=f['id'],
                style=Style(
                    width='100%',
                    height=66,
                    marginTop=8,
                    paddingLeft=10,
                    paddingRight=10,
                    alignItems=AlignItems.center,
                    justifyContent=JustifyContent.spaceBetween,
                    flexDirection=FlexDirection.row,
                ),
                buttonBuilder=_row_builder,
                onClick=(lambda friend_id=f['id']: set_selected_friend_id(friend_id)),
                children=[
                    Panel(
                        style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                        children=[
                            Image(
                                style=Style(width=40, height=40, marginRight=10),
                                src=_avatar_texture(idx),
                            ),
                            Panel(
                                style=Style(flexDirection=FlexDirection.column),
                                children=[
                                    Label(
                                        color=Colors.white,
                                        fontSize=FontSize.large,
                                        content='%s  Lv.%s' % (f['name'], f['level']),
                                    ),
                                    Label(
                                        color=Color(0xFF93C5FD),
                                        content=f['mode'],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    Panel(
                        style=Style(alignItems=AlignItems.end, flexDirection=FlexDirection.column),
                        children=[
                            Label(
                                color=status_color_map.get(status_key, Color(0xFF6B7280)),
                                content=status_text_map.get(status_key, '未知'),
                            ),
                            Panel(
                                style=Style(marginTop=2, flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=[
                                    Image(
                                        style=Style(width=14, height=14, marginRight=4),
                                        src=_ping_texture(f),
                                    ),
                                    Label(
                                        color=Color(0xFFCBD5E1),
                                        content='Ping %s' % (f['ping'] if f['ping'] > 0 else '--'),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            )
        )


    detail_nodes = []
    if current_friend is not None:
        status_key = current_friend['status']
        detail_nodes = [
            Image(
                style=Style(width='100%', height=92, marginTop=10),
                src='textures/ui/FriendsDiversity',
                color=Color(0xFF1F2937),
            ),
            Panel(
                style=Style(marginTop=10, flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                children=[
                    Image(
                        style=Style(width=56, height=56, marginRight=10),
                        src=_avatar_texture(selected_index),
                    ),
                    Image(
                        style=Style(width=18, height=18),
                        src=status_icon_map.get(status_key, 'textures/ui/player_offline_icon'),
                    ),
                ],
            ),
            Label(
                color=Colors.white,
                fontSize=FontSize.extraLarge,
                content=current_friend['name'],
            ),
            Label(
                style=Style(marginTop=6),
                color=Color(0xFF93C5FD),
                content='等级: %s' % current_friend['level'],
            ),
            Label(
                style=Style(marginTop=4),
                color=status_color_map.get(status_key, Color(0xFF6B7280)),
                content='状态: %s' % status_text_map.get(status_key, '未知'),
            ),
            Label(
                style=Style(marginTop=4),
                color=Color(0xFFFDE68A),
                content='模式: %s' % current_friend['mode'],
            ),
            Label(
                style=Style(marginTop=4),
                color=Color(0xFFCBD5E1),
                content='最近在线: %s' % current_friend['lastSeen'],
            ),
            Label(
                style=Style(marginTop=8),
                color=Color(0xFFE2E8F0),
                linePadding=2,
                content='备注: %s' % current_friend['note'],
            ),
            Panel(
                style=Style(marginTop=14, flexDirection=FlexDirection.row),
                children=[
                    Button(
                        style=Style(
                            width=100,
                            height=34,
                            marginRight=10,
                            alignItems=AlignItems.center,
                            justifyContent=JustifyContent.center,
                        ),
                        buttonBuilder=action_btn_bg_builder,
                        onClick=(lambda: None),
                        children=[
                            Label(color=Colors.white, content='邀请组队')
                        ],
                    ),
                    Button(
                        style=Style(
                            width=100,
                            height=34,
                            alignItems=AlignItems.center,
                            justifyContent=JustifyContent.center,
                        ),
                        buttonBuilder=action_btn_bg_builder,
                        onClick=(lambda: None),
                        children=[
                            Label(color=Colors.white, content='发送私聊')
                        ],
                    ),
                ],
            ),
        ]
    else:
        detail_nodes = [
            Label(
                color=Color(0xFF94A3B8),
                fontSize=FontSize.large,
                content='当前筛选下没有好友',
            )
        ]

    return Image(
        style=Style(
            width='100%',
            height='100%',
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        color=Color(0xFF0F172A),
        children=[
            Image(
                style=Style(width='100%', height='100%', flexDirection=FlexDirection.row),
                color=Color(0xFF1E293B),
                children=[
                    Image(
                        style=Style(width=380, height='100%', padding=12),
                        color=Color(0xFF111827),
                        children=[
                            Label(
                                color=Colors.white,
                                fontSize=FontSize.extraLarge,
                                content='好友面板',
                            ),
                            Image(
                                style=Style(width=26, height=26, marginTop=6),
                                src='textures/ui/FriendsIcon',
                            ),
                            Label(
                                style=Style(marginTop=4),
                                color=Color(0xFF93C5FD),
                                content='人数: %s/%s' % (len(filtered), len(friends)),
                            ),
                            Panel(
                                style=Style(marginTop=10, height=30, flexDirection=FlexDirection.row),
                                children=tab_nodes,
                            ),
                            Panel(
                                style=Style(marginTop=10, flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                children=[
                                    Label(
                                        color=Color(0xFF94A3B8),
                                        content='搜索',
                                    ),
                                    Input(
                                        style=Style(height=27, marginLeft=10, flex=1),
                                        value=search_text,
                                        onChange=set_search_text,
                                    ),
                                ],
                            ),
                            Scroll(
                                ref=scroll_node,
                                style=Style(marginTop=10, flex=1, width='100%'),
                                children=friend_nodes,
                            ),
                            Button(
                                style=Style(
                                    position=Position.absolute,
                                    bottom=20,
                                    right=20,
                                    height=26,
                                    width=26,
                                    alignItems=AlignItems.center,
                                    justifyContent=JustifyContent.center,
                                    zIndex=100,
                                ),
                                buttonBuilder=lambda state: Image(
                                    style=Style(width='100%', height='100%'),
                                    color=Color(0xFF2563EB) if state == ButtonState.default else Color(0xFF1D4ED8),
                                ),
                                onClick=lambda: scroll_to_top(),
                                children=[
                                    Label(color=Colors.white, content='^', fontSize=FontSize.large)
                                ]
                            )
                        ],
                    ),
                    Panel(
                        style=Style(flex=1, height='100%', padding=16),
                        children=[
                            Label(
                                color=Colors.white,
                                fontSize=FontSize.large,
                                content='好友详情',
                            ),
                        ] + detail_nodes,
                    ),
                ],
            ),
        ],
    )
