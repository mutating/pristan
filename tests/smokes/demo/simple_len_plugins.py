from tests.smokes.demo.simple_slots import simple_len_slot


@simple_len_slot.plugin('name')
def plugin_1():
    return 9
