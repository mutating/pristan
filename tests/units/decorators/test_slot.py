from sys import version_info

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
        @some_slot.plugin('plugin')
        def plugin():
            ...


def test_plugin_have_not_comparing_signature_to_slot(folder_slot):
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    with pytest.raises(SignatureMismatchError, match=match('No common calling method has been found between the slot and the plugin.')):
        @some_slot.plugin('name')
        def plugin():
            ...


def test_run_1_plugin_without_hints(folder_slot):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b):
        bread_crumbs.append(a + b)

    @some_slot.plugin('some_plugin')
    def some_plugin(a, b):
        bread_crumbs.append(a + b + 1)

    assert some_slot(1, 2) is None

    assert bread_crumbs == [4]


def test_run_1_plugin_with_emplty_list_hint(folder_slot, list_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> list_type:  # type: ignore[return]
        bread_crumbs.append(a + b)

    @some_slot.plugin('some_plugin')
    def some_plugin(a, b):
        bread_crumbs.append(a + b + 1)
        return a + b + 2

    assert some_slot(1, 2) == [5]

    assert bread_crumbs == [4]


def test_2_not_unique_plugins_with_same_names(folder_slot):
    @folder_slot(slot)
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

    assert [x.name for x in some_slot] == ['kek', 'kek-2', 'kek-3']
    assert [x.name for x in some_slot['kek']] == ['kek', 'kek-2', 'kek-3']


def test_2_plugins_with_same_names_and_first_one_is_unique(folder_slot):
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('kek', unique=True)
    def plugin_1(a, b):
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Plugin "kek" claims to be unique, but there are other plugins with the same name.')):
        @some_slot.plugin('kek')
        def plugin_2(a, b):
            ...

    assert [x.name for x in some_slot] == ['kek']
    assert [x.name for x in some_slot['kek'].plugins] == ['kek']


def test_2_plugins_with_same_names_and_second_one_is_unique(folder_slot):
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('kek')
    def plugin_1(a, b):
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Plugin "kek-2" claims to be unique, but there are other plugins with the same name.')):
        @some_slot.plugin('kek', unique=True)
        def plugin_2(a, b):
            ...

    assert [x.name for x in some_slot] == ['kek']
    assert [x.name for x in some_slot['kek']] == ['kek']


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


def test_strange_slot_return_type_annotation(folder_slot):
    with pytest.raises(StrangeTypeAnnotationError, match=match('The return type annotation for a slot must be either a list or a dict, or remain empty.')):
        @folder_slot(slot)
        def some_slot(a, b) -> int:  # type: ignore[empty-body]
            ...


def test_plugin_name_is_not_valid_python_identifier(folder_slot):
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    with pytest.raises(ValueError, match=match('The plugin name must be a valid Python identifier.')):
        @some_slot.plugin('lol kek')
        def some_plugin(a, b):
            ...


def test_slot_return_type_is_dict_but_keys_are_not_str(folder_slot, subscribable_dict_type):
    with pytest.raises(TypeError, match=match('Incorrect type annotation for the dict.')):
        @folder_slot(slot)
        def some_slot(a, b) -> subscribable_dict_type[int, int]:
            ...


def test_run_slot_with_empty_dict_annotation(folder_slot, dict_type):
    @folder_slot(slot)
    def some_slot(a, b) -> dict_type:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('function_2')
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == {'function_1': 4, 'function_2': 5, 'function_2-2': 6}


def test_run_slot_with_not_empty_dict_annotation(folder_slot, subscribable_dict_type):
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, int]:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('function_2')
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == {'function_1': 4, 'function_2': 5, 'function_2-2': 6}


def test_run_slot_with_not_empty_wrong_dict_annotation(folder_slot, subscribable_dict_type):
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "function_1" return value 4 does not match the expected type str.')):
        some_slot(1, 2)


def test_run_slot_with_not_empty_wrong_dict_annotation_but_type_check_is_off(subscribable_dict_type):
    @slot(type_check=False)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('function_2')
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == {'function_1': 4, 'function_2': 5, 'function_2-2': 6}


