from typing import Any, Dict, Generic, List, Optional, Type, Union

from denial import InnerNoneType
from printo import descript_data_object

from pristan.common_types import (
    PluginResult,
    SlotFunction,
    SlotPapameters,
    SlotResult,
)
from pristan.components.plugin import Plugin
from pristan.components.plugins_group import PluginsGroup
from pristan.components.slot_code_representer import SlotCodeRepresenter
from pristan.components.slot_code_representer import sentinel as return_type_sentinel


class SlotCaller(Generic[PluginResult]):
    def __init__(self, code_representation: SlotCodeRepresenter, slot_name: Optional[str], slot_function: SlotFunction[SlotPapameters, SlotResult[PluginResult]], type_check: bool) -> None:
        self.code_representation = code_representation
        self.slot_name = slot_name
        self.slot_function = slot_function
        self.type_check = type_check

    def __repr__(self) -> str:
        return descript_data_object(
            type(self).__name__,
            [],
            {
                'code_representation': self.code_representation,
                'slot_name': self.slot_name,
                'slot_function': self.slot_function,
                'type_check': self.type_check,
            },
        )

    def __call__(self, plugins: Union[PluginsGroup, List[Plugin[PluginResult]]], *args: SlotPapameters.args, **kwargs: SlotPapameters.kwargs) -> SlotResult[PluginResult]:  # type: ignore[return]
        if not self.code_representation.is_empty and not plugins:
            if self.code_representation.returns_list:
                if self.code_representation.returning_type is return_type_sentinel:
                    returns_type: Union[Type[Any], InnerNoneType] = List
                else:
                    returns_type = List[self.code_representation.returning_type]  # type: ignore[name-defined]
            elif self.code_representation.returns_dict:
                if self.code_representation.returning_type is return_type_sentinel:
                    returns_type = Dict
                else:
                    returns_type = Dict[str, self.code_representation.returning_type]  # type: ignore[name-defined]
            else:
                returns_type = self.code_representation.returning_type

            # TODO: consider to delete this "type: ignore" if python 3.9 deleted from the matrix
            result: SlotResult[PluginResult] = Plugin(self.slot_name if self.slot_name is not None else self.slot_function.__name__, self.slot_function, returns_type, self.type_check, False)(*args, **kwargs)  # type: ignore[assignment, unused-ignore]

            if self.code_representation.returning_type is return_type_sentinel and not self.code_representation.returns_dict and not self.code_representation.returns_list:
                result = None

            return result

        if self.code_representation.returns_list:
            return [plugin(*args, **kwargs) for plugin in plugins]

        if self.code_representation.returns_dict:
            return {plugin.name: plugin(*args, **kwargs) for plugin in plugins}

        for plugin in plugins:
            plugin(*args, **kwargs)


class CallerWithPlugins:
    def __init__(self, caller: SlotCaller, plugins: List[Plugin[PluginResult]]) -> None:
        self.caller = caller
        self.plugins = plugins

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.kwargs) -> SlotResult[PluginResult]:  # type: ignore[return]
        return self.caller(self.plugins, *args, **kwargs)

    def __repr__(self) -> str:
        return descript_data_object(
            type(self).__name__,
            [],
            {
                'caller': self.caller,
                'plugins': self.plugins,
            },
        )

    def __iter__(self) -> Generator[Plugin[PluginResult], None, None]:
        yield from self.plugins

    def __bool__(self) -> bool:
        return bool(self.plugins)

    def __len__(self) -> int:
        return len(self.plugins)
