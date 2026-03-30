from sys import version_info
from typing import Dict, List

import pytest


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
def folder_slot(request):
    return request.param


@pytest.fixture(params=('with_name', 'without_name'))
def folder_plugin(request):
    def folder(slot):
        def real_folder(function):
            if request.param == 'with_name':
                return slot.plugin(function.__name__)(function)
            if request.param == 'without_name':
                return slot.plugin(function)
        return real_folder

    return folder
