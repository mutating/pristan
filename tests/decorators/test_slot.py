import pytest
from full_match import match
from sigmatch.errors import SignatureMismatchError

from symplug import slot
from symplug.decorators.slot import Slot


def test_slot_is_not_a_function():
    @slot
    def some_slot():
        ...

    @slot()
    def some_slot_2():
        ...

    assert isinstance(some_slot, Slot)
    assert isinstance(some_slot_2, Slot)


def test_i_can_call_slot():
    side_effects = []

    @slot
    def some_slot():
        side_effects.append(1)
        return 2

    @slot()
    def some_slot_2():
        side_effects.append(3)
        return 4

    @slot
    def some_slot_3(a, b=4):
        side_effects.append(5)
        return a + b

    @slot()
    def some_slot_4(a, b=4):
        side_effects.append(6)
        return a + b

    assert some_slot() == 2
    assert some_slot_2() == 4
    assert some_slot_3(2) == 6
    assert some_slot_3(3) == 7
    assert some_slot_3(3, b=5) == 8

    assert some_slot_4(2) == 6
    assert some_slot_4(3) == 7
    assert some_slot_4(3, b=5) == 8

    assert side_effects == [1, 3, 5, 5, 5, 6, 6, 6]


def test_slot_have_not_comparing_signature_with_itself():
    with pytest.raises(SignatureMismatchError, match=match('The signature of the callable object does not match the expected one.')):
        @slot(signature='..')
        def some_slot():
            ...


def test_plugin_have_not_comparing_signature_to_passed_one_to_slot():
    @slot(signature='..')
    def some_slot(a, b):
        ...

    with pytest.raises(SignatureMismatchError, match=match('The signature of the callable object does not match the expected one.')):
        @some_slot.plugin('name')
        def plugin():
            ...


@pytest.mark.parametrize(
    ('folder'),
    [
        lambda x: x,
        lambda x: x(),
    ]
)
def test_plugin_have_not_comparing_signature_to_slot(folder):
    @folder(slot)
    def some_slot(a, b):
        ...

    with pytest.raises(SignatureMismatchError, match=match('No common calling method has been found between the slot and the plugin.')):
        @some_slot.plugin('name')
        def plugin():
            ...
