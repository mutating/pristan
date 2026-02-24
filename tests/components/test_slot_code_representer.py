from denial import InnerNoneType
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
        ...

    @transformed
    def function_5(a, b):
        """kek"""
        ...

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        ...

    @transformed
    def function_7():
        """
        kek
        lol
        """
        ...

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        ...

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        ...

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
        pass

    @transformed
    def function_5(a, b):
        """kek"""
        pass

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        pass

    @transformed
    def function_7():
        """
        kek
        lol
        """
        pass

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        pass

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        pass

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
        ...
        pass

    @transformed
    def function_2(a, b):
        ...
        pass

    @transformed
    def function_3(a, b, c=None):
        ...
        pass


    @transformed
    def function_4():
        """kek"""
        ...
        pass

    @transformed
    def function_5(a, b):
        """kek"""
        ...
        pass

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        ...
        pass


    @transformed
    def function_7():
        """
        kek
        lol
        """
        ...
        pass

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        ...
        pass

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        ...
        pass

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
        ...

    @transformed
    def function_2(a, b):
        ...
        ...

    @transformed
    def function_3(a, b, c=None):
        ...
        ...


    @transformed
    def function_4():
        """kek"""
        ...
        ...

    @transformed
    def function_5(a, b):
        """kek"""
        ...
        ...

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        ...
        ...


    @transformed
    def function_7():
        """
        kek
        lol
        """
        ...
        ...

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        ...
        ...

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        ...
        ...

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
        pass

    @transformed
    def function_2(a, b):
        pass
        pass

    @transformed
    def function_3(a, b, c=None):
        pass
        pass


    @transformed
    def function_4():
        """kek"""
        pass
        pass

    @transformed
    def function_5(a, b):
        """kek"""
        pass
        pass

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        pass
        pass

    @transformed
    def function_7():
        """
        kek
        lol
        """
        pass
        pass

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        pass
        pass

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        pass
        pass

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
        ...
        print('kek')

    @transformed
    def function_2(a, b):
        ...
        print('kek')

    @transformed
    def function_3(a, b, c=None):
        ...
        print('kek')

    @transformed
    def function_4():
        """kek"""
        ...
        print('kek')

    @transformed
    def function_5(a, b):
        """kek"""
        ...
        print('kek')

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        ...
        print('kek')

    @transformed
    def function_7():
        """
        kek
        lol
        """
        ...
        print('kek')

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        ...
        print('kek')

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        ...
        print('kek')

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
        print('kek')
        ...

    @transformed
    def function_2(a, b):
        print('kek')
        ...

    @transformed
    def function_3(a, b, c=None):
        print('kek')
        ...

    @transformed
    def function_4():
        """kek"""
        print('kek')
        ...

    @transformed
    def function_5(a, b):
        """kek"""
        print('kek')
        ...

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        print('kek')
        ...

    @transformed
    def function_7():
        """
        kek
        lol
        """
        print('kek')
        ...

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        print('kek')
        ...

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        print('kek')
        ...

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
        pass
        print('kek')

    @transformed
    def function_2(a, b):
        pass
        print('kek')

    @transformed
    def function_3(a, b, c=None):
        pass
        print('kek')

    @transformed
    def function_4():
        """kek"""
        pass
        print('kek')

    @transformed
    def function_5(a, b):
        """kek"""
        pass
        print('kek')

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        pass
        print('kek')

    @transformed
    def function_7():
        """
        kek
        lol
        """
        pass
        print('kek')

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        pass
        print('kek')

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        pass
        print('kek')

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
        print('kek')
        pass

    @transformed
    def function_2(a, b):
        print('kek')
        pass

    @transformed
    def function_3(a, b, c=None):
        print('kek')
        pass

    @transformed
    def function_4():
        """kek"""
        print('kek')
        pass

    @transformed
    def function_5(a, b):
        """kek"""
        print('kek')
        pass

    @transformed
    def function_6(a, b, c=None):
        """kek"""
        print('kek')
        pass

    @transformed
    def function_7():
        """
        kek
        lol
        """
        print('kek')
        pass

    @transformed
    def function_8(a, b):
        """
        kek
        lol
        """
        print('kek')
        pass

    @transformed
    def function_9(a, b, c=None):
        """
        kek
        lol
        """
        print('kek')
        pass

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

    print(SlotCodeRepresenter(function).returning_type)
    assert SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert isinstance(SlotCodeRepresenter(function).returning_type, InnerNoneType)


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
    def function() -> int:
        ...

    assert not SlotCodeRepresenter(function).returns_list
    assert not SlotCodeRepresenter(function).returns_dict
    assert SlotCodeRepresenter(function).returning_type is int
