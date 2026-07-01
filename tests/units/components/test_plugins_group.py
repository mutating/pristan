import pytest
from full_match import match

from pristan.components.plugin import Plugin
from pristan.components.plugins_group import PluginsGroup
from pristan.components.slot import Slot


@pytest.fixture
def group_with_named_duplicates():
    """Build a group with duplicate plugin names for deletion and renumbering tests."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
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
    """PluginsGroup truthiness reflects only whether it contains stored plugins, making an empty group false and a group initialized with a plugin true."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller

    assert not PluginsGroup(caller)
    assert PluginsGroup(caller, plugins=[Plugin('name', lambda x: x, int, False, False)])


def test_repr():
    """PluginsGroup repr includes the caller repr, omits an empty plugin list, and includes Plugin reprs when populated."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller

    assert repr(PluginsGroup(caller)) == 'PluginsGroup(SlotCaller(slot=Slot(lambda x: x, slot_name=\'kek\', type_check=False)))'
    assert repr(PluginsGroup(caller, plugins=[Plugin('name', lambda x: x, int, False, False)])) == 'PluginsGroup(SlotCaller(slot=Slot(lambda x: x, slot_name=\'kek\', type_check=False)), plugins=[Plugin(\'name\', plugin_function=lambda x: x, expected_result_type=int, type_check=False, unique=False)])'


def test_it_saves_default_plugins_without_renaming():
    """
    Constructor-supplied plugins are preserved and indexed by requested name without renaming.

    Duplicate-name suffixing belongs to Slot registration, not PluginsGroup initialization.
    """
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
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
    """Direct PluginsGroup.add preserves duplicate plugin names; it only stores plugins in order and buckets them by requested name, leaving suffix assignment to slot-level duplicate-name handling."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
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
    """PluginsGroup iteration yields each stored Plugin in insertion order, including duplicate requested names and differently named plugins."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
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
    """PluginsGroup length tracks add and `delete_last_by_name` cleanup from empty to one plugin and back to zero."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
    group = PluginsGroup(caller)

    assert len(group) == 0

    group.add(Plugin('name', lambda x: x, int, False, False))

    assert len(group) == 1

    group.delete_last_by_name('name')

    assert len(group) == 0


def test_len():
    """PluginsGroup length counts every stored plugin, including duplicate requested names."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    assert len(group) == 3


def test_contains_by_name():
    """String membership accepts requested names and exact numbered aliases, including `name-1` for the unsuffixed first plugin, and rejects valid absent names."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
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
    """Membership rejects malformed string names with ValueError and non-string/non-Plugin operands with TypeError."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
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
    """PluginsGroup membership accepts Plugin operands and treats them as present only when a registered plugin has the same requested name and actual name."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    assert plugins[0] in group
    assert plugins[1] in group
    assert plugins[2] in group

    assert Plugin('name', lambda x: x, int, False, False) in group
    assert Plugin('name2', lambda x: x, int, False, False) in group

    same_requested_name_with_missing_actual_name = Plugin('name', lambda x: x, int, False, False)
    same_requested_name_with_missing_actual_name.set_name('name-3')

    assert same_requested_name_with_missing_actual_name not in group

    different_requested_name_with_matching_actual_name = Plugin('other', lambda x: x, int, False, False)
    different_requested_name_with_matching_actual_name.set_name('name')

    assert different_requested_name_with_matching_actual_name not in group
    assert Plugin('name3', lambda x: x, int, False, False) not in group
    assert Plugin('name-3', lambda x: x, int, False, False) not in group


