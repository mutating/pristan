import pytest
from full_match import match
from sigmatch.errors import SignatureMismatchError

from pristan import slot
from pristan.decorators.slot import Slot


def test_slot_is_not_a_function():
    @slot
    def some_slot():
        ...

    @slot()
    def some_slot_2():
        ...

    assert isinstance(some_slot, Slot)
    assert isinstance(some_slot_2, Slot)


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


@pytest.mark.parametrize(
    ('folder'),
    [
        lambda x: x,
        lambda x: x(),
    ]
)
def test_run_1_plugin_without_hints(folder):
    bread_crumbs = []

    @folder(slot)
    def some_slot(a, b):
        bread_crumbs.append(a + b)

    @some_slot.plugin('name')
    def some_plugin(a, b):
        bread_crumbs.append(a + b + 1)

    assert some_slot(1, 2) is None

    assert bread_crumbs == [4]


@pytest.mark.parametrize(
    ('folder'),
    [
        lambda x: x,
        lambda x: x(),
    ]
)
def test_run_1_plugin_with_emplty_list_hint(folder, list_type):
    bread_crumbs = []

    @folder(slot)
    def some_slot(a, b) -> list_type:
        bread_crumbs.append(a + b)

    @some_slot.plugin('name')
    def some_plugin(a, b):
        bread_crumbs.append(a + b + 1)
        return a + b + 2

    assert some_slot(1, 2) == [5]

    assert bread_crumbs == [4]
