# -*- coding: utf-8 -*-

from pyreact.components.color import Color


try:
    _UNICODE_TYPE = unicode
except NameError:
    # Python3 fallback for local tooling; runtime is Python2 in-game.
    _UNICODE_TYPE = str


class RuntimeNativeApiMixin(object):
    _TEXT_FONT_SIZE_BASE = 16.0

    def _ensure_measure_label(self):
        measure_path = self._root_path + "/" + self._MEASURE_LABEL_NAME
        self._measure_label_path = measure_path

        control = None
        try:
            control = self._screen.GetBaseUIControl(measure_path)
        except Exception:
            control = None

        if not control:
            try:
                root_control = self._screen.GetBaseUIControl(self._root_path)
            except Exception:
                root_control = None
            if not root_control:
                return None

            def_name = "%s.%s" % (self._base_namespace, "textBase")
            try:
                control = self._screen.CreateChildControl(def_name, self._MEASURE_LABEL_NAME, root_control)
            except Exception:
                control = None
            if not control:
                return None

        self._safe_set_position(measure_path, -100000.0, -100000.0, control)
        try:
            if hasattr(control, "SetVisible"):
                control.SetVisible(True)
        except Exception:
            pass
        try:
            if hasattr(control, "SetAlpha"):
                control.SetAlpha(0.0)
        except Exception:
            pass
        return control

    def _measure_text_native(self, content, style, max_width=None):
        control = self._ensure_measure_label()
        if not control:
            return None

        label_path = self._measure_label_path
        if not label_path:
            return None

        label_control = self._to_label_control(control, label_path)
        if not label_control:
            return None

        self._safe_set_text_line_padding(label_path, 0.0, label_control)
        self._safe_set_text_font_size(label_path, 1.0, label_control)
        self._safe_set_text_alignment(label_path, "left", label_control)
        self._safe_set_text_shadow(label_path, False, label_control)

        limit_width = self._to_float(max_width, 0.0)

        self._apply_label_native_props_then_text(
            path=label_path,
            label_props=style,
            text=content,
            control=label_control,
        )

        width = 0.0
        height = 0.0
        try:
            size = label_control.GetSize()
        except Exception:
            size = None

        if (not size) or len(size) < 2:
            try:
                size = self._screen.GetSize(label_path)
            except Exception:
                size = None

        if size and len(size) >= 2:
            width = self._to_float(size[0], 0.0)
            height = self._to_float(size[1], 0.0)

        if width >= 4000.0 or height >= 4000.0:
            width = 0.0
            height = 0.0

        font_scale = self._parse_text_font_scale(style.get("fontSize") if isinstance(style, dict) else None)
        if font_scale is None or font_scale <= 0.0:
            font_scale = 1.0
        if width > 0.0 and (width / font_scale) < 4.0:
            width = 4.0 * font_scale

        try:
            label_control.SetText("", True)
        except Exception:
            self._safe_set_text(label_path, "", label_control)
        self._safe_set_position(label_path, -100000.0, -100000.0, label_control)

        if width <= 0.0 or height <= 0.0:
            return None

        if limit_width > 0.0 and width > limit_width:
            width = limit_width

        return {
            "width": width,
            "height": height,
        }

    def _safe_set_text(self, path, text, control=None):
        try:
            if control and hasattr(control, "SetText"):
                try:
                    control.SetText(text+"1", True)
                    control.SetText(text, True)
                except TypeError:
                    control.SetText(text+"1")
                    control.SetText(text)
                return
            try:
                control.asLabel().SetText(text+"1", True)
                control.asLabel().SetText(text, True)
            except TypeError:
                control.asLabel().SetText(text+"1")
                control.asLabel().SetText(text)
        except Exception:
            pass

    def _to_text_edit_box_control(self, control, path):
        if not control:
            try:
                control = self._screen.GetBaseUIControl(path)
            except Exception:
                control = None

        if control and hasattr(control, 'asTextEditBox'):
            try:
                te = control.asTextEditBox()
                if te:
                    return te
            except Exception:
                pass
        return None

    def _safe_get_edit_text(self, path, control=None):
        te = self._to_text_edit_box_control(control, path)
        if not te:
            return None
        try:
            return te.GetEditText()
        except Exception:
            return None

    def _safe_set_edit_text(self, path, text, control=None):
        te = self._to_text_edit_box_control(control, path)
        if not te:
            return False
        try:
            te.SetEditText(self._safe_text(text))
            return True
        except Exception:
            return False

    def _safe_set_edit_text_max_length(self, path, max_length, control=None):
        te = self._to_text_edit_box_control(control, path)
        if not te:
            return False
        try:
            max_len = int(max_length)
        except Exception:
            return False
        if max_len <= 0:
            return False
        try:
            te.SetEditTextMaxLength(max_len)
            return True
        except Exception:
            return False

    def _apply_label_native_props_then_text(self, path, label_props, text, control=None):
        if not isinstance(label_props, dict):
            label_props = {}

        line_padding = self._parse_line_padding(label_props.get("linePadding"))
        if line_padding is not None:
            self._safe_set_text_line_padding(path, line_padding, control)

        text_font_size = self._parse_text_font_scale(label_props.get("fontSize"))
        if text_font_size is not None:
            self._safe_set_text_font_size(path, text_font_size, control)

        text_align = self._parse_text_alignment(label_props.get("textAlign"))
        if text_align:
            self._safe_set_text_alignment(path, text_align, control)

        if label_props.get("shadow") is not None:
            self._safe_set_text_shadow(path, self._to_bool(label_props.get("shadow")), control)

        text_color = self._parse_text_color(label_props.get("color"))
        if text_color is not None:
            self._safe_set_text_color(path, text_color, control)

        self._safe_set_text(path, self._safe_text(text), control)

    def _safe_set_sprite(self, path, sprite, control=None):
        sprite_text = self._safe_text(sprite)
        if not sprite_text:
            return False

        if control and hasattr(control, "asImage"):
            try:
                image_control = control.asImage()
                if image_control and hasattr(image_control, "SetSprite"):
                    ret = image_control.SetSprite(sprite_text)
                    return ret is not False
            except Exception:
                pass

        if control and hasattr(control, "SetSprite"):
            try:
                ret = control.SetSprite(sprite_text)
                return ret is not False
            except Exception:
                pass

        return False

    def _safe_set_sprite_color(self, path, color, control=None):
        rgb = self._to_rgb_tuple(color)
        if rgb is None:
            return

        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteColor"):
            try:
                image_control.SetSpriteColor(rgb)
            except Exception:
                pass

    def _safe_set_sprite_gray(self, path, gray, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteGray"):
            try:
                image_control.SetSpriteGray(bool(gray))
            except Exception:
                pass

    def _safe_set_sprite_clip_ratio(self, path, ratio, control=None):
        image_control = self._to_image_control(control, path)
        if not image_control or not hasattr(image_control, "SetSpriteClipRatio"):
            return

        r = self._to_float(ratio, 0.0)
        if r < 0.0:
            r = 0.0
        if r > 1.0:
            r = 1.0
        try:
            image_control.SetSpriteClipRatio(r)
        except Exception:
            pass

    def _safe_set_sprite_uv(self, path, uv, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteUV"):
            try:
                image_control.SetSpriteUV(uv)
            except Exception:
                pass

    def _safe_set_sprite_uv_size(self, path, uv_size, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetSpriteUVSize"):
            try:
                image_control.SetSpriteUVSize(uv_size)
            except Exception:
                pass

    def _safe_set_ui_item(self, path, identifier, aux_value, is_enchanted=False, user_data=None, control=None):
        item_name = self._safe_text(identifier)
        if not item_name:
            return False

        try:
            aux_number = int(aux_value)
        except Exception:
            aux_number = 0

        enchant_flag = self._to_bool(is_enchanted)
        payload_user_data = user_data
        if isinstance(payload_user_data, dict) and not payload_user_data:
            payload_user_data = None

        item_control = self._to_item_renderer_control(control, path)
        if item_control and hasattr(item_control, 'SetUiItem'):
            try:
                return item_control.SetUiItem(item_name, aux_number, enchant_flag, payload_user_data) is not False
            except Exception:
                pass

        try:
            return self._screen.SetUiItem(path, item_name, aux_number, enchant_flag, payload_user_data) is not False
        except Exception:
            return False

    def _safe_set_image_adaption_type(self, path, adaption_type, adaption_data=None, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetImageAdaptionType"):
            try:
                image_control.SetImageAdaptionType(adaption_type, adaption_data)
            except Exception:
                pass

    def _safe_rotate(self, path, angle, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "Rotate"):
            try:
                image_control.Rotate(angle)
            except Exception:
                pass

    def _safe_set_rotate_pivot(self, path, pivot, control=None):
        image_control = self._to_image_control(control, path)
        if image_control and hasattr(image_control, "SetRotatePivot"):
            try:
                image_control.SetRotatePivot(pivot)
            except Exception:
                pass

    def _to_image_control(self, control, path):
        if control and hasattr(control, "asImage"):
            try:
                image_control = control.asImage()
                if image_control:
                    return image_control
            except Exception:
                pass

        try:
            base_control = self._screen.GetBaseUIControl(path)
            if base_control and hasattr(base_control, "asImage"):
                return base_control.asImage()
        except Exception:
            pass
        return None

    def _to_item_renderer_control(self, control, path):
        if control and hasattr(control, 'asItemRenderer'):
            try:
                item_control = control.asItemRenderer()
                if item_control:
                    return item_control
            except Exception:
                pass

        try:
            base_control = self._screen.GetBaseUIControl(path)
            if base_control and hasattr(base_control, 'asItemRenderer'):
                return base_control.asItemRenderer()
        except Exception:
            pass
        return None

    def _to_label_control(self, control, path):
        if control and hasattr(control, "asLabel"):
            try:
                label_control = control.asLabel()
                if label_control:
                    return label_control
            except Exception:
                pass

        try:
            base_control = self._screen.GetBaseUIControl(path)
            if base_control and hasattr(base_control, "asLabel"):
                return base_control.asLabel()
        except Exception:
            pass
        return None

    def _safe_set_text_color(self, path, color, control=None):
        rgb = self._to_rgb_tuple(color)
        if rgb is None:
            return

        if control and hasattr(control, "asLabel"):
            try:
                label_control = control.asLabel()
                if label_control and hasattr(label_control, "SetTextColor"):
                    label_control.SetTextColor(rgb)
                    return
            except Exception:
                pass

        if control and hasattr(control, "SetTextColor"):
            try:
                control.SetTextColor(rgb)
                return
            except Exception:
                pass

        try:
            if hasattr(self._screen, "SetTextColor"):
                rgba = (rgb[0], rgb[1], rgb[2], 1.0)
                self._screen.SetTextColor(path, rgba)
        except Exception:
            pass

    def _safe_set_text_font_size(self, path, scale, control=None):
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextFontSize"):
            try:
                label_control.SetTextFontSize(scale)
            except Exception:
                pass

    def _safe_set_text_alignment(self, path, alignment, control=None):
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextAlignment"):
            try:
                label_control.SetTextAlignment(alignment)
            except Exception:
                pass

    def _safe_set_text_line_padding(self, path, text_line_padding, control=None):
        label_control = self._to_label_control(control, path)
        if label_control and hasattr(label_control, "SetTextLinePadding"):
            try:
                label_control.SetTextLinePadding(text_line_padding)
            except Exception:
                pass

    def _safe_set_text_shadow(self, path, enabled, control=None):
        label_control = self._to_label_control(control, path)
        if not label_control:
            return
        try:
            if enabled and hasattr(label_control, "EnableTextShadow"):
                label_control.EnableTextShadow()
            elif (not enabled) and hasattr(label_control, "DisableTextShadow"):
                label_control.DisableTextShadow()
        except Exception:
            pass

    def _safe_set_position(self, path, x, y, control=None):
        try:
            pos = (int(round(x)), int(round(y)))
            if control:
                used_full = False
                if hasattr(control, "SetFullPosition"):
                    ret_x = control.SetFullPosition(axis="x", paramDict={"absoluteValue": float(pos[0]), "followType": "none", "relativeValue": 0.0})
                    ret_y = control.SetFullPosition(axis="y", paramDict={"absoluteValue": float(pos[1]), "followType": "none", "relativeValue": 0.0})
                    used_full = bool(ret_x) and bool(ret_y)

                if hasattr(control, "SetPosition"):
                    try:
                        control.SetPosition(pos)
                    except TypeError:
                        control.SetPosition(float(pos[0]), float(pos[1]))
                    except Exception:
                        if not used_full:
                            raise
                return
            self._screen.SetPosition(path, pos)
        except Exception:
            pass

    def _safe_set_size(self, path, w, h, control=None):
        try:
            width = int(round(w))
            height = int(round(h))
            if width < 0:
                width = 0
            if height < 0:
                height = 0
            size = (width, height)
            if control:
                used_full = False
                if hasattr(control, "SetFullSize"):
                    ret_w = control.SetFullSize(axis="x", paramDict={"absoluteValue": float(size[0]), "followType": "none", "relativeValue": 0.0})
                    ret_h = control.SetFullSize(axis="y", paramDict={"absoluteValue": float(size[1]), "followType": "none", "relativeValue": 0.0})
                    used_full = bool(ret_w) and bool(ret_h)

                if hasattr(control, "SetSize"):
                    try:
                        control.SetSize(size, True)
                    except TypeError:
                        control.SetSize(size)
                    except Exception:
                        if not used_full:
                            raise
                return
            self._screen.SetSize(path, size, True)
        except Exception:
            pass

    def _safe_set_visible(self, path, visible, control=None):
        try:
            if control and hasattr(control, "SetVisible"):
                control.SetVisible(bool(visible))
                return
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetVisible"):
                base.SetVisible(bool(visible))
        except Exception:
            pass

    def _safe_set_alpha(self, path, alpha, control=None):
        try:
            if control and hasattr(control, "SetAlpha"):
                control.SetAlpha(float(alpha))
                return
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetAlpha"):
                base.SetAlpha(float(alpha))
        except Exception:
            pass

    def _safe_set_layer(self, path, layer, control=None):
        try:
            layer_value = int(round(self._to_float(layer, 0.0)))
        except Exception:
            return

        try:
            if control and hasattr(control, "SetLayer"):
                control.SetLayer(layer_value)
                return
        except Exception:
            pass

        try:
            base = self._screen.GetBaseUIControl(path)
            if base and hasattr(base, "SetLayer"):
                base.SetLayer(layer_value)
                return
        except Exception:
            pass

        try:
            if hasattr(self._screen, "SetLayer"):
                self._screen.SetLayer(path, layer_value)
        except Exception:
            pass

    def _to_float(self, value, fallback):
        try:
            return float(value)
        except Exception:
            return float(fallback)

    def _parse_text_color(self, value):
        if not isinstance(value, Color):
            return None
        return value

    def _parse_text_font_size(self, value):
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text_value = self._safe_text(value).strip()
        if not text_value:
            return None

        try:
            return float(text_value)
        except Exception:
            return None

    def _parse_text_font_scale(self, value):
        font_size = self._parse_text_font_size(value)
        if font_size is None:
            return None

        base = self._TEXT_FONT_SIZE_BASE
        if base <= 0.0:
            return None

        return font_size / base

    def _parse_text_alignment(self, value):
        text_value = self._safe_text(value).strip().lower()
        if text_value in ("left", "start"):
            return "left"
        if text_value in ("right", "end"):
            return "right"
        if text_value in ("center", "middle"):
            return "center"
        return None

    def _parse_line_padding(self, value):
        if value is None or isinstance(value, bool):
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _to_rgb_tuple(self, color):
        if not isinstance(color, Color):
            return None
        return color.toRGBUnitTuple()

    def _parse_vec2(self, value):
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            return None
        return (
            self._to_float(value[0], 0.0),
            self._to_float(value[1], 0.0),
        )

    def _parse_vec4(self, value):
        if not isinstance(value, (list, tuple)) or len(value) < 4:
            return None
        return (
            self._to_float(value[0], 0.0),
            self._to_float(value[1], 0.0),
            self._to_float(value[2], 0.0),
            self._to_float(value[3], 0.0),
        )

    def _parse_image_adaption_type(self, style):
        if not isinstance(style, dict):
            return None

        explicit = self._safe_text(style.get("imageAdaptionType", "")).strip()
        if explicit in ("normal", "filled", "oldNineSlice", "originNineSlice"):
            return explicit

        resize_mode = self._safe_text(style.get("resizeMode", "")).strip().lower()
        if resize_mode in ("contain", "center"):
            return "normal"
        if resize_mode in ("cover", "stretch"):
            return "filled"
        return None

    def _to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        text = self._safe_text(value).strip().lower()
        return text in ("1", "true", "yes", "on")

    def _safe_text(self, value):
        if value is None:
            return ""
        try:
            # Prefer preserving unicode returned by engine APIs (e.g. edit_box).
            # The UI native layer typically expects UTF-8 encoded bytes in Py2.
            if isinstance(value, str):
                return value
            if isinstance(value, _UNICODE_TYPE):
                try:
                    return value.encode('utf-8')
                except Exception:
                    try:
                        return value.encode('utf-8', 'ignore')
                    except Exception:
                        return ""

            return "%s" % value
        except Exception:
            return ""
