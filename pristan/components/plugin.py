from typing import Any, Generic, Type, Union

from denial import InnerNoneType
from printo import descript_data_object
from simtypes import check

from pristan.common_types import PluginFunction, PluginResult, SlotPapameters
from pristan.components.slot_code_representer import sentinel as return_type_sentinel


class Plugin(Generic[PluginResult]):
    def __init__(self, name: str, plugin_function: PluginFunction[SlotPapameters, PluginResult], expected_result_type: Union[InnerNoneType, Type[Any]], type_check: bool, unique: bool) -> None:
        self.plugin_function = plugin_function
        self.requested_name = name
        self.name = name
        self.expected_result_type = expected_result_type
        self.type_check = type_check
        self.unique = unique

    def __repr__(self) -> str:
        return descript_data_object(
            type(self).__name__,
            (self.name,),
            {
                'plugin_function': self.plugin_function,
                'expected_result_type': self.expected_result_type,
                'type_check': self.type_check,
                'unique': self.unique,
            },
        )

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.kwargs) -> PluginResult:
        result = self.plugin_function(*args, **kwargs)  # type: ignore[arg-type]

        if self.type_check and self.expected_result_type is not return_type_sentinel and not check(result, self.expected_result_type, strict=True):  # type: ignore[arg-type]
            raise TypeError(f'The type {type(result).__name__} of the plugin\'s "{self.name}" return value {result!r} does not match the expected type {self.expected_result_type.__name__}.')  # type: ignore[union-attr]

        return result

    def set_name(self, name: str) -> None:
        self.name = name
