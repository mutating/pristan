from tests.smokes.demo.simple_slots import simple_explicit_plugin_names_slot


@simple_explicit_plugin_names_slot.plugin
def plugin():
    return 1
