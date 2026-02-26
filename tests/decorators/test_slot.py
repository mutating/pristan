import pytest
from full_match import match
from sigmatch.errors import SignatureMismatchError

from pristan import slot
from pristan.decorators.slot import Slot
from pristan.errors import (
    PrimadonnaPluginError,
    StrangeTypeAnnotationError,
    TooManyPluginsError,
)


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


def test_plugin_have_not_comparing_signature_to_slot(folder):
    @folder(slot)
    def some_slot(a, b):
        ...

    with pytest.raises(SignatureMismatchError, match=match('No common calling method has been found between the slot and the plugin.')):
        @some_slot.plugin('name')
        def plugin():
            ...


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


def test_2_not_unique_plugins_with_same_names(folder):
    @folder(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('kek')
    def plugin_1(a, b):
        ...

    @some_slot.plugin('kek')
    def plugin_2(a, b):
        ...

    @some_slot.plugin('kek')
    def plugin_3(a, b):
        ...

    assert [x.name for x in some_slot.plugins] == ['kek', 'kek-2', 'kek-3']
    assert [x.name for x in some_slot.plugins_by_requested_names['kek']] == ['kek', 'kek-2', 'kek-3']


def test_2_plugins_with_same_names_and_first_one_is_unique(folder):
    @folder(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('kek', unique=True)
    def plugin_1(a, b):
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Plugin "kek" claims to be unique, but there are other plugins with the same name.')):
        @some_slot.plugin('kek')
        def plugin_2(a, b):
            ...

    assert [x.name for x in some_slot.plugins] == ['kek']
    assert [x.name for x in some_slot.plugins_by_requested_names['kek']] == ['kek']


def test_2_plugins_with_same_names_and_second_one_is_unique(folder):
    @folder(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('kek')
    def plugin_1(a, b):
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Plugin "kek-2" claims to be unique, but there are other plugins with the same name.')):
        @some_slot.plugin('kek', unique=True)
        def plugin_2(a, b):
            ...

    assert [x.name for x in some_slot.plugins] == ['kek']
    assert [x.name for x in some_slot.plugins_by_requested_names['kek']] == ['kek']


def test_exceeding_the_limit_0_of_plugins():
    @slot(max_plugins=0)
    def some_slot(a, b):
        ...

    with pytest.raises(TooManyPluginsError, match=match('The maximum number of plugins for this slot is 0.')):
        @some_slot.plugin('kek')
        def kek(a, b):
            ...


def test_exceeding_the_limit_1_of_plugins():
    @slot(max_plugins=1)
    def some_slot(a, b):
        ...

    @some_slot.plugin('kek')
    def kek(a, b):
        ...

    with pytest.raises(TooManyPluginsError, match=match('The maximum number of plugins for this slot is 1.')):
        @some_slot.plugin('kek2')
        def kek(a, b):
            ...


def test_exceeding_the_limit_1000_of_plugins():
    allowed_number_of_plugins = 1000

    @slot(max_plugins=allowed_number_of_plugins)
    def some_slot(a, b):
        ...

    for index in range(allowed_number_of_plugins):
        @some_slot.plugin(f'kek{index}')
        def kek(a, b):
            ...

    with pytest.raises(TooManyPluginsError, match=match('The maximum number of plugins for this slot is 1000.')):
        @some_slot.plugin('kek')
        def kek(a, b):
            ...


def test_strange_slot_return_type_annotation(folder):
    with pytest.raises(StrangeTypeAnnotationError, match=match('The return type annotation for a slot must be either a list or a dict, or remain empty.')):
        @folder(slot)
        def some_slot(a, b) -> int:
            ...


def test_plugin_name_is_not_valid_python_identifier(folder):
    @folder(slot)
    def some_slot(a, b):
        ...

    with pytest.raises(ValueError, match=match('The plugin name must be a valid Python identifier.')):
        @some_slot.plugin('lol kek')
        def some_plugin(a, b):
            ...


def test_slot_return_type_is_dict_but_keys_are_not_str(folder, subscribable_dict_type):
    with pytest.raises(TypeError, match=match('Incorrect type annotation for the dict.')):
        @folder(slot)
        def some_slot(a, b) -> subscribable_dict_type[int, int]:
            ...


def test_run_slot_with_empty_dict_annotation(folder, dict_type):
    @folder(slot)
    def some_slot(a, b) -> dict_type:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('name2')
    def function_3(a, b):
        return a + b + 3

    assert some_slot(1, 2) == {'name1': 4, 'name2': 5, 'name2-2': 6}


def test_run_slot_with_not_empty_dict_annotation(folder, subscribable_dict_type):
    @folder(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, int]:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('name2')
    def function_3(a, b):
        return a + b + 3

    assert some_slot(1, 2) == {'name1': 4, 'name2': 5, 'name2-2': 6}


def test_run_slot_with_not_empty_wrong_dict_annotation(folder, subscribable_dict_type):
    @folder(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "name1" return value 4 does not match the expected type str.')):
        some_slot(1, 2)


def test_run_slot_with_not_empty_wrong_dict_annotation_but_type_check_is_off(subscribable_dict_type):
    @slot(type_check=False)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('name2')
    def function_3(a, b):
        return a + b + 3

    assert some_slot(1, 2) == {'name1': 4, 'name2': 5, 'name2-2': 6}


def test_run_slot_with_empty_list_annotation(folder, list_type):
    @folder(slot)
    def some_slot(a, b) -> list_type:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('name2')
    def function_3(a, b):
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_with_not_empty_list_annotation(folder, subscribable_list_type):
    @folder(slot)
    def some_slot(a, b) -> subscribable_list_type[int]:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('name2')
    def function_3(a, b):
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_with_not_empty_wrong_list_annotation(folder, subscribable_list_type):
    @folder(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "name1" return value 4 does not match the expected type str.')):
        some_slot(1, 2)


def test_run_slot_with_not_empty_wrong_list_annotation_but_type_check_is_off(subscribable_list_type):
    @slot(type_check=False)
    def some_slot(a, b) -> subscribable_list_type[str]:
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('name2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('name2')
    def function_3(a, b):
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_without_type_annotation(folder):
    bread_crumbs = []

    @folder(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('name1')
    def function_1(a, b):
        bread_crumbs.append(a + b + 1)
        return bread_crumbs[-1]

    @some_slot.plugin('name2')
    def function_2(a, b):
        bread_crumbs.append(a + b + 2)
        return bread_crumbs[-1]

    @some_slot.plugin('name2')
    def function_3(a, b):
        bread_crumbs.append(a + b + 3)
        return bread_crumbs[-1]

    assert some_slot(1, 2) is None
    assert bread_crumbs == [4, 5, 6]
