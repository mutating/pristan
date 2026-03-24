from importlib.metadata import EntryPoint

import pristan.components.slot as slot_module

from tests.smokes.demo.simple_slots import (
    simple_slot_1,
    simple_slot_2,
    simple_slot_3,
    simple_slot_4,
    simple_slot_5,
)


def test_run_simple_slot(monkeypatch):
    def get_entries(group=None):
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}
    assert simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}


def test_run_simple_slot_with_another_name(monkeypatch):
    def get_entries(group=None):
        return [EntryPoint(name='name2', value='tests.smokes.demo.plugins_another_name', group='another_name')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}
    assert simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}


def test_plugins_are_loaded_when_called(monkeypatch):
    def get_entries(group=None):
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_3.loaded

    assert simple_slot_3() == {'name': 1}

    assert simple_slot_3.loaded


def test_plugins_are_loaded_when_keys_readed(monkeypatch):
    def get_entries(group=None):
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_4.loaded

    assert simple_slot_4.keys() == ('name',)

    assert simple_slot_4.loaded


def test_plugins_are_loaded_when_getitem(monkeypatch):
    def get_entries(group=None):
        return [EntryPoint(name='name', value='tests.smokes.demo.simple_plugins', group='pristan')]

    monkeypatch.setattr(slot_module, "entry_points", get_entries)

    assert not simple_slot_5.loaded

    assert len(simple_slot_5['name']) == 1

    assert simple_slot_5.loaded
