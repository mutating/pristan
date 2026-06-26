from typing import Any, Dict, Generator, Generic, List, Type, Union

from denial import InnerNoneType
from printo import repred

from pristan.common_types import (
    PluginResult,
    SlotFunction,
    SlotParameters,
    SlotResult,
)
from pristan.components.plugin import Plugin
from pristan.components.plugins_group import PluginsGroup
from pristan.components.slot_code_representer import SlotCodeRepresenter
from pristan.components.slot_code_representer import sentinel as return_type_sentinel
from pristan.errors import OneResolutionError


@repred
class SlotCaller(Generic[PluginResult]):
    # TODO: consider to delete this "type: ignore" if python 3.8 deleted from the matrix
    def __init__(self, code_representation: SlotCodeRepresenter, slot_name: str, slot_function: SlotFunction[SlotParameters, SlotResult[PluginResult]], type_check: bool) -> None:
        self.code_representation = code_representation
        self.slot_name = slot_name
        self.slot_function = slot_function
        self.type_check = type_check

    @property
    def has_non_empty_default_body(self) -> bool:
        return not self.code_representation.is_empty

    def __call__(self, plugins: Union[PluginsGroup[PluginResult], List[Plugin[PluginResult]]], *args: SlotParameters.args, **kwargs: SlotParameters.kwargs) -> SlotResult[PluginResult]:  # type: ignore[return]
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
            result: SlotResult[PluginResult] = Plugin(self.slot_name, self.slot_function, returns_type, self.type_check, False)(*args, **kwargs)

            if self.code_representation.returning_type is return_type_sentinel and not self.code_representation.returns_dict and not self.code_representation.returns_list:
                result = None

            return result

        if self.code_representation.returns_list:
            return [plugin(*args, **kwargs) for plugin in plugins]

        if self.code_representation.returns_dict:
            return {plugin.name: plugin(*args, **kwargs) for plugin in plugins}

        for plugin in plugins:
            plugin(*args, **kwargs)


@repred
class CallerWithPlugins(Generic[PluginResult]):
    def __init__(self, caller: SlotCaller[PluginResult], plugins: List[Plugin[PluginResult]]) -> None:
        self.caller = caller
        self.plugins = plugins

    def __call__(self, *args: SlotParameters.args, **kwargs: SlotParameters.kwargs) -> SlotResult[PluginResult]:
        return self.caller(self.plugins, *args, **kwargs)

    def __iter__(self) -> Generator[Plugin[PluginResult], None, None]:
        yield from self.plugins

    def __bool__(self) -> bool:
        return bool(self.plugins) or self.caller.has_non_empty_default_body

    def __len__(self) -> int:
        return len(self.plugins)

    @property
    def one(self) -> 'CallerWithPlugins[PluginResult]':
        if not self:
            raise OneResolutionError(f'Selection from slot "{self.caller.slot_name}" has no selected plugins and the slot body is empty.')
        if len(self) > 1:
            raise OneResolutionError(f'Selection from slot "{self.caller.slot_name}" has {len(self)} selected plugins, so .one cannot choose one.')
        return self
