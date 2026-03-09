from tests.smokes.demo.simple_slots import (
    simple_slot_1,
    simple_slot_3,
    simple_slot_4,
    simple_slot_5,
)


@simple_slot_1.plugin('name')  # type: ignore[attr-defined]
def plugin_1():
    return 1


@simple_slot_3.plugin('name')  # type: ignore[attr-defined]
def plugin_2():
    return 1


@simple_slot_4.plugin('name')  # type: ignore[attr-defined]
def plugin_3():
    return 1


@simple_slot_5.plugin('name')  # type: ignore[attr-defined]
def plugin_4():
    return 1
