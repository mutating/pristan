from typing import List, Union
from sys import version_info

import pytest
from full_match import match

from pristan.components.plugin import Plugin


def test_i_can_run_plugin():
    assert Plugin('some_name', lambda x, y: x + y, int, True, True)(1, 2) == 3
    assert Plugin('some_name', lambda x, y: x + y, str, False, True)(1, 2) == 3
    assert Plugin('some_name', lambda x, y: x + y, int, True, False)(1, 2) == 3
    assert Plugin('some_name', lambda x, y: x + y, str, False, False)(1, 2) == 3


@pytest.mark.skipif(version_info <= (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_type_check_is_not_passed_without_ignore_new_pythons():
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


@pytest.mark.skipif(version_info >= (3, 10), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_type_check_is_not_passed_without_ignore():
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
    plugin = Plugin('some_name', lambda x, y: x + y, int, True, True)

    assert plugin.name == 'some_name'

    plugin.set_name('kek')

    assert plugin.name == 'kek'


def test_repr():
    def some_function(a, b): ...

    assert repr(Plugin('some_name', lambda x, y: x + y, int, True, True)) == "Plugin('some_name', plugin_function=λ, expected_result_type=int, type_check=True, unique=True)"
    assert repr(Plugin('some_name', some_function, int, True, True)) == "Plugin('some_name', plugin_function=some_function, expected_result_type=int, type_check=True, unique=True)"
