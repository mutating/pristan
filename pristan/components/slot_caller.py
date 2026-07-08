import warnings
from typing import Any, Dict, Generator, Generic, List, NoReturn, Type, Union, cast

from denial import InnerNoneType
from printo import repred

from pristan.common_types import (
    PluginResult,
    SlotParameters,
    SlotResult,
)
from pristan.components.plugin import Plugin
from pristan.components.plugins_group import PluginsGroup
from pristan.components.slot_code_representer import sentinel as return_type_sentinel
from pristan.errors import OneResolutionError


@repred
class SlotCaller(Generic[PluginResult]):
    def __init__(self, slot: 'Slot[PluginResult]') -> None:  # type: ignore[name-defined]  # noqa: F821
        self.slot = slot

    @property
    def has_non_empty_default_body(self) -> bool:
        return not self.slot.code_representation.is_empty

    def __call__(self, plugins: Union[PluginsGroup[PluginResult], List[Plugin[PluginResult]]], *args: SlotParameters.args, **kwargs: SlotParameters.kwargs) -> SlotResult[PluginResult]:  # type: ignore[return]
        slot = self.slot
        code_representation = slot.code_representation
        slot_name = slot.slot_name
        slot_function = slot.slot_function
        type_check = slot.type_check

        if not code_representation.is_empty and not plugins:
            if code_representation.returns_list:
                if code_representation.returning_type is return_type_sentinel:
                    returns_type: Union[Type[Any], InnerNoneType] = List
                else:
                    returns_type = List[code_representation.returning_type]  # type: ignore[name-defined]
            elif code_representation.returns_dict:
                if code_representation.returning_type is return_type_sentinel:
                    returns_type = Dict
                else:
                    returns_type = Dict[str, code_representation.returning_type]  # type: ignore[name-defined]
            else:
                returns_type = code_representation.returning_type

            # TODO: consider to delete this "type: ignore" if python 3.9 deleted from the matrix
            result: SlotResult[PluginResult] = Plugin(slot_name, slot_function, returns_type, type_check, False)(*args, **kwargs)

            if code_representation.returning_type is return_type_sentinel and not code_representation.returns_dict and not code_representation.returns_list:
                result = None

            return result

        if code_representation.returns_list:
            return [plugin(*args, **kwargs) for plugin in plugins]

        if code_representation.returns_dict:
            return {plugin.name: plugin(*args, **kwargs) for plugin in plugins}

        for plugin in plugins:
            plugin(*args, **kwargs)


@repred
class CallerWithPlugins(Generic[PluginResult]):
    """
    Callable plugin selection returned by regular slot filtering.

    `CallerWithPlugins` preserves the normal slot contract: dispatch returns
    the full aggregate `SlotResult`. Its `.one` property creates a
    `OneCallerWithPlugins`, which keeps the same selected plugins but unwraps a
    single payload after dispatch.
    """

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
    def one(self) -> 'OneCallerWithPlugins[PluginResult]':
        if not self.caller.slot.unique:
            warnings.warn(f'Consider setting unique=True for slot "{self.caller.slot.slot_name}", because this code uses .one to work with a single plugin.', SyntaxWarning, stacklevel=2)
        if not self:
            raise OneResolutionError(f'Selection from slot "{self.caller.slot.slot_name}" has no selected plugins and the slot body is empty.')
        if len(self) > 1:
            raise OneResolutionError(f'Selection from slot "{self.caller.slot.slot_name}" has {len(self)} selected plugins, so .one cannot choose one.')
        return OneCallerWithPlugins(self.caller, list(self.plugins))

    @one.setter
    def one(self, value: Any) -> NoReturn:  # noqa: ARG002
        raise AttributeError('Attribute ".one" is read-only.')

    @one.deleter
    def one(self) -> NoReturn:
        raise AttributeError('Attribute ".one" is read-only.')


class OneCallerWithPlugins(CallerWithPlugins[PluginResult]):
    """
    Callable selection returned by `.one`.

    `CallerWithPlugins` keeps the regular slot contract and returns the full
    aggregate `SlotResult`. This subclass is used only for `.one`: it delegates
    dispatch to `CallerWithPlugins`, then verifies that an aggregate has exactly
    one result and unwraps that result to the plugin payload.
    """

    def __call__(self, *args: SlotParameters.args, **kwargs: SlotParameters.kwargs) -> PluginResult:  # type: ignore[override]
        result = super().__call__(*args, **kwargs)

        if self.caller.slot.code_representation.returning_type is return_type_sentinel:
            return None  # type: ignore[return-value]

        if isinstance(result, (list, dict)):
            result_count = len(result)
            if result_count != 1:
                raise OneResolutionError(f'Slot "{self.caller.slot.slot_name}" .one returned {result_count} results, so .one cannot choose one.')

            payload = result[0] if isinstance(result, list) else next(iter(result.values()))

        else:
            payload = cast(PluginResult, result)

        return payload
