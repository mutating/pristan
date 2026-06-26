import sys
from typing import Dict, List

import pytest
from full_match import match
from sigmatch.errors import SignatureMismatchError

import pristan.components.slot as slot_module
from pristan import slot as public_slot
from pristan.components.slot import Slot
from pristan.components.slot_caller import CallerWithPlugins
from pristan.errors import (
    CannotGetVersionsError,
    EntrypointLoadingError,
    ExplicitNameRequiredError,
    NumberOfCallsError,
    OneResolutionError,
    PrimadonnaPluginError,
    PristanException,
)


def test_set_max_less_than_zero():
    with pytest.raises(ValueError, match=match('The maximum number of plugins cannot be less than zero.')):
        Slot(lambda x: x, signature='.', slot_name='slot_name', max=-1, type_check=False, entrypoint_group='pristan', unique=False)


def test_bool_loads_entrypoints_before_checking_local_plugins(monkeypatch):
    """Local plugins do not short-circuit entry point loading.

    The slot already has a local plugin, so an implementation that checked
    local plugin presence first would return True. The failing provider proves
    that bool resolves entry points before looking at the local collection.
    """
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    @slot.plugin
    def plugin():
        raise AssertionError('plugin was executed')

    provider_error = KeyError('provider')

    def get_entries(group=None):
        assert group == 'pristan'
        raise provider_error

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert len(slot) == 1

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        bool(slot)

    assert exception_info.value.__cause__ is provider_error
    assert not slot.loaded


def test_bool_passes_custom_entrypoint_group(monkeypatch):
    """Bool uses the configured entry point group when it resolves plugins."""
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='custom-group', unique=False)

    def get_entries(group=None):
        assert group == 'custom-group'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not bool(slot)

    assert slot.loaded


def test_bool_is_idempotent_after_successful_loading(monkeypatch):
    """A successfully loaded slot is not resolved again by repeated bool calls."""
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    provider_calls = []

    class FakeEntryPoint:
        def load(self):
            @slot.plugin('plugin')
            def plugin():
                return None

    def get_entries(group=None):
        provider_calls.append(group)
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)
    assert bool(slot)

    assert provider_calls == ['pristan']
    assert [plugin.name for plugin in slot.plugins.plugins] == ['plugin']


