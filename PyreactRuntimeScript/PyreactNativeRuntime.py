# -*- coding: utf-8 -*-

from pyreact.components.enums import ButtonState

from PyreactRuntimeScript.native_runtime.lifecycle_mixin import RuntimeLifecycleMixin
from PyreactRuntimeScript.native_runtime.props_mixin import RuntimePropsMixin
from PyreactRuntimeScript.native_runtime.native_api_mixin import RuntimeNativeApiMixin
from PyreactRuntimeScript.native_runtime.animation_mixin import RuntimeAnimationMixin


class PyreactNativeRuntime(RuntimeLifecycleMixin, RuntimePropsMixin, RuntimeNativeApiMixin, RuntimeAnimationMixin):
    """Render pyreact component tree into NetEase ScreenNode controls."""

    _CONTROL_NAME_PREFIX = "pyreact_"

    _TYPE_DEF_SUFFIX_MAP = {
        "Panel": "panelBase",
        "Image": "imageBase",
        "Label": "textBase",
        "Item": "itemBase",
        "Button": "buttonBase",
        "Input": "inputBase",
        "Scroll": "scrollBase",
        "PaperDoll": "paperDollBase",
    }
    _DEFAULT_WHITE_TEXTURE = "textures/ui/white_bg"

    _BUTTON_STATES = (ButtonState.default, ButtonState.hover, ButtonState.pressed)
    _BUTTON_STATE_TEXTURES = {
        ButtonState.default: "textures/netease/common/button/default",
        ButtonState.hover: "textures/netease/common/button/hover",
        ButtonState.pressed: "textures/netease/common/button/pressed",
    }

    def __init__(self, app_id, screen_node, root_path, app_fn, base_namespace="PyreactBase", log_perf=False, debug_mode=False):
        self.app_id = app_id
        self._screen = screen_node
        self._root_path = root_path or "/root"
        self._app_fn = app_fn
        self._base_namespace = self._safe_text(base_namespace) or "PyreactBase"
        self._log_perf = bool(log_perf)
        self._debug_mode = bool(debug_mode)

        self._layout_engine = None
        self._text_measurer = None
        self._component_instance = None
        self._tree_builder = None
        self._reconciler = None
        self._prev_vtree = None
        self._prev_shadow_root = None
        self._mounted = False
        self._is_rendering = False
        self._needs_render = False
        self._render_scheduled = False
        self._button_callbacks = {}
        self._button_touch_callbacks = {}
        self._active_touch_nodes = {}
        self._actor_motion_comp = None
        self._input_callbacks = {}
        self._input_paths = {}
        self._input_last_values = {}
        self._node_refs = {}
        self._prev_node_refs = {}
        self._native_common_style_cache = {}
        self._native_control_cache = {}
        self._native_adapter_cache = {}
        self._native_label_props_cache = {}
        self._native_image_props_cache = {}
        self._native_paper_doll_props_cache = {}
        self._native_geometry_cache = {}
        self._button_bind_cache = {}
        self._button_slot_cache = {}
        self._button_slot_base_alpha_cache = {}
        self._button_slot_perf_stats = {}
        self._native_commit_perf_stats = {}
        self._pending_button_binds = {}
        self._scroll_path_cache = {}
        self._animation_states = {}
        self._pending_animation_removals = {}
        self._force_layout_next_render = False
        self._last_root_size = None
        self._input_edit_bound = False
        self._input_edit_handler_method_name = None

        # Debug logs are enabled by default for example apps.
        app_label = ""
        try:
            app_label = ("%s" % (app_id or "")).lower()
        except Exception:
            app_label = ""
        self._debug_render = ("example" in app_label)
        self._debug_input = ("example" in app_label)

        self._init_pyreact_runtime()
        self._init_animation_runtime_state()

    # ------------------------------------------------------------------
    # Debug / inspection API
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize(v):
        """Recursively convert non-JSON-serializable values to plain Python types."""
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        # Python 2 unicode / long
        try:
            if isinstance(v, unicode):
                return v
        except NameError:
            pass
        try:
            if isinstance(v, long):
                return int(v)
        except NameError:
            pass
        # Color object: serialize as "#AARRGGBB"
        if hasattr(v, '_value') and hasattr(v, 'alpha8') and hasattr(v, 'red'):
            return '#%08x' % v._value
        if isinstance(v, dict):
            return {k: PyreactNativeRuntime._sanitize(val) for k, val in v.items()}
        if isinstance(v, (list, tuple)):
            return [PyreactNativeRuntime._sanitize(i) for i in v]
        # Fallback: repr
        return repr(v)

    def _serialize_shadow_node(self, node, depth=0):
        if node is None:
            return None
        layout = node.layout
        s = PyreactNativeRuntime._sanitize
        result = {
            'id': node.node_id,
            'type': node.node_type,
            'props': s(node.props),
            'style': s(node.style),
            'opacity': node.effective_opacity,
            'layout': {
                'x': layout.x, 'y': layout.y,
                'width': layout.width, 'height': layout.height,
            } if layout else None,
            'children': [self._serialize_shadow_node(c, depth + 1) for c in (node.children or [])],
        }
        return result

    def debug_get_ui_tree(self):
        """Return the full UI tree as a serializable dict."""
        return {
            'app_id': self.app_id,
            'root_path': self._root_path,
            'tree': self._serialize_shadow_node(self._prev_shadow_root),
        }

    def debug_get_subtree(self, node_id):
        """Return the subtree rooted at the first node matching node_id."""
        def _find(node):
            if node is None:
                return None
            if node.node_id == node_id:
                return self._serialize_shadow_node(node)
            for child in (node.children or []):
                found = _find(child)
                if found is not None:
                    return found
            return None
        return _find(self._prev_shadow_root)

    def debug_get_node_props(self, node_id):
        """Return props+style+layout for a single node by node_id."""
        def _find(node):
            if node is None:
                return None
            if node.node_id == node_id:
                layout = node.layout
                return {
                    'id': node.node_id,
                    'type': node.node_type,
                    'props': node.props,
                    'style': node.style,
                    'opacity': node.effective_opacity,
                    'layout': {
                        'x': layout.x, 'y': layout.y,
                        'width': layout.width, 'height': layout.height,
                    } if layout else None,
                }
            for child in (node.children or []):
                found = _find(child)
                if found is not None:
                    return found
            return None
        return _find(self._prev_shadow_root)
