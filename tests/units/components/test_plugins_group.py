import pytest
from full_match import match

from pristan.components.plugin import Plugin
from pristan.components.plugins_group import PluginsGroup
from pristan.components.slot_caller import SlotCaller
from pristan.components.slot_code_representer import SlotCodeRepresenter


@pytest.fixture
def group_with_named_duplicates():
    """Build a group with duplicate plugin names for deletion and renumbering tests."""
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    plugins[1].set_name('name-2')
    plugins[2].set_name('name-3')
    return PluginsGroup(caller, plugins=plugins), plugins


def test_bool():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)

    assert not PluginsGroup(caller)
    assert PluginsGroup(caller, plugins=[Plugin('name', lambda x: x, int, False, False)])


def test_repr():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)

    assert repr(PluginsGroup(caller)) == 'PluginsGroup(SlotCaller(code_representation=SlotCodeRepresenter(λ), slot_name=\'kek\', slot_function=λ, type_check=False))'
    assert repr(PluginsGroup(caller, plugins=[Plugin('name', lambda x: x, int, False, False)])) == 'PluginsGroup(SlotCaller(code_representation=SlotCodeRepresenter(λ), slot_name=\'kek\', slot_function=λ, type_check=False), plugins=[Plugin(\'name\', plugin_function=lambda x: x, expected_result_type=int, type_check=False, unique=False)])'


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
    assert 'name-1' in group
    assert 'name2' in group
    assert 'name-2' in group

    assert 'name3' not in group
    assert 'name-3' not in group
    assert 'kek' not in group
    assert 'kek-2' not in group
    assert 'kek-1' not in group


def test_contains_with_not_valid_names():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    with pytest.raises(ValueError, match=match("The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, 'name-22'. 'kek-kek' is not a valid name for a plugin.")):
        'kek-kek' in group  # noqa: B015

    with pytest.raises(ValueError, match=match("The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, 'name-22'. 'kek-2-2' is not a valid name for a plugin.")):
        'kek-2-2' in group  # noqa: B015

    with pytest.raises(ValueError, match=match("The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, 'name-22'. 'kek--' is not a valid name for a plugin.")):
        'kek--' in group  # noqa: B015

    with pytest.raises(ValueError, match=match("The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, 'name-22'. '@' is not a valid name for a plugin.")):
        '@' in group  # noqa: B015

    with pytest.raises(ValueError, match=match("The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, 'name-22'. 'kek-0' is not a valid name for a plugin.")):
        'kek-0' in group  # noqa: B015

    with pytest.raises(TypeError, match=match('Checking for inclusion is only possible for strings of a valid format or for plugin objects.')):
        123 in group  # noqa: B015

    with pytest.raises(TypeError, match=match('Checking for inclusion is only possible for strings of a valid format or for plugin objects.')):
        False in group  # noqa: B015

    with pytest.raises(TypeError, match=match('Checking for inclusion is only possible for strings of a valid format or for plugin objects.')):
        None in group  # noqa: B015


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


def test_getitem_good_key():
    caller = SlotCaller(SlotCodeRepresenter(lambda x: x), 'kek', lambda x: x, False)
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    assert group['name']
    assert len(group['name']) == 2
    assert [x.name for x in group['name']] == ['name', 'name']

    assert not group['name-2']
    assert len(group['name-2']) == 0
    assert [x.name for x in group['name-2']] == []

    assert group['name2']
    assert len(group['name2']) == 1
    assert [x.name for x in group['name2']] == ['name2']

    assert not group['kek']
    assert len(group['kek']) == 0
    assert [x.name for x in group['kek']] == []

    assert not group['kek-2']
    assert len(group['kek-2']) == 0
    assert [x.name for x in group['kek-2']] == []


def test_pop_by_base_name(group_with_named_duplicates):
    group, plugins = group_with_named_duplicates
    removed_plugins = group.pop('name')

    assert removed_plugins == plugins[:3]
    assert group.plugins == [plugins[3]]
    assert group.plugins_by_requested_names == {
        'name2': [plugins[3]],
    }


def test_pop_first_plugin_by_name_1(group_with_named_duplicates):
    group, plugins = group_with_named_duplicates
    removed_plugins = group.pop('name-1')

    assert removed_plugins == [plugins[0]]
    assert [x.name for x in group.plugins] == ['name', 'name-2', 'name2']
    assert group.plugins_by_requested_names == {
        'name': [plugins[1], plugins[2]],
        'name2': [plugins[3]],
    }


def test_pop_middle_plugin_renumbers_remaining_duplicates(group_with_named_duplicates):
    group, plugins = group_with_named_duplicates
    removed_plugins = group.pop('name-2')

    assert removed_plugins == [plugins[1]]
    assert [x.name for x in group.plugins] == ['name', 'name-2', 'name2']
    assert group.plugins_by_requested_names == {
        'name': [plugins[0], plugins[2]],
        'name2': [plugins[3]],
    }


def test_pop_last_plugin_keeps_compact_numbering(group_with_named_duplicates):
    group, plugins = group_with_named_duplicates
    removed_plugins = group.pop('name-3')

    assert removed_plugins == [plugins[2]]
    assert [x.name for x in group.plugins] == ['name', 'name-2', 'name2']
    assert group.plugins_by_requested_names == {
        'name': [plugins[0], plugins[1]],
        'name2': [plugins[3]],
    }


def test_pop_only_plugin_by_name_1_removes_requested_name_bucket(group_with_named_duplicates):
    group, plugins = group_with_named_duplicates

    removed_plugins = group.pop('name2-1')

    assert removed_plugins == [plugins[3]]
    assert group.plugins == plugins[:3]
    assert group.plugins_by_requested_names == {
        'name': plugins[:3],
    }


def test_pop_missing_valid_key(group_with_named_duplicates):
    group, _ = group_with_named_duplicates
    with pytest.raises(KeyError, match=match("'name3'")):
        group.pop('name3')

    with pytest.raises(KeyError, match=match("'name-4'")):
        group.pop('name-4')


def test_pop_invalid_key(group_with_named_duplicates):
    group, _ = group_with_named_duplicates
    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        group.pop('name--')
