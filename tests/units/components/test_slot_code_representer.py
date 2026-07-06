from sys import version_info

import pytest
from denial import InnerNoneType
from full_match import match
from packaging.version import Version
from printo import describe_call

from pristan.components.slot_code_representer import SlotCodeRepresenter


def test_function_with_one_single_ellipsis_is_empty(transformed):
    """Treat bodies containing only a single ellipsis or only a docstring as empty across transformed sync, async, and generator functions with varied signatures."""
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
    """Treat bodies containing only a single `pass` or only a docstring as empty across transformed function forms and signatures."""
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
    """Extra blank lines between pass-only and docstring-only definitions do not affect empty-body detection across transformed signatures."""
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
    """Blank lines between ellipsis-only and docstring-only definition groups do not affect empty-body detection across transformed signatures."""
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
    """A blank line between pass-only and docstring-only definition groups does not affect empty-body detection across transformed signatures."""
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
    """Executable statements after optional docstrings make the represented body non-empty."""
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

    @transformed
    def function_10():
        ...  # noqa: PIE790
        return 'kek'

    assert not SlotCodeRepresenter(function_1).is_empty
    assert not SlotCodeRepresenter(function_2).is_empty
    assert not SlotCodeRepresenter(function_3).is_empty
    assert not SlotCodeRepresenter(function_4).is_empty
    assert not SlotCodeRepresenter(function_5).is_empty
    assert not SlotCodeRepresenter(function_6).is_empty
    assert not SlotCodeRepresenter(function_7).is_empty
    assert not SlotCodeRepresenter(function_8).is_empty
    assert not SlotCodeRepresenter(function_9).is_empty
    assert not SlotCodeRepresenter(function_10).is_empty


def test_function_with_ellipsis_and_some_code_before_is_not_empty(transformed):
    """Executable print or return statements make the represented body non-empty across transformed forms, with or without docstrings."""
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
    """Function bodies with executable print or return statements are not empty, including transformed forms with optional docstrings."""
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
    """Executable print or return statements make the body non-empty even when preceded by a docstring."""
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
    """Bare list and typing.List annotations mark both empty and list-returning bodies as list-returning, with InnerNoneType as returning_type."""
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
    """Bare dict and typing.Dict annotations select dict aggregation with no value type, leaving returning_type as the sentinel."""
    @transformed
    def function() -> dict_type:
        ...

    assert SlotCodeRepresenter(function).returns_dict
    assert not SlotCodeRepresenter(function).returns_list
    assert isinstance(SlotCodeRepresenter(function).returning_type, InnerNoneType)


def test_dict_with_parameters_is_dict(transformed, subscribable_dict_type):
    """Parameterized dict annotations are recognized as dict-returning, and their value type becomes returning_type."""
    @transformed
    def function() -> subscribable_dict_type[str, str]:
        ...

    assert SlotCodeRepresenter(function).returns_dict
    assert not SlotCodeRepresenter(function).returns_list
    assert SlotCodeRepresenter(function).returning_type is str


def test_list_with_parameters_is_list(transformed, subscribable_list_type):
    """Parameterized list annotations, including typing.List[str] and list[str] where available, mark the slot as list-aggregating and use str as the plugin return type."""
    @transformed
    def function() -> subscribable_list_type[str]:
        ...

    assert SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert SlotCodeRepresenter(function).returning_type is str


def test_empty_hint_returns_sentinel(transformed):
    """A slot function with no return annotation uses the InnerNoneType sentinel and does not select list or dict aggregation."""
    @transformed
    def function():
        ...

    assert not SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert isinstance(SlotCodeRepresenter(function).returning_type, InnerNoneType)


def test_returning_another_objects(transformed):
    """A non-list, non-dict return annotation does not select aggregation and remains the returning_type."""
    @transformed
    def function() -> int:  # type: ignore[empty-body]
        ...

    assert not SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert SlotCodeRepresenter(function).returning_type is int


def test_base_module():
    """base_module reports the top-level package for installed dependency functions and local test functions."""
    def function(): ...

    assert SlotCodeRepresenter(describe_call).base_module == 'printo'
    assert SlotCodeRepresenter(function).base_module == 'tests'


def test_package_version():
    """package_version is a Version for installed functions and None for local functions without distribution metadata."""
    def function(): ...

    assert SlotCodeRepresenter(describe_call).package_version >= Version('0.0.27')
    assert SlotCodeRepresenter(function).package_version is None


def test_wrong_dict_type_annotation(subscribable_dict_type):
    """Partially parameterized dict annotations are rejected: built-in dict[str] gets Pristan's dict-annotation TypeError, while typing.Dict[str] raises Python's version-specific arity error."""
    if subscribable_dict_type is dict:
        def function() -> subscribable_dict_type[str]: ...

        with pytest.raises(TypeError, match=match('Incorrect type annotation for the dict.')):
            SlotCodeRepresenter(function).returning_type  # noqa: B018

    elif version_info[:2] == (3, 8):
        with pytest.raises(TypeError, match=match('Too few parameters for typing.Dict; actual 1, expected at least 2')):  # noqa: PT012
            def function() -> subscribable_dict_type[str]: ...

            SlotCodeRepresenter(function).returning_type  # noqa: B018

    elif version_info[:2] == (3, 9):
        with pytest.raises(TypeError, match=match('Too few parameters for typing.Dict; actual 1, expected 2')):  # noqa: PT012
            def function() -> subscribable_dict_type[str]: ...

            SlotCodeRepresenter(function).returning_type  # noqa: B018

    else:
        with pytest.raises(TypeError, match=match('Too few arguments for typing.Dict; actual 1, expected 2')):  # noqa: PT012
            def function() -> subscribable_dict_type[str]: ...

            SlotCodeRepresenter(function).returning_type  # noqa: B018