def test_run_slot_with_empty_list_annotation(folder_slot, list_type):
    @folder_slot(slot)
    def some_slot(a, b) -> list_type:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('function_2')
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_with_not_empty_list_annotation(folder_slot, subscribable_list_type):
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[int]:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('function_2')
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_with_not_empty_wrong_list_annotation(folder_slot, subscribable_list_type):
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "function_1" return value 4 does not match the expected type str.')):
        some_slot(1, 2)


def test_run_slot_with_not_empty_wrong_list_annotation_but_type_check_is_off(subscribable_list_type):
    @slot(type_check=False)
    def some_slot(a, b) -> subscribable_list_type[str]:
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        return a + b + 1

    @some_slot.plugin('function_2')
    def function_2(a, b):
        return a + b + 2

    @some_slot.plugin('function_2')
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_without_type_annotation(folder_slot):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(a + b + 1)
        return bread_crumbs[-1]

    @some_slot.plugin('function_2')
    def function_2(a, b):
        bread_crumbs.append(a + b + 2)
        return bread_crumbs[-1]

    @some_slot.plugin('function_2')
    def function_2(a, b):  # noqa: F811
        bread_crumbs.append(a + b + 3)
        return bread_crumbs[-1]

    assert some_slot(1, 2) is None
    assert bread_crumbs == [4, 5, 6]


