from typing import List

import pytest
from typing_extensions import reveal_type

from pristan.components.slot_caller import CallerWithPlugins, SlotCaller
from pristan.components.slot_code_representer import SlotCodeRepresenter


@pytest.mark.mypy_testing
def test_slot_caller_has_non_empty_default_body_is_bool():
    """The default-body helper is exposed as a boolean property."""
    def collect() -> list:
        return []

    caller = SlotCaller(SlotCodeRepresenter(collect), 'collect', collect, True)

    reveal_type(caller.has_non_empty_default_body)  # R: builtins.bool


@pytest.mark.mypy_testing
def test_concrete_caller_with_plugins_one_keeps_selection_type():
    """`CallerWithPlugins.one` returns the same selection type."""
    def collect() -> List[int]:
        return [1]

    caller = SlotCaller(SlotCodeRepresenter(collect), 'collect', collect, True)
    selection: CallerWithPlugins[int] = CallerWithPlugins(caller, [])

    reveal_type(selection.one)  # R: pristan.components.slot_caller.CallerWithPlugins[builtins.int]
