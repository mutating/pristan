from importlib.metadata import EntryPoint

import pytest
from full_match import match

import pristan.components.slot as slot_module
from pristan.errors import PrimadonnaPluginError
from tests.smokes.demo.simple_slots import (
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


def test_unique_slot_rejects_duplicate_plugins_loaded_from_entrypoints(monkeypatch):
    """Lazy entry point imports apply the unique-slot policy on first resolution.

    Loading the demo plugin module through a real `EntryPoint` registers two
    plugins with the same requested name. The first public slot call must raise
    the slot-level uniqueness error during lazy resolution, after the first
    plugin has been installed and before the duplicate is kept.

    A failed resolution does not mark the slot as loaded, so another public
    call would try to load the same failing entry point again. The test replaces
    entry points with an empty provider before the second call; that call then
    proves through public behavior that only the first plugin participates.
    """
    def get_entries(group=None):  # noqa: ARG001
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_unique_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    try:
        with pytest.raises(PrimadonnaPluginError, match=match('Slot "simple_slot_6" requires unique plugin names, but "name" is already registered.')):
            simple_slot_6()

        monkeypatch.setattr(slot_module, 'entry_points', lambda group=None: [])  # noqa: ARG005

        assert simple_slot_6() == {'name': 1}
    finally:
        simple_slot_6.pop('name', None)
