from pyreact import *

@Component
def CounterDemo():
    count, setCount = useState(0)

    def increment():
        setCount(count + 1)

    return Panel(
        style=Style(
            width="100%",
            height="100%",
            alignItems=AlignItems.center,
            justifyContent=JustifyContent.center,
        ),
        children=[
            Label(
                style=Style(marginBottom=8),
                fontSize=FontSize.large,
                shadow=True,
                content="这是一个计数器示例"
            ),
            FilledButton(
                style=Style(padding=8),
                default=Colors.dodgerBlue,
                hover=Colors.dodgerBlue.withAlpha(0.8),
                pressed=Colors.dodgerBlue.withAlpha(0.6),
                onClick=increment,
                children=Label(shadow=True, content="Count: " + str(count))
            ),
        ]
    )