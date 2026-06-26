from importlib.metadata import EntryPoint

import pytest
from full_match import match

import pristan.components.slot as slot_module
from pristan import slot
from pristan.errors import (
    EntrypointLoadingError,
    ExplicitNameRequiredError,
    PrimadonnaPluginError,
)
from tests.smokes.demo.simple_slots import (
    simple_bool_slot,
    simple_contains_slot,
    simple_custom_one_slot,
    simple_explicit_plugin_names_slot,
    simple_len_slot,
    simple_one_slot,
    simple_slot_1,
    simple_slot_2,
    simple_slot_3,
    simple_slot_4,
    simple_slot_5,
    simple_slot_6,
)


def test_run_simple_slot(monkeypatch):
    """Calling a slot loads its plugins from the default entry point group."""
    def get_entries(group=None):
        assert group == 'pristan'
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}
    assert simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}


def test_run_simple_slot_with_another_name(monkeypatch):
    """Calling a slot respects its custom entry point group."""
    def get_entries(group=None):
        assert group == 'another_name'
        return [EntryPoint(name='name2', value='tests.smokes.demo.plugins_another_name', group='another_name')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}
    assert simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}


def test_plugins_are_loaded_when_called(monkeypatch):
    """A slot call triggers lazy entry point loading."""
    def get_entries(group=None):
        assert group == 'pristan'
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_call_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_slot_3.loaded

    assert simple_slot_3() == {'name': 1}

    assert simple_slot_3.loaded


def test_plugins_are_loaded_when_keys_are_read(monkeypatch):
    """Reading keys triggers lazy entry point loading."""
    def get_entries(group=None):
        assert group == 'pristan'
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_keys_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_slot_4.loaded

    assert simple_slot_4.keys() == ('name',)

    assert simple_slot_4.loaded


def test_getitem_loads_plugins_from_real_entrypoint(monkeypatch):
    """Getting a selection triggers lazy entry point loading."""
    def get_entries(group=None):
        assert group == 'pristan'
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_getitem_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_slot_5.loaded

    assert len(simple_slot_5['name']) == 1

    assert simple_slot_5.loaded


def test_bool_loads_plugins_from_real_entrypoint_once(monkeypatch):
    """Bool loads a real EntryPoint once and reuses the plugin.

    `EntryPoint.load()` imports a demo module that registers against a global
    slot, keeping this a real module-loading smoke test.
    """
    requested_groups = []

    def get_entries(group=None):
        requested_groups.append(group)
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_bool_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(simple_bool_slot)
    assert simple_bool_slot.loaded
    assert [plugin.name for plugin in simple_bool_slot.plugins.plugins] == ['name']

    assert bool(simple_bool_slot)
    assert requested_groups == ['pristan']


def test_slot_one_loads_plugin_from_real_entrypoint_and_calls_result(monkeypatch):
    """`Slot.one` loads a real entry point once and returns a callable selection."""
    requested_groups = []

    def get_entries(group=None):
        requested_groups.append(group)
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_one_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_one_slot.loaded
    assert simple_one_slot.one() == {'name': 7}
    assert simple_one_slot.loaded

    assert simple_one_slot.one() == {'name': 7}
    assert requested_groups == ['pristan']


def test_len_loads_plugins_from_real_entrypoint(monkeypatch):
    """Length loads a real entry point once and counts the registered plugin."""
    requested_groups = []

    def get_entries(group=None):
        requested_groups.append(group)
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_len_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_len_slot.loaded
    assert len(simple_len_slot) == 1
    assert simple_len_slot.loaded
    assert [plugin.name for plugin in simple_len_slot.plugins.plugins] == ['name']

    assert len(simple_len_slot) == 1
    assert simple_len_slot() == {'name': 9}
    assert requested_groups == ['pristan']


def test_contains_loads_plugins_from_real_entrypoint(monkeypatch):
    """Membership checks load a real entry point once and inspect the registered plugin."""
    requested_groups = []

    def get_entries(group=None):
        requested_groups.append(group)
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_contains_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_contains_slot.loaded
    assert 'name' in simple_contains_slot
    assert simple_contains_slot.loaded
    assert [plugin.name for plugin in simple_contains_slot.plugins.plugins] == ['name']

    assert 'name' in simple_contains_slot
    assert simple_contains_slot() == {'name': 10}
    assert requested_groups == ['pristan']


def test_slot_one_loads_plugin_from_custom_entrypoint_group(monkeypatch):
    """`Slot.one` loads a custom-group entry point once into a callable selection."""
    requested_groups = []

    def get_entries(group=None):
        requested_groups.append(group)
        return [EntryPoint(name='name2', value='tests.smokes.demo.simple_custom_one_plugins', group='another_name')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not simple_custom_one_slot.loaded
    assert simple_custom_one_slot.one() == {'name2': 8}
    assert simple_custom_one_slot.loaded

    assert simple_custom_one_slot.one() == {'name2': 8}
    assert requested_groups == ['another_name']


def test_broken_import_from_entrypoint_is_wrapped(monkeypatch):
    """A real import failure is exposed as EntrypointLoadingError with cause.

    The broken module lives in the demo package and is imported through a real
    `EntryPoint`. The slot itself is local because the failing module never
    needs to register a plugin against it.
    """
    @slot
    def target_slot():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return [
            EntryPoint(
                name='broken',
                value='tests.smokes.demo.broken_import_plugin',
                group='pristan',
            ),
        ]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        bool(target_slot)

    assert isinstance(exception_info.value.__cause__, KeyError)
    assert exception_info.value.__cause__.args == ('broken import',)
    assert not target_slot.loaded


def test_unique_slot_rejects_duplicate_plugins_loaded_from_entrypoints(monkeypatch):
    """Lazy entry point registration errors keep their Pristan exception type.

    The real demo module registers duplicate requested names during
    `point.load()`, so the Pristan error passes through directly. A second call
    with no entry points proves the plugin registered before the failure remains
    usable.
    """
    def get_entries(group=None):
        assert group == 'pristan'
        return [
            EntryPoint(
                name='name',
                value='tests.smokes.demo.simple_unique_plugins',
                group='pristan',
            ),
        ]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(PrimadonnaPluginError, match=match('Slot "simple_slot_6" requires unique plugin names, but "name" is already registered.')):
        simple_slot_6()

    assert not simple_slot_6.loaded

    def get_empty_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_empty_entries)

    assert simple_slot_6() == {'name': 1}
    assert simple_slot_6.loaded


def test_explicit_plugin_names_rejects_inferred_name_loaded_from_entrypoint(monkeypatch):
    """A real EntryPoint preserves strict plugin-name registration errors."""
    def get_entries(group=None):
        assert group == 'pristan'
        return [
            EntryPoint(
                name='entrypoint_name',
                value='tests.smokes.demo.simple_explicit_plugin_names_plugins',
                group='pristan',
            ),
        ]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(ExplicitNameRequiredError, match=match('Slot "simple_explicit_plugin_names_slot" requires explicit plugin names.')):
        simple_explicit_plugin_names_slot()

    assert not simple_explicit_plugin_names_slot.loaded
    assert simple_explicit_plugin_names_slot.plugins.plugins == []
