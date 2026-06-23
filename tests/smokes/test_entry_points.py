import sys
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
    simple_explicit_plugin_names_slot,
    simple_slot_1,
    simple_slot_2,
    simple_slot_3,
    simple_slot_4,
    simple_slot_5,
    simple_slot_6,
)


def test_run_simple_slot(monkeypatch):
    def get_entries(group=None):  # noqa: ARG001
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}
    assert simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}


def test_run_simple_slot_with_another_name(monkeypatch):
    def get_entries(group=None):  # noqa: ARG001
        return [EntryPoint(name='name2', value='tests.smokes.demo.plugins_another_name', group='another_name')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}
    assert simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}


def test_plugins_are_loaded_when_called(monkeypatch):
    def get_entries(group=None):  # noqa: ARG001
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_3.loaded

    assert simple_slot_3() == {'name': 1}

    assert simple_slot_3.loaded


def test_plugins_are_loaded_when_keys_readed(monkeypatch):
    def get_entries(group=None):  # noqa: ARG001
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_4.loaded

    assert simple_slot_4.keys() == ('name',)

    assert simple_slot_4.loaded


def test_plugins_are_loaded_when_getitem(monkeypatch):
    def get_entries(group=None):  # noqa: ARG001
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_5.loaded

    assert len(simple_slot_5['name']) == 1

    assert simple_slot_5.loaded


def test_bool_loads_plugins_from_real_entrypoint_once(monkeypatch):
    """Bool resolves a real EntryPoint and does not import it again after success.

    The plugin lives in the demo package and is imported through
    `EntryPoint.load()`, so this stays a real module-loading smoke test. The
    global demo slot is necessary here because plugin registration happens as a
    module import side effect.
    """
    calls = []
    module_name = 'tests.smokes.demo.simple_bool_plugins'

    def get_entries(group=None):
        calls.append(group)
        return [
            EntryPoint(
                name='name',
                value=module_name,
                group='pristan',
            ),
        ]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    simple_bool_slot.plugins.plugins.clear()
    simple_bool_slot.plugins.plugins_by_requested_names.clear()
    simple_bool_slot.loaded = False
    sys.modules.pop(module_name, None)

    try:
        assert bool(simple_bool_slot)
        assert simple_bool_slot.loaded
        assert [plugin.name for plugin in simple_bool_slot.plugins.plugins] == ['name']

        assert bool(simple_bool_slot)
        assert calls == ['pristan']
    finally:
        simple_bool_slot.plugins.plugins.clear()
        simple_bool_slot.plugins.plugins_by_requested_names.clear()
        simple_bool_slot.loaded = False
        sys.modules.pop(module_name, None)


def test_broken_import_from_entrypoint_is_wrapped(monkeypatch):
    """A real import failure is exposed as EntrypointLoadingError with cause.

    The broken module lives in the demo package and is imported through a real
    `EntryPoint`. The slot itself is local because the failing module never
    needs to register a plugin against it.
    """
    @slot
    def target_slot():
        pass

    def get_entries(group=None):  # noqa: ARG001
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

    Loading the demo plugin module through a real `EntryPoint` registers two
    plugins with the same requested name. The duplicate registration happens in
    Pristan code during `point.load()`, so it must pass through directly
    instead of being converted to an external-loading wrapper.

    After that failure, replacing entry points with an empty provider lets the
    next public call prove that the first plugin registered before the failure
    remains installed and usable.
    """
    module_name = 'tests.smokes.demo.simple_unique_plugins'

    def get_entries(group=None):  # noqa: ARG001
        return [
            EntryPoint(
                name='name',
                value=module_name,
                group='pristan',
            ),
        ]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    simple_slot_6.plugins.plugins.clear()
    simple_slot_6.plugins.plugins_by_requested_names.clear()
    simple_slot_6.loaded = False
    sys.modules.pop(module_name, None)

    try:
        with pytest.raises(PrimadonnaPluginError, match=match('Slot "simple_slot_6" requires unique plugin names, but "name" is already registered.')):
            simple_slot_6()

        assert not simple_slot_6.loaded

        monkeypatch.setattr(slot_module, 'entry_points', lambda group=None: [])  # noqa: ARG005

        assert simple_slot_6() == {'name': 1}
        assert simple_slot_6.loaded
    finally:
        simple_slot_6.plugins.plugins.clear()
        simple_slot_6.plugins.plugins_by_requested_names.clear()
        simple_slot_6.loaded = False
        sys.modules.pop(module_name, None)


def test_explicit_plugin_names_rejects_inferred_name_loaded_from_entrypoint(monkeypatch):
    """A real EntryPoint preserves strict plugin-name registration errors."""
    module_name = 'tests.smokes.demo.simple_explicit_plugin_names_plugins'

    def get_entries(group=None):  # noqa: ARG001
        return [
            EntryPoint(
                name='entrypoint_name',
                value=module_name,
                group='pristan',
            ),
        ]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    def reset_slot():
        simple_explicit_plugin_names_slot.plugins.plugins.clear()
        simple_explicit_plugin_names_slot.plugins.plugins_by_requested_names.clear()
        simple_explicit_plugin_names_slot.loaded = False
        sys.modules.pop(module_name, None)

    reset_slot()

    try:
        with pytest.raises(ExplicitNameRequiredError, match=match('Slot "simple_explicit_plugin_names_slot" requires explicit plugin names.')):
            simple_explicit_plugin_names_slot()

        assert not simple_explicit_plugin_names_slot.loaded
        assert len(simple_explicit_plugin_names_slot) == 0
    finally:
        reset_slot()
