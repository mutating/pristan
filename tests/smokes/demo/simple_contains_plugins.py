from tests.smokes.demo.simple_slots import simple_contains_slot


@simple_contains_slot.plugin('name')
def plugin_1():
    return 10
