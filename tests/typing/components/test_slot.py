import pytest
from typing_extensions import reveal_type

from pristan.components.slot import Slot


@pytest.mark.mypy_testing
def test_concrete_slot_bool_method_is_typed_as_bool():
    """The concrete Slot class exposes a typed __bool__ method."""
    def collect() -> list:
        return []

    slot_view = Slot(collect, None, None, None, True, 'pristan', False)

    reveal_type(slot_view.__bool__())  # R: builtins.bool
