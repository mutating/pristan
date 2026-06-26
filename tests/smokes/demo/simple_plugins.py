from tests.smokes.demo.simple_slots import simple_slot_1


@simple_slot_1.plugin('name')
def plugin_1():
    return 1
