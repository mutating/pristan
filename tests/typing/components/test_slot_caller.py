from typing import List

import pytest
from full_match import match
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
    """
    `CallerWithPlugins.one` returns the same selection type.

    Catching the warning keeps this check on a non-unique slot; changing it to
    unique=True would bias coverage, while leaving it uncaught would add warning noise.
    """
    def collect() -> List[int]:
        return [1]

    slot = Slot(collect, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    selection: CallerWithPlugins[int] = CallerWithPlugins(slot.caller, [])

    with pytest.warns(SyntaxWarning, match=match('Consider setting unique=True for slot "collect", because this code uses .one to work with a single plugin.')):
        reveal_type(selection.one)  # R: pristan.components.slot_caller.CallerWithPlugins[builtins.int]