def test_getitem_bad_key():
    """PluginsGroup indexing rejects invalid keys with KeyError. Malformed string selectors and non-string values use the shared invalid-key message rather than returning a selection."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
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
    """Valid PluginsGroup indexing returns selection objects: base names select stored requested-name buckets, and absent valid base or suffixed keys return empty selections."""
    caller = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False).caller
    plugins = [
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name', lambda x: x, int, False, False),
        Plugin('name2', lambda x: x, int, False, False),
    ]
    group = PluginsGroup(caller, plugins=plugins)

    for key, expected_names in (
        ('name', ['name', 'name']),
        ('name-2', []),
        ('name2', ['name2']),
        ('kek', []),
        ('kek-2', []),
    ):
        assert [plugin.name for plugin in group[key]] == expected_names


def test_pop_by_base_name(group_with_named_duplicates):
    """Popping a base requested name returns and removes all plugins in that bucket, mutates the plugin list in place, and leaves other buckets intact."""
    group, plugins = group_with_named_duplicates
    plugins_reference = group.plugins

    assert group.pop('name') == plugins[:3]
    assert group.plugins is plugins_reference
    assert group.plugins == [plugins[3]]
    assert group.plugins_by_requested_names == {
        'name2': [plugins[3]],
    }


def test_pop_first_plugin_by_name_1(group_with_named_duplicates):
    """Popping `name-1` removes the unsuffixed first duplicate, mutates the existing plugins list in place, renumbers remaining duplicates, and keeps unrelated buckets intact."""
    group, plugins = group_with_named_duplicates
    plugins_reference = group.plugins

    assert group.pop('name-1') == [plugins[0]]
    assert group.plugins is plugins_reference
    assert [x.name for x in group.plugins] == ['name', 'name-2', 'name2']
    assert group.plugins_by_requested_names == {
        'name': [plugins[1], plugins[2]],
        'name2': [plugins[3]],
    }


def test_pop_middle_plugin_renumbers_remaining_duplicates(group_with_named_duplicates):
    """Popping `name-2` removes only that middle duplicate, mutates the plugins list in place, and renumbers later duplicates to keep the bucket compact."""
    group, plugins = group_with_named_duplicates
    plugins_reference = group.plugins

    assert group.pop('name-2') == [plugins[1]]
    assert group.plugins is plugins_reference
    assert [x.name for x in group.plugins] == ['name', 'name-2', 'name2']
    assert group.plugins_by_requested_names == {
        'name': [plugins[0], plugins[2]],
        'name2': [plugins[3]],
    }


def test_pop_last_plugin_keeps_compact_numbering(group_with_named_duplicates):
    """
    Popping the last suffixed duplicate by exact key removes only that plugin.

    The backing plugins list object and requested-name bucket stay in sync, and remaining duplicates keep compact names without a name-3 gap.
    """
    group, plugins = group_with_named_duplicates
    plugins_reference = group.plugins

    assert group.pop('name-3') == [plugins[2]]
    assert group.plugins is plugins_reference
    assert [x.name for x in group.plugins] == ['name', 'name-2', 'name2']
    assert group.plugins_by_requested_names == {
        'name': [plugins[0], plugins[1]],
        'name2': [plugins[3]],
    }


def test_pop_only_plugin_by_name_1_removes_requested_name_bucket(group_with_named_duplicates):
    """Popping `name2-1` removes the unsuffixed singleton bucket, mutates the list in place, deletes only that empty bucket, and leaves the `name` duplicates intact."""
    group, plugins = group_with_named_duplicates
    plugins_reference = group.plugins

    assert group.pop('name2-1') == [plugins[3]]
    assert group.plugins is plugins_reference
    assert group.plugins == plugins[:3]
    assert group.plugins_by_requested_names == {
        'name': plugins[:3],
    }


def test_pop_missing_valid_key(group_with_named_duplicates):
    """Popping a valid but absent key raises KeyError for that exact key, including an absent base name and an absent numbered duplicate."""
    group, _ = group_with_named_duplicates

    for key in ('name3', 'name-4'):
        with pytest.raises(KeyError, match=match(repr(key))):
            group.pop(key)


def test_pop_invalid_key(group_with_named_duplicates):
    """PluginsGroup.pop rejects malformed suffixed keys like 'name--' with the shared invalid-key KeyError before removal or renaming, rather than treating them as valid missing keys."""
    group, _ = group_with_named_duplicates
    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        group.pop('name--')
