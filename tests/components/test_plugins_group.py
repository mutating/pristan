import pytest
from full_match import match

from pristan.components.plugin import Plugin
from pristan.components.plugins_group import PluginsGroup
from pristan.components.slot_caller import SlotCaller
from pristan.components.slot_code_representer import SlotCodeRepresenter


def test_bool():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)

    assert not PluginsGroup(caller)
    assert PluginsGroup(caller, plugins=[Plugin('name', lambda x: x, int, False, False)])


def test_repr():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)

    assert repr(PluginsGroup(caller)) == 'PluginsGroup(SlotCaller(SlotCodeRepresenter(λ), \'kek\', λ, False))'
    assert repr(PluginsGroup(caller, plugins=[Plugin('name', lambda x: x, int, False, False)])) == 'PluginsGroup(SlotCaller(SlotCodeRepresenter(λ), \'kek\', λ, False), plugins=[Plugin(\'name\', plugin_function=λ, expected_result_type=int, type_check=False, unique=False)])'


def test_it_saves_default_plugins_without_renaming():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    assert group.plugins == plugins
    assert group.plugins_by_requested_names == {
        'name': [plugins[0], plugins[1]],
        'name2': [plugins[2]],
    }


def test_it_saves_plugins_without_renaming():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller)

    group.add(plugins[0])
    group.add(plugins[1])
    group.add(plugins[2])

    assert group.plugins == plugins
    assert group.plugins_by_requested_names == {
        'name': [plugins[0], plugins[1]],
        'name2': [plugins[2]],
    }


def test_iter():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller)

    group.add(plugins[0])
    group.add(plugins[1])
    group.add(plugins[2])

    iteration_result = []

    for plugin in group:
        iteration_result.append(plugin)
        assert isinstance(plugin, Plugin)

    assert iteration_result == plugins


def test_zero_len():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    group = PluginsGroup(caller)

    assert len(group) == 0

    group.add(Plugin('name', lambda x: x, int, False, False))

    assert len(group) == 1

    group.delete_last_by_name('name')

    assert len(group) == 0


def test_len():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    assert len(group) == 3


def test_contains_by_name():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    plugins[1].set_name('name-2')
    group = PluginsGroup(caller, plugins=plugins)

    assert 'name' in group
    assert 'name2' in group
    assert 'name-2' in group

    assert 'name3' not in group
    assert 'name-3' not in group
    assert 'kek' not in group


def test_contains_with_not_valid_names():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    with pytest.raises(ValueError, match=match('The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, “name-22”. "kek-kek" is not a valid name for a plugin.')):
        'kek-kek' in group

    with pytest.raises(ValueError, match=match('The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, “name-22”. "kek-2-2" is not a valid name for a plugin.')):
        'kek-2-2' in group

    with pytest.raises(ValueError, match=match('The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, “name-22”. "kek--" is not a valid name for a plugin.')):
        'kek--' in group

    with pytest.raises(ValueError, match=match('The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, “name-22”. "@" is not a valid name for a plugin.')):
        '@' in group


def test_contains_plugins():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    assert plugins[0] in group
    assert plugins[1] in group
    assert plugins[2] in group

    assert Plugin('name3', lambda x: x, int, False, False) not in group
    assert Plugin('name-3', lambda x: x, int, False, False) not in group


def test_getitem_bad_key():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        group['kek-kek']

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        group['kek--']

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        group[123]

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        group[True]
