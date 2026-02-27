from sys import version_info

import pytest
from denial import InnerNoneType
from full_match import match
from packaging.version import Version
from printo import descript_data_object

from pristan.components.slot_code_representer import SlotCodeRepresenter


def test_function_with_one_single_ellipsis_is_empty(transformed):
    @transformed
    def function_1():
        ...

    @transformed
    def function_2(a, b):
        ...

    @transformed
    def function_3(a, b, c=None):
        ...

    @transformed
    def function_4():
        """kek"""

    @transformed
    def function_5(a, b):
        """kek"""

    @transformed
    def function_6(a, b, c=None):
        """kek"""

    @transformed
    def function_7():
        """
        kek
        lol
        """

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """

    assert SlotCodeRepresenter(function_1).is_empty
    assert SlotCodeRepresenter(function_2).is_empty
    assert SlotCodeRepresenter(function_3).is_empty
    assert SlotCodeRepresenter(function_4).is_empty
    assert SlotCodeRepresenter(function_5).is_empty
    assert SlotCodeRepresenter(function_6).is_empty
    assert SlotCodeRepresenter(function_7).is_empty
    assert SlotCodeRepresenter(function_8).is_empty
    assert SlotCodeRepresenter(function_9).is_empty


def test_function_with_one_single_pass_is_empty(transformed):
    @transformed
    def function_1():
        pass

    @transformed
    def function_2(a, b):
        pass

    @transformed
    def function_3(a, b, c=None):
        pass

    @transformed
    def function_4():
        """kek"""

    @transformed
    def function_5(a, b):
        """kek"""

    @transformed
    def function_6(a, b, c=None):
        """kek"""

    @transformed
    def function_7():
        """
        kek
        lol
        """

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """

    assert SlotCodeRepresenter(function_1).is_empty
    assert SlotCodeRepresenter(function_2).is_empty
    assert SlotCodeRepresenter(function_3).is_empty
    assert SlotCodeRepresenter(function_4).is_empty
    assert SlotCodeRepresenter(function_5).is_empty
    assert SlotCodeRepresenter(function_6).is_empty
    assert SlotCodeRepresenter(function_7).is_empty
    assert SlotCodeRepresenter(function_8).is_empty
    assert SlotCodeRepresenter(function_9).is_empty


def test_function_with_one_single_ellipsis_and_one_single_pass_is_empty(transformed):
    @transformed
    def function_1():
        pass

    @transformed
    def function_2(a, b):
        pass

    @transformed
    def function_3(a, b, c=None):
        pass


    @transformed
    def function_4():
        """kek"""

    @transformed
    def function_5(a, b):
        """kek"""

    @transformed
    def function_6(a, b, c=None):
        """kek"""


    @transformed
    def function_7():
        """
        kek
        lol
        """

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """

    assert SlotCodeRepresenter(function_1).is_empty
    assert SlotCodeRepresenter(function_2).is_empty
    assert SlotCodeRepresenter(function_3).is_empty
    assert SlotCodeRepresenter(function_4).is_empty
    assert SlotCodeRepresenter(function_5).is_empty
    assert SlotCodeRepresenter(function_6).is_empty
    assert SlotCodeRepresenter(function_7).is_empty
    assert SlotCodeRepresenter(function_8).is_empty
    assert SlotCodeRepresenter(function_9).is_empty


def test_function_with_two_ellipsises_is_empty(transformed):
    @transformed
    def function_1():
        ...

    @transformed
    def function_2(a, b):
        ...

    @transformed
    def function_3(a, b, c=None):
        ...


    @transformed
    def function_4():
        """kek"""

    @transformed
    def function_5(a, b):
        """kek"""

    @transformed
    def function_6(a, b, c=None):
        """kek"""


    @transformed
    def function_7():
        """
        kek
        lol
        """

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """

    assert SlotCodeRepresenter(function_1).is_empty
    assert SlotCodeRepresenter(function_2).is_empty
    assert SlotCodeRepresenter(function_3).is_empty
    assert SlotCodeRepresenter(function_4).is_empty
    assert SlotCodeRepresenter(function_5).is_empty
    assert SlotCodeRepresenter(function_6).is_empty
    assert SlotCodeRepresenter(function_7).is_empty
    assert SlotCodeRepresenter(function_8).is_empty
    assert SlotCodeRepresenter(function_9).is_empty