def test_run_not_empty_default_function_without_plugins_without_annotations(folder_slot):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b):
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) is None
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) is None
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_empty_dict_annotation(folder_slot, dict_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> dict_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return {'some_slot': bread_crumbs[-1]}

    assert some_slot(1, 2) == {'some_slot': 'run_slot_3'}
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_not_empty_dict_annotation(folder_slot, subscribable_dict_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return {'some_slot': bread_crumbs[-1]}

    assert some_slot(1, 2) == {'some_slot': 'run_slot_3'}
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_empty_list_annotation(folder_slot, list_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> list_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return [bread_crumbs[-1]]

    assert some_slot(1, 2) == ['run_slot_3']
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_not_empty_list_annotation(folder_slot, subscribable_list_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return [bread_crumbs[-1]]

    assert some_slot(1, 2) == ['run_slot_3']
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_dict_annotation_with_wrong_return_type_new_pythons(folder_slot, dict_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> dict_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type Dict.')):
        some_slot(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(not (version_info[:2] == (3, 8) or version_info[:2] == (3, 9)), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_dict_annotation_with_wrong_return_type(folder_slot, dict_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> dict_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type typing.Dict.')):
        some_slot(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_dict_annotation_with_wrong_return_type_new_pythons(folder_slot, subscribable_dict_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return 12

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_dict_type[str, str]:  # noqa: ARG001
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_dict_type[str, str]:
        return {a + b: bread_crumbs[-1]}

    @folder_slot(slot)
    def some_slot_4(a, b) -> subscribable_dict_type[str, str]:
        return {bread_crumbs[-1]: a + b}

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot" return value 12 does not match the expected type Dict.')):
        some_slot(1, 2)

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot_2" return value \'run_slot_3\' does not match the expected type Dict.')):
        some_slot_2(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_3" return value {3: \'run_slot_3\'} does not match the expected type Dict.')):
        some_slot_3(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_4" return value {\'run_slot_3\': 3} does not match the expected type Dict.')):
        some_slot_4(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(not (version_info[:2] == (3, 8) or version_info[:2] == (3, 9)), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_dict_annotation_with_wrong_return_type(folder_slot, subscribable_dict_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return 12

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_dict_type[str, str]:  # noqa: ARG001
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_dict_type[str, str]:
        return {a + b: bread_crumbs[-1]}

    @folder_slot(slot)
    def some_slot_4(a, b) -> subscribable_dict_type[str, str]:
        return {bread_crumbs[-1]: a + b}

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot" return value 12 does not match the expected type typing.Dict[str, str].')):
        some_slot(1, 2)

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot_2" return value \'run_slot_3\' does not match the expected type typing.Dict[str, str].')):
        some_slot_2(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_3" return value {3: \'run_slot_3\'} does not match the expected type typing.Dict[str, str].')):
        some_slot_3(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_4" return value {\'run_slot_3\': 3} does not match the expected type typing.Dict[str, str].')):
        some_slot_4(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_list_annotation_with_wrong_return_type_new_pythons(folder_slot, list_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> list_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> list_type:
        return a + b

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type List.')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type List.')):
        some_slot_2(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(not (version_info[:2] == (3, 8) or version_info[:2] == (3, 9)), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_list_annotation_with_wrong_return_type(folder_slot, list_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> list_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> list_type:
        return a + b

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type typing.List.')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type typing.List.')):
        some_slot_2(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info >= (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_list_annotation_with_wrong_return_type(folder_slot, subscribable_list_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_list_type[str]:
        return a + b

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_list_type[str]:
        return [a + b]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type typing.List[str].')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type typing.List[str].')):
        some_slot_2(1, 2)
    with pytest.raises(TypeError, match=match('The type list of the plugin\'s "some_slot_3" return value [3] does not match the expected type typing.List[str].')):
        some_slot_3(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_list_annotation_with_wrong_return_type_new_pythons(folder_slot, subscribable_list_type):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_list_type[str]:
        return a + b

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_list_type[str]:
        return [a + b]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type List.')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type List.')):
        some_slot_2(1, 2)
    with pytest.raises(TypeError, match=match('The type list of the plugin\'s "some_slot_3" return value [3] does not match the expected type List.')):
        some_slot_3(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @some_slot.plugin('function_1')
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


def test_getitem_bad_key(folder_slot):
    @folder_slot(slot)
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin():
        ...

    @some_slot.plugin('plugin')
    def plugin():  # noqa: F811
        ...

    @some_slot.plugin('plugin')
    def plugin():  # noqa: F811
        ...

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot['kek-kek']

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot['kek--']

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot[123]

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot[True]


def test_getitem_good_key(folder_slot):
    @folder_slot(slot)
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin():
        ...

    @some_slot.plugin('plugin')
    def plugin():  # noqa: F811
        ...

    @some_slot.plugin('plugin2')
    def plugin2():
        ...

    assert some_slot['plugin']
    assert len(some_slot['plugin']) == 2
    assert [x.name for x in some_slot['plugin']] == ['plugin', 'plugin-2']

    assert some_slot['plugin-1']
    assert len(some_slot['plugin-1']) == 1
    assert [x.name for x in some_slot['plugin-1']] == ['plugin']

    assert some_slot['plugin-2']
    assert len(some_slot['plugin-2']) == 1
    assert [x.name for x in some_slot['plugin-2']] == ['plugin-2']

    assert some_slot['plugin2']
    assert len(some_slot['plugin2']) == 1
    assert [x.name for x in some_slot['plugin2']] == ['plugin2']

    assert not some_slot['kek']
    assert len(some_slot['kek']) == 0
    assert [x.name for x in some_slot['kek']] == []

    assert not some_slot['kek-2']
    assert len(some_slot['kek-2']) == 0
    assert [x.name for x in some_slot['kek-2']] == []


def test_getitem_call(folder_slot):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot():
        bread_crumbs.append('some_slot')

    @some_slot.plugin('plugin')
    def plugin():
        bread_crumbs.append('plugin_1')

    @some_slot.plugin('plugin')
    def plugin():  # noqa: F811
        bread_crumbs.append('plugin_2')

    @some_slot.plugin('plugin2')
    def plugin2():
        bread_crumbs.append('plugin_3')

    some_slot['plugin']()

    assert bread_crumbs == ['plugin_1', 'plugin_2']

    bread_crumbs.clear()

    some_slot['plugin2']()

    assert bread_crumbs == ['plugin_3']

    bread_crumbs.clear()

    some_slot['kek']()

    assert bread_crumbs == ['some_slot']

    bread_crumbs.clear()


def test_getitem_call_with_parameters(folder_slot):
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b=3):
        bread_crumbs.append(f'some_slot_{a}_{b}')

    @some_slot.plugin('plugin')
    def plugin(a, b=4):
        bread_crumbs.append(f'plugin_1_{a}_{b}')

    @some_slot.plugin('plugin')
    def plugin(a, b=5):  # noqa: F811
        bread_crumbs.append(f'plugin_2_{a}_{b}')

    @some_slot.plugin('plugin2')
    def plugin2(a, b=6):
        bread_crumbs.append(f'plugin_3_{a}_{b}')

    some_slot['plugin'](1)

    assert bread_crumbs == ['plugin_1_1_4', 'plugin_2_1_5']

    bread_crumbs.clear()

    some_slot['plugin2'](1)

    assert bread_crumbs == ['plugin_3_1_6']

    bread_crumbs.clear()

    some_slot['kek'](1)

    assert bread_crumbs == ['some_slot_1_3']

    bread_crumbs.clear()

    some_slot['plugin'](1, 2)

    assert bread_crumbs == ['plugin_1_1_2', 'plugin_2_1_2']

    bread_crumbs.clear()

    some_slot['plugin2'](1, 2)

    assert bread_crumbs == ['plugin_3_1_2']

    bread_crumbs.clear()

    some_slot['kek'](1, 2)

    assert bread_crumbs == ['some_slot_1_2']

    bread_crumbs.clear()


def test_repr(folder_slot):
    @folder_slot(slot)
    def some_slot(a, b=3):
        ...

    @slot(name='name')
    def some_slot_2(a, b=3):
        ...

    @slot(name='name2', signature='..')
    def some_slot_3(a, b=3):
        ...

    @slot(name='name3', signature='..', max_plugins=3)
    def some_slot_4(a, b=3):
        ...

    @slot(name='name4', signature='..', max_plugins=3, type_check=False)
    def some_slot_5(a, b=3):
        ...

    assert repr(some_slot) == 'Slot(some_slot)'
    assert repr(some_slot_2) == 'Slot(some_slot_2, slot_name=\'name\')'
    assert repr(some_slot_3) == 'Slot(some_slot_3, signature=\'..\', slot_name=\'name2\')'
    assert repr(some_slot_4) == 'Slot(some_slot_4, signature=\'..\', slot_name=\'name3\', max_plugins=3)'
    assert repr(some_slot_5) == 'Slot(some_slot_5, signature=\'..\', slot_name=\'name4\', max_plugins=3, type_check=False)'


def test_getitem_repr(folder_slot):
    @folder_slot(slot)
    def some_slot(a, b=3):
        ...

    @some_slot.plugin('plugin')
    def plugin(a, b=3):
        ...

    @some_slot.plugin('plugin')
    def plugin(a, b=3):  # noqa: F811
        ...

    assert repr(some_slot['plugin']) == 'CallerWithPlugins(caller=SlotCaller(code_representation=SlotCodeRepresenter(some_slot), slot_name=None, slot_function=some_slot, type_check=True), plugins=[Plugin(\'plugin\', plugin_function=plugin, expected_result_type=InnerNoneType(1), type_check=True, unique=False), Plugin(\'plugin-2\', plugin_function=plugin, expected_result_type=InnerNoneType(1), type_check=True, unique=False)])'


def test_keys(folder_slot):
    @folder_slot(slot)
    def slot_1():
        ...

    @slot_1.plugin('plugin')
    def plugin():
        ...

    @slot_1.plugin('plugin')
    def plugin():  # noqa: F811
        ...

    @slot_1.plugin('plugin2')
    def plugin2():
        ...

    @folder_slot(slot)
    def slot_2():
        ...

    assert slot_1.keys() == ('plugin', 'plugin2')
    assert slot_2.keys() == ()


def test_getitem_is_loading_entry_points(folder_slot):
    @folder_slot(slot)
    def some_slot():
        ...

    assert not some_slot.loaded

    some_slot['kek']

    assert some_slot.loaded


def test_iter_is_loading_entry_points(folder_slot):
    @folder_slot(slot)
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin():
        ...

    @some_slot.plugin('plugin')
    def plugin():  # noqa: F811
        ...

    assert not some_slot.loaded

    for _ in some_slot:
        assert some_slot.loaded

    assert some_slot.loaded


def test_getting_keys_is_loading_entry_points(folder_slot):
    @folder_slot(slot)
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin():
        ...

    @some_slot.plugin('plugin')
    def plugin():  # noqa: F811
        ...

    assert not some_slot.loaded

    assert some_slot.keys() == ('plugin',)

    assert some_slot.loaded
