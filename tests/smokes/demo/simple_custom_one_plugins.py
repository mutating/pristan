from tests.smokes.demo.simple_slots import simple_custom_one_slot


@simple_custom_one_slot.plugin('name2')
def plugin() -> int:
    return 8