def test_empty_list_is_nothing(dict_type, subscribable_dict_type, list_type, subscribable_list_type):
    """List-annotated slots treat a sole literal `return []` as no default body. This is a static source-shape rule: missing or non-list annotations, populated literals, computed values, variables, and comprehensions stay non-empty."""
    def function_1(): return []
    def function_2() -> dict_type: return []
    def function_3() -> subscribable_dict_type[str, int]: return []

    def function_4() -> list_type: return []
    def function_4_1() -> list_type: return [1, 2, 3]
    def function_4_2() -> list_type: return [None]
    def function_4_3() -> list_type:
        variable = 1 + 2
        return [variable]
    def function_4_4() -> list_type:
        variable = []  # type: ignore[var-annotated]
        return variable  # noqa: RET504
    def function_4_5(y) -> list_type: return [x for x in y]

    def function_5() -> subscribable_list_type[int]: return []
    def function_5_1() -> subscribable_list_type[int]: return [1, 2, 3]
    def function_5_2() -> subscribable_list_type[None]: return [None]
    def function_5_3() -> subscribable_list_type[int]:
        variable = 1 + 2
        return [variable]
    def function_5_4() -> subscribable_list_type[int]:
        variable = []  # type: ignore[var-annotated]
        return variable  # noqa: RET504
    def function_5_5(y) -> subscribable_list_type[int]: return [x for x in y]

    assert SlotCodeRepresenter(function_4).is_empty
    assert SlotCodeRepresenter(function_5).is_empty

    assert not SlotCodeRepresenter(function_1).is_empty
    assert not SlotCodeRepresenter(function_2).is_empty
    assert not SlotCodeRepresenter(function_3).is_empty

    assert not SlotCodeRepresenter(function_4_1).is_empty
    assert not SlotCodeRepresenter(function_4_2).is_empty
    assert not SlotCodeRepresenter(function_4_3).is_empty
    assert not SlotCodeRepresenter(function_4_4).is_empty
    assert not SlotCodeRepresenter(function_4_5).is_empty

    assert not SlotCodeRepresenter(function_5_1).is_empty
    assert not SlotCodeRepresenter(function_5_2).is_empty
    assert not SlotCodeRepresenter(function_5_3).is_empty
    assert not SlotCodeRepresenter(function_5_4).is_empty
    assert not SlotCodeRepresenter(function_5_5).is_empty


def test_empty_dict_is_nothing(dict_type, subscribable_dict_type, list_type, subscribable_list_type):
    """A single `return {}` is empty only for slots annotated to aggregate dict results; mismatched annotations and any non-empty or non-literal dict return remain fallback bodies."""
    def function_1(): return {}
    def function_2() -> list_type: return {}
    def function_3() -> subscribable_list_type[int]: return {}

    def function_4() -> dict_type: return {}
    def function_4_1() -> dict_type: return {'a': 1}
    def function_4_2() -> dict_type: return {'a': None}
    def function_4_3() -> dict_type:
        variable = 1 + 2
        return {'key': variable}
    def function_4_4() -> dict_type:
        variable = {}  # type: ignore[var-annotated]
        return variable  # noqa: RET504
    def function_4_5(y) -> dict_type: return {key: value for key, value in y.items()}

    def function_5() -> subscribable_dict_type[str, int]: return {}
    def function_5_1() -> subscribable_dict_type[str, int]: return {'a': 1}
    def function_5_2() -> subscribable_dict_type[str, None]: return {'a': None}
    def function_5_3() -> subscribable_dict_type[str, int]:
        variable = 1 + 2
        return {'key': variable}
    def function_5_4() -> subscribable_dict_type[str, int]:
        variable = {}  # type: ignore[var-annotated]
        return variable  # noqa: RET504
    def function_5_5(y) -> subscribable_dict_type[str, int]: return {key: value for key, value in y.items()}

    assert SlotCodeRepresenter(function_4).is_empty
    assert SlotCodeRepresenter(function_5).is_empty

    assert not SlotCodeRepresenter(function_1).is_empty
    assert not SlotCodeRepresenter(function_2).is_empty
    assert not SlotCodeRepresenter(function_3).is_empty

    assert not SlotCodeRepresenter(function_4_1).is_empty
    assert not SlotCodeRepresenter(function_4_2).is_empty
    assert not SlotCodeRepresenter(function_4_3).is_empty
    assert not SlotCodeRepresenter(function_4_4).is_empty
    assert not SlotCodeRepresenter(function_4_5).is_empty

    assert not SlotCodeRepresenter(function_5_1).is_empty
    assert not SlotCodeRepresenter(function_5_2).is_empty
    assert not SlotCodeRepresenter(function_5_3).is_empty
    assert not SlotCodeRepresenter(function_5_4).is_empty
    assert not SlotCodeRepresenter(function_5_5).is_empty
