from typing import Union, Any, Type

from simtypes import check
from denial import InnerNoneType

from pristan.common_types import SlotPapameters, PluginResult, PluginFunction
from pristan.components.slot_code_representer import sentinel as return_type_sentinel


class Plugin:
    def __init__(self, name: str, plugin_function: PluginFunction, expected_result_type: Union[InnerNoneType, Type[Any]], type_check: bool) -> None:
        self.plugin_function = plugin_function
        self.requested_name = name
        self.name = name
        self.expected_result_type = expected_result_type
        self.type_check = type_check

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.args) -> PluginResult:
        result = self.plugin_function(*args, **kwargs)

        if self.type_check and self.expected_result_type is not return_type_sentinel and not check(result, self.expected_result_type):
            raise TypeError(f'The type {type(result).__name__} of the plugin\'s "{self.name}" return value {repr(result)} does not match the expected type {self.expected_result_type.__name__}.')

        return result

    def set_name(self, name: str) -> None:
        self.name = name
