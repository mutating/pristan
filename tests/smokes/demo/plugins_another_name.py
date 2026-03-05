from tests.smokes.demo.simple_slots import simple_slot_2


@simple_slot_2.plugin('name2')
def plugin_2():
    return 2
