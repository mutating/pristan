from tests.smokes.demo.simple_slots import simple_slot_6


@simple_slot_6.plugin('name')  # type: ignore[attr-defined]
def plugin_5():
    return 1


@simple_slot_6.plugin('name')  # type: ignore[attr-defined]
def plugin_6():
    return 2
