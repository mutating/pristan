import pytest
from typing_extensions import reveal_type

from pristan.components.slot_caller import SlotCaller
from pristan.components.slot_code_representer import SlotCodeRepresenter


@pytest.mark.mypy_testing
def test_slot_caller_has_non_empty_default_body_is_bool():
    """The default-body helper is exposed as a boolean property."""
    def collect() -> list:
        return []

    caller = SlotCaller(SlotCodeRepresenter(collect), 'collect', collect, True)

    reveal_type(caller.has_non_empty_default_body)  # R: builtins.bool
