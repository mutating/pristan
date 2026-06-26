from tests.smokes.demo.simple_slots import simple_one_slot


@simple_one_slot.plugin('name')
def plugin() -> int:
    return 7
