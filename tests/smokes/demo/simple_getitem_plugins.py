from tests.smokes.demo.simple_slots import simple_slot_5


@simple_slot_5.plugin('name')
def plugin() -> int:
    return 1
