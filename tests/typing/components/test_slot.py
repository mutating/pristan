from typing import List

import pytest
from typing_extensions import reveal_type

import pristan.components.slot as slot_module
from pristan.components.slot import Slot


@pytest.mark.mypy_testing
def test_concrete_slot_bool_method_is_typed_as_bool(monkeypatch):
    """The concrete Slot class exposes a typed __bool__ method."""
    def collect() -> list:
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)
    slot_view = Slot(collect, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    reveal_type(slot_view.__bool__())  # R: builtins.bool


@pytest.mark.mypy_testing
def test_concrete_slot_one_is_typed_as_caller_with_plugins(monkeypatch):
    """Concrete `Slot.one` returns `CallerWithPlugins` with the same plugin result generic."""
    def collect() -> List[int]:
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)
    slot_view: Slot[int] = Slot(collect, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    @slot_view.plugin('plugin')
    def plugin() -> int:
        return 1

    reveal_type(slot_view.one)  # R: pristan.components.slot_caller.CallerWithPlugins[builtins.int]
