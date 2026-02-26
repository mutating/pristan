from sys import version_info
from typing import Dict, List

import pytest
from transfunctions import transfunction


@pytest.fixture(params=['async', 'sync', 'generator'])
def transformed(request):
    def transformator_function(function):
        if request.param == 'sync':
            return function
        if request.param == 'async':
            return transfunction(function, check_decorators=False).get_async_function()
        if request.param == 'generator':
            return transfunction(function, check_decorators=False).get_generator_function()
    return transformator_function


@pytest.fixture(params=[Dict, dict])
def dict_type(request):
    return request.param


@pytest.fixture(params=[List, list])
def list_type(request):
    return request.param


@pytest.fixture(params=([List] if version_info < (3, 9) else [List, list]))
def subscribable_list_type(request):
    return request.param


@pytest.fixture(params=([Dict] if version_info < (3, 9) else [Dict, dict]))
def subscribable_dict_type(request):
    return request.param


@pytest.fixture(params=(lambda x: x, lambda x: x()))
def folder(request):
    return request.param
