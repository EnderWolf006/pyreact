import time

from .fiber import Fiber
from .hooks import with_current_fiber
from .hooks import run_effects


def _get_func_code(fn):
    if fn is None:
        return None
    return getattr(fn, 'func_code', getattr(fn, '__code__', None))


class FunctionComponent(object):
    def __init__(self, component_fn):
        if not callable(component_fn):
            raise TypeError("component_fn must be callable")
        self.component_fn = component_fn

    def __call__(self, props=None):
        return self.component_fn(props or {})


class ComponentInstance(object):
    def __init__(self, component_fn, props=None, rerender_callback=None):
        self.component_fn = component_fn
        self.props = props or {}
        self.pending_updates = []
        self.latest_output = None
        self.fiber = Fiber(
            component_fn=component_fn,
            props=self.props,
            rerender_callback=rerender_callback
        )
        self.last_render_duration_ms = 0.0

    def set_props(self, props):
        self.props = props or {}
        self.fiber.props = self.props

    def set_rerender_callback(self, callback):
        self.fiber.rerender_callback = callback

    def render(self):
        # Enforce: all module-level components used under render_app root must be
        # decorated with @Component, otherwise key/ref cannot be supported.
        if callable(self.component_fn) and not getattr(self.component_fn, '__pyreact_component__', False):
            name = getattr(self.component_fn, '__name__', 'component')
            raise TypeError(
                "Root component '%s' must be decorated with @Component (required for key/ref support)." % name
            )

        self.fiber.props = self.props
        self.fiber.begin_render()
        start_time = time.time()

        # NOTE: We intentionally do NOT use `sys.setprofile`-based enforcement
        # here, because `sys` is not guaranteed to be available in NetEase
        # ModSDK's Python whitelist.
        with with_current_fiber(self.fiber):
            try:
                output = self.component_fn(self.props)
            except TypeError:
                output = self.component_fn()

        self.fiber.finish_render()
        self.fiber.pending_state_update = False
        self.latest_output = output
        self.last_render_duration_ms = (time.time() - start_time) * 1000.0
        run_effects(self.fiber)
        return output


def render_component(component_fn, props=None, instance=None, rerender_callback=None):
    if isinstance(component_fn, FunctionComponent):
        fn = component_fn.component_fn
    else:
        fn = component_fn

    if instance is None:
        instance = ComponentInstance(
            component_fn=fn,
            props=props,
            rerender_callback=rerender_callback
        )
    else:
        instance.component_fn = fn
        instance.set_props(props)
        if rerender_callback is not None:
            instance.set_rerender_callback(rerender_callback)

    result = instance.render()
    return result
