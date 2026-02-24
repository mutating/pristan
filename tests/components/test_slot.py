import pytest
from full_match import match

from pristan.components.slot import Slot


def test_set_max_less_than_zero():
    with pytest.raises(ValueError, match=match('The maximum number of plugins cannot be less than zero.')):
        Slot(lambda x: x, '.', 'slot_name', -1, False)
