from tests.smokes.demo.simple_slots import simple_slot_3


@simple_slot_3.plugin('name')
def plugin() -> int:
    return 1
