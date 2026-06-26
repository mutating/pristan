from tests.smokes.demo.simple_slots import simple_slot_4


@simple_slot_4.plugin('name')
def plugin() -> int:
    return 1
