from typing import List

import pytest
from typing_extensions import reveal_type

from pristan.components.slot import Slot
from pristan.components.slot_caller import CallerWithPlugins


@pytest.mark.mypy_testing
def test_slot_caller_has_non_empty_default_body_is_bool():
    """The default-body helper is exposed as a boolean property."""
    def collect() -> list:
        return []

    slot = Slot(collect, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    reveal_type(slot.caller.has_non_empty_default_body)  # R: builtins.bool


@pytest.mark.mypy_testing
def test_concrete_caller_with_plugins_one_keeps_selection_type():
    """`CallerWithPlugins.one` returns the same selection type."""
    def collect() -> List[int]:
        return [1]

    slot = Slot(collect, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    selection: CallerWithPlugins[int] = CallerWithPlugins(slot.caller, [])

    reveal_type(selection.one)  # R: pristan.components.slot_caller.CallerWithPlugins[builtins.int]
