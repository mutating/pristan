import pytest

from pristan.components.slot_caller import CallerWithPlugins, OneCallerWithPlugins


@pytest.fixture(params=(CallerWithPlugins, OneCallerWithPlugins))
def caller_class(request):
    return request.param