def test_bool_does_not_execute_default_or_plugins(monkeypatch):
    """Truthiness does not call the slot body or registered plugin functions."""
    def default():
        raise AssertionError('default body was executed')

    slot = Slot(default, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    @slot.plugin
    def plugin():
        raise AssertionError('plugin was executed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)


def test_bool_short_circuits_default_body_when_plugins_exist(monkeypatch):
    """A present plugin makes bool true without reading fallback body state."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    @slot.plugin
    def plugin():
        raise AssertionError('plugin was executed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot.caller.code_representation = BrokenCodeRepresentation()
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)


def test_bool_with_empty_loaded_entrypoints_depends_on_default_body(monkeypatch):
    """Empty loaded entry points leave truthiness to current body detection.

    All representative body shapes are declared inside this test and then
    checked as one table, so the body-source examples stay close to the
    expectation they document without module-level support functions.
    """
    def empty_body():
        pass

    def ellipsis_body():
        ...

    def docstring_body():
        """Only a docstring."""

    def docstring_with_pass_body():
        """Docstring plus pass."""
        pass  # noqa: PIE790

    def empty_list_body() -> List[int]:
        return []

    def empty_dict_body() -> Dict[str, int]:
        return {}

    def bare_return_body():
        return

    def none_return_body():
        return None

    def unannotated_list_body():
        return []

    def docstring_with_annotated_list_body() -> List[int]:
        """Docstring plus annotated empty list return."""
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for function, expected in (
        (empty_body, False),
        (ellipsis_body, False),
        (docstring_body, False),
        (docstring_with_pass_body, False),
        (empty_list_body, False),
        (empty_dict_body, False),
        (bare_return_body, True),
        (none_return_body, True),
        (unannotated_list_body, True),
        (docstring_with_annotated_list_body, True),
    ):
        slot = Slot(function, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

        assert bool(slot) is expected


def test_bool_with_fixture_container_annotations_is_false_for_empty_returns(monkeypatch, list_type, dict_type):
    """Fixture-provided list and dict annotations use the existing empty-return rule."""
    def list_slot() -> list_type:
        return []

    def dict_slot() -> dict_type:
        return {}

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for function in (list_slot, dict_slot):
        assert not bool(Slot(function, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False))


def test_bool_keeps_loaded_after_successful_load_and_inspection_error(monkeypatch):
    """A fallback inspection failure after successful loading does not reset loaded."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    requested_groups = []
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def get_entries(group=None):
        requested_groups.append(group)
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)
    slot.caller.code_representation = BrokenCodeRepresentation()

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        bool(slot)

    assert slot.loaded

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        bool(slot)

    assert requested_groups == ['pristan']


def test_len_and_contains_do_not_load_entrypoints(monkeypatch):
    """Length and valid membership checks remain plugin-only no-load operations."""
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def get_entries(group=None):
        assert group == 'pristan'
        raise RuntimeError('provider')

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert len(slot) == 0
    assert 'plugin' not in slot


def test_invalid_contains_does_not_load_entrypoints(monkeypatch):
    """Invalid membership checks raise local collection errors without loading."""
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def get_entries(group=None):
        assert group == 'pristan'
        raise RuntimeError('provider')

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(ValueError, match=match("The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, 'name-22'. 'bad--' is not a valid name for a plugin.")):
        'bad--' in slot  # noqa: B015

    with pytest.raises(TypeError, match=match('Checking for inclusion is only possible for strings of a valid format or for plugin objects.')):
        1 in slot  # noqa: B015


def test_iter_creation_does_not_load_until_consumed(monkeypatch):
    """Slot iteration is lazy until the generator is consumed."""
    def empty_body():
        pass

    provider_error = RuntimeError('provider')
    calls = []
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def get_entries(group=None):
        calls.append(group)
        raise provider_error

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    iterator = iter(slot)

    assert calls == []

    with pytest.raises(EntrypointLoadingError) as exception_info:
        next(iterator)

    assert exception_info.value.__cause__ is provider_error
    assert calls == ['pristan']


def test_truthy_slot_with_non_empty_default_can_have_zero_plugins(monkeypatch):
    """Truthiness is not equivalent to plugin collection size."""
    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = Slot(none_return_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)
    assert len(slot) == 0


def test_getitem_loads_before_returning_selection(monkeypatch):
    """Selection lookup resolves entry points before returning CallerWithPlugins."""
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert len(slot['missing']) == 0
    assert slot.loaded


def test_getitem_and_delitem_load_errors_dominate_key_validation(monkeypatch):
    """Lazy load failures happen before invalid-key validation."""
    def empty_body():
        pass

    def getitem_invalid(slot):
        slot['bad--']

    def delitem_invalid(slot):
        del slot['bad--']

    def make_failing_provider(provider_error):
        def get_entries(group=None):
            assert group == 'pristan'
            raise provider_error

        return get_entries

    for operation in (getitem_invalid, delitem_invalid):
        provider_error = RuntimeError('provider')
        slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
        monkeypatch.setattr(slot_module, 'entry_points', make_failing_provider(provider_error))

        with pytest.raises(EntrypointLoadingError) as exception_info:
            operation(slot)

        assert exception_info.value.__cause__ is provider_error


def test_saved_selection_is_snapshot_and_does_not_load_again(monkeypatch):
    """Saved selections keep their plugin snapshots for `.one` after parent mutation."""
    def empty_body():
        pass

    requested_groups = []
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def get_entries(group=None):
        requested_groups.append(group)
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    @slot.plugin('group')
    def first_group_plugin():
        return None

    @slot.plugin('group')
    def second_group_plugin():
        return None

    singleton_selection = slot['plugin']
    grouped_selection = slot['group']
    empty_selection = slot['missing']

    del slot['plugin']
    del slot['group']

    @slot.plugin('missing')
    def later_plugin():
        return None

    @slot.plugin('group')
    def later_group_plugin():
        return None

    assert bool(singleton_selection)
    assert len(singleton_selection) == 1
    assert singleton_selection.one is singleton_selection
    assert len(slot['plugin']) == 0
    with pytest.raises(OneResolutionError, match=match('Slot "empty_body" has 2 registered plugins, so .one cannot choose one.')):
        _ = slot.one
    assert len(grouped_selection) == 2
    assert [plugin.name for plugin in grouped_selection] == ['group', 'group-2']
    assert [plugin.name for plugin in slot['group']] == ['group']
    with pytest.raises(OneResolutionError, match=match('Selection from slot "empty_body" has 2 selected plugins, so .one cannot choose one.')):
        _ = grouped_selection.one
    assert not bool(empty_selection)
    assert len(empty_selection) == 0
    with pytest.raises(OneResolutionError, match=match('Selection from slot "empty_body" has no selected plugins and the slot body is empty.')):
        _ = empty_selection.one
    assert bool(slot)
    assert requested_groups == ['pristan']


def test_selection_bool_branches(monkeypatch):
    """CallerWithPlugins bool covers plugin, fallback-true, and fallback-false branches."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)
    slot_with_plugin = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    @slot_with_plugin.plugin
    def plugin():
        return None

    slot_with_plugin.caller.code_representation = BrokenCodeRepresentation()

    assert bool(slot_with_plugin['plugin'])

    assert bool(Slot(none_return_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)['missing'])
    assert not bool(Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)['missing'])


def test_selection_bool_does_not_execute_default_or_plugins(monkeypatch):
    """Selection truthiness does not call the slot body or selected plugins."""
    def default():
        raise AssertionError('default body was executed')

    slot = Slot(default, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    @slot.plugin('plugin')
    def plugin():
        raise AssertionError('plugin was executed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot['missing'])
    assert bool(slot['plugin'])


def test_selection_bool_for_absent_duplicate_depends_on_default_body(monkeypatch):
    """An absent numbered duplicate is empty but still uses fallback truthiness."""
    def empty_body():
        pass

    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for body, expected_bool in (
        (empty_body, False),
        (none_return_body, True),
    ):
        current_slot = Slot(body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

        @current_slot.plugin('name')
        def plugin():
            return None

        selection = current_slot['name-3']
        assert bool(selection) is expected_bool
        assert len(selection) == 0


def test_del_last_plugin_updates_parent_bool(monkeypatch):
    """After deleting the last plugin, parent bool falls back to default body state."""
    def empty_body():
        pass

    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for body, expected_bool in (
        (empty_body, False),
        (none_return_body, True),
    ):
        current_slot = Slot(body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

        @current_slot.plugin('plugin')
        def plugin():
            return None

        del current_slot['plugin']

        assert bool(current_slot) is expected_bool


def test_pop_existing_returns_detached_truthy_selection(monkeypatch):
    """Popping an existing plugin returns a detached truthy selection."""
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    popped_selection = slot.pop('plugin')

    assert bool(popped_selection)
    assert len(popped_selection) == 1
    assert not bool(slot)


def test_pop_existing_with_default_returns_selection_not_default(monkeypatch):
    """A found key makes pop return a selection even when a default is supplied."""
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    default = object()
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    popped_selection = slot.pop('plugin', default)

    assert popped_selection is not default
    assert bool(popped_selection)


@pytest.mark.parametrize('key', ['missing', 'bad--'])
def test_pop_default_returns_default_after_successful_load(monkeypatch, key):
    """A missing or invalid plugin key returns the default after loading succeeds."""
    def empty_body():
        pass

    default = object()
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert slot.pop(key, default) is default
    assert slot.loaded


def test_duplicate_plugin_selection_keys(monkeypatch):
    """Base-name lookup returns duplicate bucket; numbered keys select exact matches."""
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('name')
    def plugin_1():
        return None

    @slot.plugin('name')
    def plugin_2():
        return None

    for key, expected_names in (
        ('name', ['name', 'name-2']),
        ('name-1', ['name']),
        ('name-2', ['name-2']),
        ('name-3', []),
    ):
        assert [plugin.name for plugin in slot[key]] == expected_names


def test_slot_and_caller_with_plugins_one_are_read_only_properties(monkeypatch):
    """`.one` is read-only and cannot be shadowed by failed assignment or deletion."""
    @public_slot
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    selection = slot['plugin']

    assert [plugin.name for plugin in slot.one] == ['plugin']
    assert selection.one is selection

    if sys.version_info < (3, 11):
        setter_message = "can't set attribute"
        deleter_message = "can't delete attribute"
    else:
        setter_message = "property 'one' of '{class_name}' object has no setter"
        deleter_message = "property 'one' of '{class_name}' object has no deleter"

    with pytest.raises(AttributeError, match=match(setter_message.format(class_name='Slot'))):
        slot.one = object()  # type: ignore[misc]
    with pytest.raises(AttributeError, match=match(setter_message.format(class_name='CallerWithPlugins'))):
        selection.one = object()  # type: ignore[misc]
    with pytest.raises(AttributeError, match=match(deleter_message.format(class_name='Slot'))):
        del slot.one  # type: ignore[misc]
    with pytest.raises(AttributeError, match=match(deleter_message.format(class_name='CallerWithPlugins'))):
        del selection.one  # type: ignore[misc]

    assert [plugin.name for plugin in slot.one] == ['plugin']
    assert selection.one is selection


def test_slot_one_returns_caller_with_plugins_for_singleton_and_fallback(monkeypatch, subscribable_list_type, subscribable_dict_type):
    """`Slot.one` returns callable selections for singleton plugins and non-empty fallback bodies across public forms."""
    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @public_slot
    def bare_slot() -> subscribable_list_type[str]:
        return []

    @bare_slot.plugin
    def bare_plugin() -> str:
        return 'bare'

    @public_slot()
    def factory_slot() -> subscribable_dict_type[str, int]:
        return {}

    @factory_slot.plugin('factory')
    def factory_plugin() -> int:
        return 1

    @public_slot('named_slot')
    def named_slot() -> subscribable_list_type[int]:
        return []

    @named_slot.plugin('named')
    def named_plugin() -> int:
        return 3

    @public_slot(signature='.', name='configured_slot', max=1, type_check=False)
    def configured_slot(_value) -> subscribable_list_type[str]:
        return []

    @configured_slot.plugin
    def configured_plugin(value) -> int:
        return value

    def direct_body() -> subscribable_dict_type[str, int]:
        return {}

    direct_slot = public_slot(direct_body)

    @direct_slot.plugin('direct')
    def direct_plugin() -> int:
        return 2

    def direct_named_body() -> subscribable_dict_type[str, int]:
        return {}

    direct_named_slot = public_slot(direct_named_body, name='direct_named_slot')

    @direct_named_slot.plugin('direct_named')
    def direct_named_plugin() -> int:
        return 4

    @public_slot
    def bare_fallback_slot() -> subscribable_list_type[str]:
        """A non-empty fallback body."""
        return []

    @public_slot()
    def factory_fallback_slot() -> subscribable_dict_type[str, int]:
        """A non-empty fallback body."""
        return {}

    @public_slot(signature='.', name='configured_fallback_slot', max=1, type_check=False)
    def configured_fallback_slot(_value) -> subscribable_list_type[str]:
        """A non-empty fallback body."""
        return []

    def direct_fallback_body() -> subscribable_list_type[str]:
        """A non-empty fallback body."""
        return []

    direct_fallback_slot = public_slot(direct_fallback_body)

    @public_slot('named_fallback_slot')
    def named_fallback_slot() -> subscribable_list_type[int]:
        """A non-empty fallback body."""
        return []

    def direct_named_fallback_body() -> subscribable_dict_type[str, int]:
        """A non-empty fallback body."""
        return {}

    direct_named_fallback_slot = public_slot(direct_named_fallback_body, name='direct_named_fallback_slot')

    for current_slot, call_arguments, expected_plugin_count, expected_result in (
        (bare_slot, (), 1, ['bare']),
        (factory_slot, (), 1, {'factory': 1}),
        (named_slot, (), 1, [3]),
        (configured_slot, (1,), 1, [1]),
        (direct_slot, (), 1, {'direct': 2}),
        (direct_named_slot, (), 1, {'direct_named': 4}),
        (bare_fallback_slot, (), 0, []),
        (factory_fallback_slot, (), 0, {}),
        (named_fallback_slot, (), 0, []),
        (configured_fallback_slot, (1,), 0, []),
        (direct_fallback_slot, (), 0, []),
        (direct_named_fallback_slot, (), 0, {}),
    ):
        resolved_selection = current_slot.one

        assert isinstance(resolved_selection, CallerWithPlugins)
        assert bool(resolved_selection)
        assert len(resolved_selection) == expected_plugin_count
        assert resolved_selection(*call_arguments) == expected_result


def test_caller_with_plugins_one_resolves_by_count_and_fallback():
    """Selections return themselves for one plugin or fallback, else raise selection-specific errors."""
    @public_slot
    def empty_body():
        pass

    @public_slot(name='fallback_slot')
    def fallback_body():
        return None

    @public_slot(name='plugin_slot')
    def plugin_body():
        pass

    empty_slot = empty_body
    fallback_slot = fallback_body
    plugin_slot = plugin_body

    @plugin_slot.plugin('plugin')
    def plugin():
        return None

    @plugin_slot.plugin('group')
    def first_group_plugin():
        return None

    @plugin_slot.plugin('group')
    def second_group_plugin():
        return None

    with pytest.raises(OneResolutionError, match=match('Selection from slot "empty_body" has no selected plugins and the slot body is empty.')):
        _ = CallerWithPlugins(empty_slot.caller, []).one

    fallback_selection = CallerWithPlugins(fallback_slot.caller, [])
    assert fallback_selection.one is fallback_selection

    singleton_selection = plugin_slot.plugins['plugin']
    assert singleton_selection.one is singleton_selection

    with pytest.raises(OneResolutionError, match=match('Selection from slot "plugin_slot" has 2 selected plugins, so .one cannot choose one.')):
        _ = plugin_slot.plugins['group'].one


def test_caller_with_plugins_one_does_not_load_entrypoints(monkeypatch):
    """A saved selection does not trigger entry point loading again."""
    @public_slot
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    selection = slot['plugin']

    def raise_loading_error():
        raise RuntimeError('loading failed')

    slot._load_entrypoints = raise_loading_error  # type: ignore[method-assign]

    assert selection.one is selection


@pytest.mark.parametrize(('operation_name', 'remaining_plugin_count'), [('getitem', 1), ('pop', 0)])
def test_getitem_and_pop_selections_resolve_loaded_plugins_through_one(monkeypatch, subscribable_list_type, operation_name, remaining_plugin_count):
    """Getitem/pop selections resolve newly loaded plugins through `.one`; pop mutates after successful loading."""
    @public_slot
    def empty_body() -> subscribable_list_type[int]:
        return []

    slot = empty_body

    class FakeEntryPoint:
        def load(self):
            @slot.plugin('name')
            def plugin():
                return 1

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    operations = {
        'getitem': lambda: slot['name'],
        'pop': lambda: slot.pop('name'),
    }
    selection = operations[operation_name]()

    assert selection.one() == [1]
    assert slot.loaded
    assert len(slot) == remaining_plugin_count


@pytest.mark.parametrize('operation_name', ['getitem', 'pop'])
def test_getitem_and_pop_loading_errors_prevent_selection_creation(monkeypatch, operation_name):
    """Loading errors prevent getitem/pop selection creation and pop parent mutation."""
    @public_slot
    def empty_body() -> List[int]:
        return []

    slot = empty_body

    @slot.plugin('name')
    def local_plugin():
        return 1

    loading_error = RuntimeError('loading failed')

    def get_entries(group=None):
        assert group == 'pristan'
        raise loading_error

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    operations = {
        'getitem': lambda: slot['name'],
        'pop': lambda: slot.pop('name'),
    }

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        operations[operation_name]()

    assert exception_info.value.__cause__ is loading_error
    assert not slot.loaded
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name']


@pytest.mark.parametrize(
    ('access_selection', 'remaining_plugin_count'),
    [
        (lambda slot: slot.one, 1),
        (lambda slot: slot['name'].one, 1),
        (lambda slot: slot.pop('name').one, 0),
    ],
    ids=('slot', 'getitem', 'pop'),
)
def test_public_one_single_plugin_access_paths_return_callable_selections(monkeypatch, subscribable_list_type, access_selection, remaining_plugin_count):
    """Public singleton access paths return callable selections.

    The pop row proves parent mutation does not affect the returned selection.
    """
    @public_slot
    def empty_body() -> subscribable_list_type[int]:
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('name')
    def plugin():
        return 1

    selection = access_selection(slot)

    assert selection() == [1]
    assert len(slot) == remaining_plugin_count
    assert slot.loaded


def test_slot_one_calls_load_entrypoints_once_per_access():
    """Every `Slot.one` access calls the lazy entry-point loader hook once."""
    @public_slot
    def empty_body():
        pass

    load_calls = []
    slot = empty_body

    @slot.plugin('plugin')
    def plugin():
        return None

    def load_entrypoints():
        load_calls.append('load')

    slot._load_entrypoints = load_entrypoints  # type: ignore[method-assign]

    _ = slot.one
    _ = slot.one

    assert load_calls == ['load', 'load']


def test_slot_one_uses_plugins_loaded_before_snapshot():
    """The `Slot.one` snapshot is created after entry point loading."""
    @public_slot
    def empty_body():
        pass

    slot = empty_body

    def load_entrypoints():
        @slot.plugin('loaded')
        def plugin():
            return None

    slot._load_entrypoints = load_entrypoints  # type: ignore[method-assign]

    resolved_selection = slot.one

    assert [plugin.name for plugin in resolved_selection] == ['loaded']


def test_slot_one_load_error_dominates_local_singleton():
    """Entry point loading failures dominate a locally resolvable singleton."""
    @public_slot
    def empty_body():
        pass

    slot = empty_body

    @slot.plugin('plugin')
    def plugin():
        return None

    def load_entrypoints():
        raise RuntimeError('loading failed')

    slot._load_entrypoints = load_entrypoints  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match=match('loading failed')):
        _ = slot.one


def test_slot_one_load_error_dominates_fallback_body():
    """Entry point loading failures dominate fallback-body resolution."""
    @public_slot
    def fallback_body():
        return None

    slot = fallback_body

    def load_entrypoints():
        raise RuntimeError('loading failed')

    slot._load_entrypoints = load_entrypoints  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match=match('loading failed')):
        _ = slot.one


def test_slot_one_counts_local_and_loaded_plugins_together():
    """`Slot.one` counts local and newly loaded plugins as one candidate set."""
    @public_slot(name='sample_slot')
    def empty_body():
        pass

    slot = empty_body

    @slot.plugin('local')
    def local_plugin():
        return None

    def load_entrypoints():
        @slot.plugin('loaded')
        def loaded_plugin():
            return None

    slot._load_entrypoints = load_entrypoints  # type: ignore[method-assign]

    with pytest.raises(OneResolutionError, match=match('Slot "sample_slot" has 2 registered plugins, so .one cannot choose one.')):
        _ = slot.one

    assert [plugin.name for plugin in slot.plugins.plugins] == ['local', 'loaded']


def test_slot_one_failed_loading_keeps_partial_plugins_and_retries(monkeypatch):
    """Failed `Slot.one` loading keeps partial plugins and retries from the start."""
    class FakeEntryPoint:
        def load(self):
            @slot.plugin('name')
            def plugin():
                return None

            raise RuntimeError('stable failure')

    @public_slot
    def empty_body():
        pass

    slot = empty_body

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for _ in range(2):
        with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
            _ = slot.one

        assert isinstance(exception_info.value.__cause__, RuntimeError)
        assert str(exception_info.value.__cause__) == 'stable failure'
        assert not slot.loaded

    assert [plugin.name for plugin in slot.plugins.plugins] == ['name', 'name-2']


def test_slot_one_passes_custom_entrypoint_group(monkeypatch):
    """`Slot.one` uses the configured entry point group during loading."""
    @public_slot(entrypoint_group='custom-group')
    def empty_body():
        pass

    slot = empty_body

    class FakeEntryPoint:
        def load(self):
            @slot.plugin('loaded')
            def plugin():
                return None

    def get_entries(group=None):
        assert group == 'custom-group'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert [plugin.name for plugin in slot.one] == ['loaded']


def test_slot_one_raises_slot_specific_resolution_errors(monkeypatch):
    """`Slot.one` uses slot-specific resolution error messages."""
    @public_slot(name='empty_slot')
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    empty_slot = empty_body

    with pytest.raises(OneResolutionError, match=match('Slot "empty_slot" has no registered plugins and its body is empty.')):
        _ = empty_slot.one

    @public_slot(name='plugin_slot')
    def plugin_body():
        pass

    plugin_slot = plugin_body

    @plugin_slot.plugin('first')
    def first():
        return None

    @plugin_slot.plugin('second')
    def second():
        return None

    with pytest.raises(OneResolutionError, match=match('Slot "plugin_slot" has 2 registered plugins, so .one cannot choose one.')):
        _ = plugin_slot.one


def test_one_raises_for_empty_bodies_without_plugins(monkeypatch, list_type, dict_type):
    """`Slot.one` uses existing empty-body rules for slots and selections.

    Annotated empty list/dict returns are not fallback candidates.
    """
    def empty_body():
        pass

    def ellipsis_body():
        ...

    def docstring_body():
        """Only a docstring."""

    def docstring_with_pass_body():
        """Docstring plus pass."""
        pass  # noqa: PIE790

    def empty_list_body() -> list_type:
        return []

    def empty_dict_body() -> dict_type:
        return {}

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for body_function in (
        empty_body,
        ellipsis_body,
        docstring_body,
        docstring_with_pass_body,
        empty_list_body,
        empty_dict_body,
    ):
        slot = public_slot(body_function)

        with pytest.raises(OneResolutionError, match=match(f'Slot "{body_function.__name__}" has no registered plugins and its body is empty.')):
            _ = slot.one

    representative_slot = public_slot(empty_list_body, name='representative')

    with pytest.raises(OneResolutionError, match=match('Selection from slot "representative" has no selected plugins and the slot body is empty.')):
        _ = representative_slot['missing'].one


def test_slot_one_resolves_non_empty_fallback_bodies(monkeypatch, subscribable_list_type, subscribable_dict_type):
    """`Slot.one` treats non-empty fallback bodies as one candidate.

    Rows cover unannotated None normalization and list/dict results of any size.
    """
    def unannotated_list_body():
        return []

    def unannotated_dict_body():
        return {}

    def bare_return_body():
        return

    def none_return_body():
        return None

    def scalar_body():
        return 1

    def single_list_body() -> subscribable_list_type[int]:
        return [1]

    def multi_list_body() -> subscribable_list_type[int]:
        return [1, 2]

    def multi_dict_body() -> subscribable_dict_type[str, int]:
        return {'first': 1, 'second': 2}

    def docstring_with_annotated_list_body() -> subscribable_list_type[int]:
        """Docstring plus annotated empty list return."""
        return []

    def docstring_with_annotated_dict_body() -> subscribable_dict_type[str, int]:
        """Docstring plus annotated empty dict return."""
        return {}

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for body_function, expected_result in (
        (unannotated_list_body, None),
        (unannotated_dict_body, None),
        (bare_return_body, None),
        (none_return_body, None),
        (scalar_body, None),
        (single_list_body, [1]),
        (multi_list_body, [1, 2]),
        (multi_dict_body, {'first': 1, 'second': 2}),
        (docstring_with_annotated_list_body, []),
        (docstring_with_annotated_dict_body, {}),
    ):
        slot = public_slot(body_function)
        resolved_selection = slot.one

        assert isinstance(resolved_selection, CallerWithPlugins)
        assert bool(resolved_selection)
        assert len(resolved_selection) == 0
        assert resolved_selection() == expected_result


def test_slot_one_prefers_single_plugin_over_non_empty_fallback_body(monkeypatch, subscribable_list_type):
    """A singleton plugin resolves alone even when the slot body is non-empty."""
    @public_slot
    def fallback_body() -> subscribable_list_type[str]:
        return ['fallback']

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = fallback_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return 'plugin'

    assert slot.one() == ['plugin']


def test_slot_one_plugin_count_resolution_skips_fallback_body():
    """Plugin-count resolution skips fallback-body inspection and execution."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def default_body():
        raise AssertionError('default body was executed')

    for plugin_count in (1, 2):
        slot = public_slot(default_body, name='default_body')

        for index in range(plugin_count):
            @slot.plugin(f'plugin_{index}')
            def plugin():
                return None

        slot.caller.code_representation = BrokenCodeRepresentation()
        slot._load_entrypoints = lambda: None  # type: ignore[method-assign]

        if plugin_count == 1:
            assert len(slot.one) == 1
        else:
            with pytest.raises(OneResolutionError, match=match('Slot "default_body" has 2 registered plugins, so .one cannot choose one.')):
                _ = slot.one


def test_one_property_access_does_not_execute_plugin_or_fallback_body(monkeypatch):
    """Reading `.one` resolves candidates without running plugins or fallback bodies."""
    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    fallback_events = []

    @public_slot
    def fallback_body():
        fallback_events.append('fallback-called')

    fallback_slot = fallback_body
    fallback_selection = fallback_slot.one

    assert not fallback_events
    fallback_selection()
    assert fallback_events == ['fallback-called']

    plugin_events = []

    @public_slot
    def empty_body():
        pass

    plugin_slot = empty_body

    @plugin_slot.plugin('plugin')
    def plugin():
        plugin_events.append('plugin-called')

    plugin_selection = plugin_slot.one

    assert not plugin_events
    plugin_selection()
    assert plugin_events == ['plugin-called']

    multiple_events = []
    @public_slot(name='multiple_slot')
    def multiple_body():
        pass

    multiple_slot = multiple_body

    @multiple_slot.plugin('first')
    def first():
        multiple_events.append('first-called')

    @multiple_slot.plugin('second')
    def second():
        multiple_events.append('second-called')

    with pytest.raises(OneResolutionError, match=match('Slot "multiple_slot" has 2 registered plugins, so .one cannot choose one.')):
        _ = multiple_slot.one

    assert not multiple_events


def test_slot_one_propagates_body_inspection_errors_without_plugins(monkeypatch):
    """With no plugins, `.one` propagates body inspection errors after loading."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    @public_slot
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    slot.caller.code_representation = BrokenCodeRepresentation()
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        _ = slot.one

    assert slot.loaded


def test_one_result_type_checks_happen_on_call_for_plugins_and_fallback(monkeypatch, subscribable_list_type):
    """Plugin and fallback result checks happen when the resolved selection is called."""
    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @public_slot
    def empty_body() -> subscribable_list_type[str]:
        return []

    plugin_slot = empty_body

    @plugin_slot.plugin('plugin')  # type: ignore[arg-type]
    def plugin() -> str:
        return 1  # type: ignore[return-value]

    plugin_selection = plugin_slot.one

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "plugin" return value 1 does not match the expected type str.')):
        plugin_selection()

    @public_slot(name='fallback_body')
    def fallback_body() -> subscribable_list_type[str]:
        """Force the annotated fallback body to be non-empty."""
        return [1]  # type: ignore[list-item]

    fallback_slot = fallback_body
    fallback_selection = fallback_slot.one
    fallback_expected_type = List[fallback_selection.caller.code_representation.returning_type]
    fallback_expected_type_name = getattr(fallback_expected_type, '__name__', str(fallback_expected_type))

    with pytest.raises(TypeError, match=match(f'The type list of the plugin\'s "fallback_body" return value [1] does not match the expected type {fallback_expected_type_name}.')):
        fallback_selection()


def test_slot_one_preserves_run_once_plugin_state(monkeypatch, subscribable_list_type):
    """`Slot.one` snapshots share plugin objects, so run-once state is preserved."""
    @public_slot
    def empty_body() -> subscribable_list_type[int]:
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin', run_once=True)
    def plugin():
        return 1

    assert slot.one() == [1]

    with pytest.raises(NumberOfCallsError, match=match('A limit of 1 has been set on the number of calls for plugin "plugin". And this plugin has already been called previously.')):
        slot.one()


def test_slot_one_returns_independent_snapshots_with_shared_plugins(monkeypatch):
    """`Slot.one` returns independent snapshots that share plugin objects."""
    @public_slot(name='empty_body')
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('first')
    def first():
        return None

    first_snapshot = slot.one
    second_snapshot = slot.one

    assert first_snapshot is not second_snapshot
    assert first_snapshot.plugins is not second_snapshot.plugins
    assert first_snapshot.plugins[0] is second_snapshot.plugins[0]

    @slot.plugin('second')
    def second():
        return None

    for snapshot in (first_snapshot, second_snapshot):
        assert len(snapshot) == 1
        assert [plugin.name for plugin in snapshot] == ['first']

    with pytest.raises(OneResolutionError, match=match('Slot "empty_body" has 2 registered plugins, so .one cannot choose one.')):
        _ = slot.one


def test_duplicate_plugin_selection_keys_and_pop_resolve_through_one(monkeypatch, subscribable_list_type):
    """Duplicate numbered keys and exact-key pops resolve through `.one`.

    Base-name lookup remains ambiguous; pop renumbers survivors.
    """
    @public_slot
    def empty_body() -> subscribable_list_type[int]:
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('name')
    def first():
        return 1

    @slot.plugin('name')
    def second():
        return 2

    @slot.plugin('name')
    def third():
        return 3

    for key, expected_result in (('name-1', [1]), ('name-2', [2]), ('name-3', [3])):
        assert slot[key].one() == expected_result

    with pytest.raises(OneResolutionError, match=match('Selection from slot "empty_body" has 3 selected plugins, so .one cannot choose one.')):
        _ = slot['name'].one

    popped_selection = slot.pop('name-2')

    assert popped_selection.one() == [2]
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name', 'name-2']
    for key, expected_result in (('name-1', [1]), ('name-2', [3])):
        assert slot[key].one() == expected_result


def test_popped_group_one_resolution_error_happens_after_parent_mutation(monkeypatch):
    """A popped multi-plugin selection raises OneResolutionError after parent mutation."""
    @public_slot
    def empty_body() -> List[int]:
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = empty_body
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('name')
    def first():
        return 1

    @slot.plugin('name')
    def second():
        return 2

    popped_selection = slot.pop('name')

    assert len(slot) == 0
    assert [plugin.name for plugin in popped_selection] == ['name', 'name-2']
    with pytest.raises(OneResolutionError, match=match('Selection from slot "empty_body" has 2 selected plugins, so .one cannot choose one.')):
        _ = popped_selection.one


@pytest.mark.parametrize('operation_name', ['bool', 'call', 'iter', 'keys', 'getitem', 'delitem', 'pop', 'pop-default', 'one'])
@pytest.mark.parametrize('provider_name', ['provider-call', 'provider-iteration', 'point-load-runtime', 'point-load-key-error'])
def test_entrypoint_loading_errors_are_wrapped_for_lazy_operation_matrix(monkeypatch, operation_name, provider_name):
    """Lazy operations, including `.one`, wrap external entry point failures with their original cause."""
    class FakeEntryPoint:
        def __init__(self, exception):
            self.exception = exception

        def load(self):
            raise self.exception

    class BrokenIterable:
        def __init__(self, exception):
            self.exception = exception

        def __iter__(self):
            raise self.exception

    def empty_body():
        pass

    def delete_missing_item(slot):
        del slot['missing']

    def make_provider_call_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            raise cause

        return get_entries

    def make_provider_iteration_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return BrokenIterable(cause)

        return get_entries

    def make_point_load_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return [FakeEntryPoint(cause)]

        return get_entries

    operations = {
        'bool': bool,
        'call': lambda slot: slot(),
        'iter': list,
        'keys': lambda slot: slot.keys(),
        'getitem': lambda slot: slot['missing'],
        'delitem': delete_missing_item,
        'pop': lambda slot: slot.pop('missing'),
        'pop-default': lambda slot: slot.pop('missing', None),
        'one': lambda slot: slot.one,
    }
    provider_cases = {
        'provider-call': (make_provider_call_failure, KeyError('provider')),
        'provider-iteration': (make_provider_iteration_failure, KeyError('iteration')),
        'point-load-runtime': (make_point_load_failure, RuntimeError('load')),
        'point-load-key-error': (make_point_load_failure, KeyError('broken import')),
    }
    provider_factory, cause = provider_cases[provider_name]
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', provider_factory(cause))

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        operations[operation_name](slot)

    assert exception_info.value.__cause__ is cause
    assert not slot.loaded


@pytest.mark.parametrize('provider_name', ['provider-call', 'provider-iteration', 'point-load'])
@pytest.mark.parametrize('cause_name', ['primadonna', 'inner-wrapper', 'custom'])
def test_pristan_errors_from_entrypoint_loading_stages_are_not_wrapped(monkeypatch, provider_name, cause_name):
    """Pristan exceptions from provider, iteration, or `point.load` pass through unwrapped."""
    class FakeEntryPoint:
        def __init__(self, exception):
            self.exception = exception

        def load(self):
            raise self.exception

    class BrokenIterable:
        def __init__(self, exception):
            self.exception = exception

        def __iter__(self):
            raise self.exception

    class CustomPristanError(PristanException):
        pass

    def empty_body():
        pass

    def make_provider_call_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            raise cause

        return get_entries

    def make_provider_iteration_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return BrokenIterable(cause)

        return get_entries

    def make_point_load_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return [FakeEntryPoint(cause)]

        return get_entries

    provider_factories = {
        'provider-call': make_provider_call_failure,
        'provider-iteration': make_provider_iteration_failure,
        'point-load': make_point_load_failure,
    }
    causes = {
        'primadonna': PrimadonnaPluginError('duplicate plugin'),
        'inner-wrapper': EntrypointLoadingError('inner wrapper'),
        'custom': CustomPristanError('future internal error'),
    }
    cause = causes[cause_name]
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', provider_factories[provider_name](cause))

    with pytest.raises(type(cause), match=match(str(cause))) as exception_info:
        bool(slot)

    assert exception_info.value is cause
    assert not slot.loaded


@pytest.mark.parametrize('operation_name', ['bool', 'call', 'iter', 'keys', 'getitem', 'delitem', 'pop', 'pop-default', 'one'])
@pytest.mark.parametrize('provider_name', ['provider-call', 'provider-iteration', 'point-load'])
@pytest.mark.parametrize('cause_name', ['base-pristan', 'one-resolution'])
def test_pristan_errors_from_entrypoint_loading_are_not_wrapped_for_lazy_operation_matrix(monkeypatch, operation_name, provider_name, cause_name):
    """Lazy public operations, including defaulted pop and `.one`, pass through Pristan exceptions across loading stages."""
    class FakeEntryPoint:
        def __init__(self, exception):
            self.exception = exception

        def load(self):
            raise self.exception

    class BrokenIterable:
        def __init__(self, exception):
            self.exception = exception

        def __iter__(self):
            raise self.exception

    def empty_body():
        pass

    def delete_missing_item(slot):
        del slot['missing']

    def make_provider_call_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            raise cause

        return get_entries

    def make_provider_iteration_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return BrokenIterable(cause)

        return get_entries

    def make_point_load_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return [FakeEntryPoint(cause)]

        return get_entries

    operations = {
        'bool': bool,
        'call': lambda slot: slot(),
        'iter': list,
        'keys': lambda slot: slot.keys(),
        'getitem': lambda slot: slot['missing'],
        'delitem': delete_missing_item,
        'pop': lambda slot: slot.pop('missing'),
        'pop-default': lambda slot: slot.pop('missing', None),
        'one': lambda slot: slot.one,
    }
    provider_cases = {
        'provider-call': make_provider_call_failure,
        'provider-iteration': make_provider_iteration_failure,
        'point-load': make_point_load_failure,
    }
    causes = {
        'base-pristan': PristanException('provider'),
        'one-resolution': OneResolutionError('provider one resolution'),
    }
    cause = causes[cause_name]
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', provider_cases[provider_name](cause))

    with pytest.raises(type(cause), match=match(str(cause))) as exception_info:
        operations[operation_name](slot)

    assert exception_info.value is cause
    assert not slot.loaded


def test_slot_one_signature_mismatch_during_entrypoint_load_is_wrapped(monkeypatch):
    """`Slot.one` wraps signature mismatches raised by entry point registration."""
    class FakeEntryPoint:
        def load(self):
            @slot.plugin('bad')
            def bad_plugin():
                return None

    @public_slot
    def empty_body(value):
        pass

    slot = empty_body

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        _ = slot.one

    assert isinstance(exception_info.value.__cause__, SignatureMismatchError)
    assert not slot.loaded
    assert len(slot.plugins.plugins) == 0


def test_slot_one_unique_registration_error_during_entrypoint_load_passes_through(monkeypatch):
    """`Slot.one` passes through unique-name errors after partial registration."""
    @public_slot(unique=True)
    def empty_body():
        pass

    slot = empty_body

    class FakeEntryPoint:
        def load(self):
            @slot.plugin('name')
            def first_plugin():
                return None

            @slot.plugin('name')
            def second_plugin():
                return None

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(PrimadonnaPluginError, match=match('Slot "empty_body" requires unique plugin names, but "name" is already registered.')):
        _ = slot.one

    assert not slot.loaded
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name']


def test_slot_one_explicit_name_registration_error_during_entrypoint_load_passes_through(monkeypatch):
    """`Slot.one` passes through explicit-name errors without adding plugins."""
    @public_slot(explicit_plugin_names=True)
    def empty_body():
        pass

    slot = empty_body

    class FakeEntryPoint:
        def load(self):
            @slot.plugin
            def plugin():
                return None

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(ExplicitNameRequiredError, match=match('Slot "empty_body" requires explicit plugin names.')):
        _ = slot.one

    assert not slot.loaded
    assert len(slot.plugins.plugins) == 0


def test_slot_one_engine_version_error_during_entrypoint_load_passes_through(monkeypatch):
    """`Slot.one` passes through engine version-discovery errors without adding plugins."""
    @public_slot
    def empty_body():
        pass

    slot = empty_body

    class FakeEntryPoint:
        def load(self):
            @slot.plugin('plugin', engine='>1000.0.0')
            def plugin():
                return None

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(CannotGetVersionsError, match=match('It is not possible to obtain the name of the package in which the slot is declared.')):
        _ = slot.one

    assert not slot.loaded
    assert len(slot.plugins.plugins) == 0


def test_registration_error_during_entrypoint_loading_is_not_wrapped(monkeypatch):
    """Registration failures raised inside point.load remain direct Pristan errors."""
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=True)
    captured_exceptions = []

    def register_duplicates():
        @slot.plugin('name')
        def first_plugin():
            return None

        try:
            @slot.plugin('name')
            def second_plugin():
                return None
        except PrimadonnaPluginError as exception:
            captured_exceptions.append(exception)
            raise

    class FakeEntryPoint:
        def load(self):
            register_duplicates()

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(PrimadonnaPluginError) as exception_info:
        bool(slot)

    assert exception_info.value is captured_exceptions[0]
    assert not slot.loaded
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name']


def test_explicit_plugin_names_error_during_entrypoint_loading_is_not_wrapped(monkeypatch):
    """Strict plugin-name failures raised inside point.load remain direct Pristan errors."""
    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False, explicit_plugin_names=True)
    captured_exceptions = []

    def register_inferred_name():
        try:
            @slot.plugin
            def plugin():
                return None
        except ExplicitNameRequiredError as exception:
            captured_exceptions.append(exception)
            raise

    class FakeEntryPoint:
        def load(self):
            register_inferred_name()

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(ExplicitNameRequiredError, match=match('Slot "empty_body" requires explicit plugin names.')) as exception_info:
        bool(slot)

    assert exception_info.value is captured_exceptions[0]
    assert not slot.loaded
    assert len(slot.plugins.plugins) == 0


def test_load_failure_then_retry_success_keeps_partial_plugins(monkeypatch):
    """A failed load keeps partial plugins and retries from the provider start.

    Entry point loading does not roll back plugins that registered before a
    later entry point failed. A retry starts discovery again, so the previously
    registered plugin remains and can be duplicated before the retry succeeds.
    """
    class FakeEntryPoint:
        def __init__(self, loader):
            self.loader = loader

        def load(self):
            self.loader()

    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    attempts = []

    def register_name():
        @slot.plugin('name')
        def plugin():
            return None

    def register_other():
        @slot.plugin('other')
        def plugin():
            return None

    def fail_first_load():
        raise RuntimeError('first failure')

    def get_entries(group=None):
        assert group == 'pristan'
        attempts.append('attempt')
        if len(attempts) == 1:
            return [FakeEntryPoint(register_name), FakeEntryPoint(fail_first_load)]
        return [FakeEntryPoint(register_name), FakeEntryPoint(register_other)]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        bool(slot)

    assert isinstance(exception_info.value.__cause__, RuntimeError)
    assert str(exception_info.value.__cause__) == 'first failure'
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name']
    assert not slot.loaded

    assert bool(slot)
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name', 'name-2', 'other']
    assert slot.loaded


def test_stable_load_failure_can_accumulate_partial_duplicates(monkeypatch):
    """Stable failures retry from the start and can duplicate partial plugins.

    The loader intentionally keeps partial state after failed discovery. When
    the same provider fails repeatedly after registering one plugin, each retry
    can add another duplicate before the same load error is raised.
    """
    class FakeEntryPoint:
        def __init__(self, loader):
            self.loader = loader

        def load(self):
            self.loader()

    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    def register_name():
        @slot.plugin('name')
        def plugin():
            return None

    def fail_stable_load():
        raise RuntimeError('stable failure')

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint(register_name), FakeEntryPoint(fail_stable_load)]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for _ in range(2):
        with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
            bool(slot)

        assert isinstance(exception_info.value.__cause__, RuntimeError)
        assert str(exception_info.value.__cause__) == 'stable failure'

    assert [plugin.name for plugin in slot.plugins.plugins] == ['name', 'name-2']
    assert not slot.loaded


@pytest.mark.parametrize('operation_name', ['bool', 'call', 'iter', 'keys', 'getitem', 'delitem', 'pop', 'pop-default', 'one'])
@pytest.mark.parametrize('provider_name', ['provider-call', 'provider-iteration', 'point-load'])
def test_base_exception_from_entrypoint_loading_passes_through(monkeypatch, operation_name, provider_name):
    """BaseException subclasses pass through every lazy loading operation."""
    class CustomBaseException(BaseException):
        pass

    class FakeEntryPoint:
        def __init__(self, exception):
            self.exception = exception

        def load(self):
            raise self.exception

    class BrokenIterable:
        def __init__(self, exception):
            self.exception = exception

        def __iter__(self):
            raise self.exception

    def empty_body():
        pass

    def delete_missing_item(slot):
        del slot['missing']

    def make_provider_call_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            raise cause

        return get_entries

    def make_provider_iteration_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return BrokenIterable(cause)

        return get_entries

    def make_point_load_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return [FakeEntryPoint(cause)]

        return get_entries

    provider_cases = {
        'provider-call': make_provider_call_failure,
        'provider-iteration': make_provider_iteration_failure,
        'point-load': make_point_load_failure,
    }
    operations = {
        'bool': bool,
        'call': lambda slot: slot(),
        'iter': list,
        'keys': lambda slot: slot.keys(),
        'getitem': lambda slot: slot['missing'],
        'delitem': delete_missing_item,
        'pop': lambda slot: slot.pop('missing'),
        'pop-default': lambda slot: slot.pop('missing', None),
        'one': lambda slot: slot.one,
    }
    cause = CustomBaseException(provider_name)
    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', provider_cases[provider_name](cause))

    with pytest.raises(CustomBaseException) as exception_info:
        operations[operation_name](slot)

    assert exception_info.value is cause
    assert not slot.loaded


def test_direct_local_errors_are_not_wrapped(monkeypatch):
    """Errors outside entry point loading keep their original types."""
    def default_body():
        raise ValueError('default failed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    default_slot = Slot(default_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(ValueError, match=match('default failed')):
        default_slot()

    plugin_slot = Slot(default_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    @plugin_slot.plugin
    def plugin():
        raise RuntimeError('plugin failed')

    with pytest.raises(RuntimeError, match=match('plugin failed')):
        plugin_slot()
