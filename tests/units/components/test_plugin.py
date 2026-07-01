from sys import version_info
from typing import List, Union

import pytest
from full_match import match

from pristan.components.plugin import Plugin
from pristan.errors import NumberOfCallsError


def test_i_can_run_plugin():
    """A Plugin call forwards arguments and returns the wrapped function's raw result, accepting valid checked returns and ignoring expected type mismatches when type checks are disabled regardless of unique."""
    assert Plugin('some_name', lambda x, y: x + y, int, True, True)(1, 2) == 3
    assert Plugin('some_name', lambda x, y: x + y, str, False, True)(1, 2) == 3
    assert Plugin('some_name', lambda x, y: x + y, int, True, False)(1, 2) == 3
    assert Plugin('some_name', lambda x, y: x + y, str, False, False)(1, 2) == 3


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_type_check_is_not_passed_without_ignore_new_pythons():
    """
    Plugin return type checking reports modern-Python expectation names for mismatched results.

    With type_check=True, an int result is rejected for str, List, and Union expectations for both unique settings, proving uniqueness does not bypass the check.
    """
    plugin_name = 'some_name'

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type str.')):
        Plugin(plugin_name, lambda x, y: x + y, str, True, True)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type List.')):
        Plugin(plugin_name, lambda x, y: x + y, List, True, True)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type Union.')):
        Plugin(plugin_name, lambda x, y: x + y, Union[List, str], True, True)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type str.')):
        Plugin(plugin_name, lambda x, y: x + y, str, True, False)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type List.')):
        Plugin(plugin_name, lambda x, y: x + y, List, True, False)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type Union.')):
        Plugin(plugin_name, lambda x, y: x + y, Union[List, str], True, False)(1, 2)


@pytest.mark.skipif(not (version_info[:2] == (3, 8) or version_info[:2] == (3, 9)), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_type_check_is_not_passed_without_ignore():
    """Plugins with type_check=True reject mismatched return values on Python 3.8/3.9 using the legacy expected-type text for str, typing.List, and typing.Union[typing.List, str], regardless of unique."""
    plugin_name = 'some_name'

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type str.')):
        Plugin(plugin_name, lambda x, y: x + y, str, True, True)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type typing.List.')):
        Plugin(plugin_name, lambda x, y: x + y, List, True, True)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type typing.Union[typing.List, str].')):
        Plugin(plugin_name, lambda x, y: x + y, Union[List, str], True, True)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type str.')):
        Plugin(plugin_name, lambda x, y: x + y, str, True, False)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type typing.List.')):
        Plugin(plugin_name, lambda x, y: x + y, List, True, False)(1, 2)

    with pytest.raises(TypeError, match=match(f'The type int of the plugin\'s "{plugin_name}" return value 3 does not match the expected type typing.Union[typing.List, str].')):
        Plugin(plugin_name, lambda x, y: x + y, Union[List, str], True, False)(1, 2)


def test_set_name():
    """Plugin.set_name replaces a plugin's current observable name after initialization."""
    plugin = Plugin('some_name', lambda x, y: x + y, int, True, True)

    assert plugin.name == 'some_name'

    plugin.set_name('kek')

    assert plugin.name == 'kek'


def test_repr():
    """Plugin repr includes the name, callable, expected type, type_check, unique, and run_once only when non-default."""
    def some_function(a, b): ...

    assert repr(Plugin('some_name', lambda x, y: x + y, int, True, True)) == "Plugin('some_name', plugin_function=lambda x, y: x + y, expected_result_type=int, type_check=True, unique=True)"
    assert repr(Plugin('some_name', some_function, int, True, True)) == "Plugin('some_name', plugin_function=some_function, expected_result_type=int, type_check=True, unique=True)"
    assert repr(Plugin('some_name', some_function, int, True, True, run_once=True)) == "Plugin('some_name', plugin_function=some_function, expected_result_type=int, type_check=True, unique=True, run_once=True)"


def test_run_once_off():
    """A Plugin with run_once disabled can be called repeatedly, using each call's arguments."""
    plugin = Plugin('some_name', lambda x, y: x + y, int, True, True, run_once=False)

    assert plugin(1, 2) == 3
    assert plugin(1, 3) == 4


def test_run_once_on():
    """run_once plugins allow one direct Plugin call and raise NumberOfCallsError on the next call to the same instance."""
    plugin = Plugin('some_name', lambda x, y: x + y, int, True, True, run_once=True)

    assert plugin(1, 2) == 3

    with pytest.raises(NumberOfCallsError, match=match('A limit of 1 has been set on the number of calls for plugin "some_name". And this plugin has already been called previously.')):
        plugin(1, 3)