def test_function_with_two_passes_is_empty(transformed):
    @transformed
    def function_1():
        pass

    @transformed
    def function_2(a, b):
        pass

    @transformed
    def function_3(a, b, c=None):
        pass


    @transformed
    def function_4():
        """kek"""

    @transformed
    def function_5(a, b):
        """kek"""

    @transformed
    def function_6(a, b, c=None):
        """kek"""

    @transformed
    def function_7():
        """
        kek
        lol
        """

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """

    assert SlotCodeRepresenter(function_1).is_empty
    assert SlotCodeRepresenter(function_2).is_empty
    assert SlotCodeRepresenter(function_3).is_empty
    assert SlotCodeRepresenter(function_4).is_empty
    assert SlotCodeRepresenter(function_5).is_empty
    assert SlotCodeRepresenter(function_6).is_empty
    assert SlotCodeRepresenter(function_7).is_empty
    assert SlotCodeRepresenter(function_8).is_empty
    assert SlotCodeRepresenter(function_9).is_empty


def test_function_with_ellipsis_and_some_code_after_is_not_empty(transformed):
    @transformed
    def function_1():
        print('kek')  # noqa: T201

    @transformed
    def function_2(a, b):
        return a + b

    @transformed
    def function_3(a, b, c=None):
        return a + b + c

    @transformed
    def function_4():
        """kek"""
        print('kek')  # noqa: T201

    @transformed
    def function_5(a, b):
        """kek"""
        return a + b

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        return a + b + c

    @transformed
    def function_7():
        """
        kek
        lol
        """
        print('kek')  # noqa: T201

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        return a + b

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        return a + b + c

    assert not SlotCodeRepresenter(function_1).is_empty
    assert not SlotCodeRepresenter(function_2).is_empty
    assert not SlotCodeRepresenter(function_3).is_empty
    assert not SlotCodeRepresenter(function_4).is_empty
    assert not SlotCodeRepresenter(function_5).is_empty
    assert not SlotCodeRepresenter(function_6).is_empty
    assert not SlotCodeRepresenter(function_7).is_empty
    assert not SlotCodeRepresenter(function_8).is_empty
    assert not SlotCodeRepresenter(function_9).is_empty


def test_function_with_ellipsis_and_some_code_before_is_not_empty(transformed):
    @transformed
    def function_1():
        print('kek')  # noqa: T201

    @transformed
    def function_2(a, b):
        return a + b

    @transformed
    def function_3(a, b, c=None):
        return a + b + c

    @transformed
    def function_4():
        """kek"""
        print('kek')  # noqa: T201

    @transformed
    def function_5(a, b):
        """kek"""
        return a + b

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        return a + b + c

    @transformed
    def function_7():
        """
        kek
        lol
        """
        print('kek')  # noqa: T201

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        return a + b

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        return a + b + c

    assert not SlotCodeRepresenter(function_1).is_empty
    assert not SlotCodeRepresenter(function_2).is_empty
    assert not SlotCodeRepresenter(function_3).is_empty
    assert not SlotCodeRepresenter(function_4).is_empty
    assert not SlotCodeRepresenter(function_5).is_empty
    assert not SlotCodeRepresenter(function_6).is_empty
    assert not SlotCodeRepresenter(function_7).is_empty
    assert not SlotCodeRepresenter(function_8).is_empty
    assert not SlotCodeRepresenter(function_9).is_empty


def test_function_with_pass_and_some_code_after_is_not_empty(transformed):
    @transformed
    def function_1():
        print('kek')  # noqa: T201

    @transformed
    def function_2(a, b):
        return a + b

    @transformed
    def function_3(a, b, c=None):
        return a + b + c

    @transformed
    def function_4():
        """kek"""
        print('kek')  # noqa: T201

    @transformed
    def function_5(a, b):
        """kek"""
        return a + b

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        return a + b + c

    @transformed
    def function_7():
        """
        kek
        lol
        """
        print('kek')  # noqa: T201

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        return a + b

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        return a + b + c

    assert not SlotCodeRepresenter(function_1).is_empty
    assert not SlotCodeRepresenter(function_2).is_empty
    assert not SlotCodeRepresenter(function_3).is_empty
    assert not SlotCodeRepresenter(function_4).is_empty
    assert not SlotCodeRepresenter(function_5).is_empty
    assert not SlotCodeRepresenter(function_6).is_empty
    assert not SlotCodeRepresenter(function_7).is_empty
    assert not SlotCodeRepresenter(function_8).is_empty
    assert not SlotCodeRepresenter(function_9).is_empty


def test_function_with_pass_and_some_code_before_is_not_empty(transformed):
    @transformed
    def function_1():
        print('kek')  # noqa: T201

    @transformed
    def function_2(a, b):
        return a + b

    @transformed
    def function_3(a, b, c=None):
        return a + b + c

    @transformed
    def function_4():
        """kek"""
        print('kek')  # noqa: T201

    @transformed
    def function_5(a, b):
        """kek"""
        return a + b

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        return a + b + c

    @transformed
    def function_7():
        """
        kek
        lol
        """
        print('kek')  # noqa: T201

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        return a + b

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        return a + b + c

    assert not SlotCodeRepresenter(function_1).is_empty
    assert not SlotCodeRepresenter(function_2).is_empty
    assert not SlotCodeRepresenter(function_3).is_empty
    assert not SlotCodeRepresenter(function_4).is_empty
    assert not SlotCodeRepresenter(function_5).is_empty
    assert not SlotCodeRepresenter(function_6).is_empty
    assert not SlotCodeRepresenter(function_7).is_empty
    assert not SlotCodeRepresenter(function_8).is_empty
    assert not SlotCodeRepresenter(function_9).is_empty


def test_just_list_is_list(transformed, list_type):
    @transformed
    def function() -> list_type:
        ...

    @transformed
    def function2(a, b) -> list_type:
        return [a + b]

    assert SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert isinstance(SlotCodeRepresenter(function).returning_type, InnerNoneType)

    assert SlotCodeRepresenter(function2).returns_list
    assert not SlotCodeRepresenter(function2).returns_dict
    assert isinstance(SlotCodeRepresenter(function2).returning_type, InnerNoneType)


def test_just_dict_is_dict(transformed, dict_type):
    @transformed
    def function() -> dict_type:
        ...

    assert SlotCodeRepresenter(function).returns_dict
    assert not SlotCodeRepresenter(function).returns_list
    assert isinstance(SlotCodeRepresenter(function).returning_type, InnerNoneType)


def test_dict_with_parameters_is_dict(transformed, subscribable_dict_type):
    @transformed
    def function() -> subscribable_dict_type[str, str]:
        ...

    assert SlotCodeRepresenter(function).returns_dict
    assert not SlotCodeRepresenter(function).returns_list
    assert SlotCodeRepresenter(function).returning_type is str


def test_list_with_parameters_is_list(transformed, subscribable_list_type):
    @transformed
    def function() -> subscribable_list_type[str]:
        ...

    assert SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert SlotCodeRepresenter(function).returning_type is str


def test_empty_hint_returns_sentinel(transformed):
    @transformed
    def function():
        ...

    assert not SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert isinstance(SlotCodeRepresenter(function).returning_type, InnerNoneType)


def test_returning_another_objects(transformed):
    @transformed
    def function() -> int:  # type: ignore[empty-body]
        ...

    assert not SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert SlotCodeRepresenter(function).returning_type is int


def test_base_module():
    def function(): ...

    assert SlotCodeRepresenter(descript_data_object).base_module == 'printo'
    assert SlotCodeRepresenter(function).base_module == 'tests'


def test_package_version():
    def function(): ...

    assert SlotCodeRepresenter(descript_data_object).package_version == Version('0.0.14')
    assert SlotCodeRepresenter(function).package_version is None


@pytest.mark.skipif(version_info >= (3, 10), reason='On new versions of Python, it is not possible to pass the wrong number of arguments.')
def test_wrong_dict_type_annotation(subscribable_dict_type):
    def function() -> subscribable_dict_type[str]: ...

    if subscribable_dict_type is dict:
        with pytest.raises(TypeError, match=match('Incorrect type annotation for the dict.')):
            SlotCodeRepresenter(function).returning_type  # noqa: B018

    else:
        with pytest.raises(TypeError, match=match('Too few arguments for typing.Dict; actual 1, expected 2')):
            SlotCodeRepresenter(function).returning_type  # noqa: B018


def test_base_module_and_package_version_are_none_when_cant_get_module():
    assert SlotCodeRepresenter(1).base_module is None
    assert SlotCodeRepresenter(1).package_version is None
