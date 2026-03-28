# -*- coding: utf-8 -*-

from pyreact.components.enums import ButtonState

from PyreactRuntimeScript.native_runtime.lifecycle_mixin import RuntimeLifecycleMixin
from PyreactRuntimeScript.native_runtime.props_mixin import RuntimePropsMixin
from PyreactRuntimeScript.native_runtime.native_api_mixin import RuntimeNativeApiMixin


class PyreactNativeRuntime(RuntimeLifecycleMixin, RuntimePropsMixin, RuntimeNativeApiMixin):
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
    }
    _DEFAULT_WHITE_TEXTURE = "textures/ui/white_bg"
    _MEASURE_LABEL_NAME = "__pyreact_measure_label"

    _BUTTON_STATES = (ButtonState.default, ButtonState.hover, ButtonState.pressed)
    _BUTTON_STATE_TEXTURES = {
        ButtonState.default: "textures/netease/common/button/default",
        ButtonState.hover: "textures/netease/common/button/hover",
        ButtonState.pressed: "textures/netease/common/button/pressed",
    }

    def __init__(self, app_id, screen_node, root_path, app_fn, base_namespace="PyreactBase", log_perf=False):
        self.app_id = app_id
        self._screen = screen_node
        self._root_path = root_path or "/root"
        self._app_fn = app_fn
        self._base_namespace = self._safe_text(base_namespace) or "PyreactBase"
        self._log_perf = bool(log_perf)

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
        self._input_callbacks = {}
        self._input_paths = {}
        self._input_last_values = {}
        self._node_refs = {}
        self._prev_node_refs = {}
        self._native_common_style_cache = {}
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
        self._measure_label_path = None

        self._init_pyreact_runtime()
