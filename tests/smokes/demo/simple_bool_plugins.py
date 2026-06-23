from tests.smokes.demo.simple_slots import simple_bool_slot


@simple_bool_slot.plugin('name')
def plugin():
    raise AssertionError('plugin was executed')
