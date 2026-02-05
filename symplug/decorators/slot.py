from dataclasses import dataclass
from functools import partial, wraps
from typing import Callable, List, Optional, ParamSpec, TypeVar, Union, overload

SlotPapameters = ParamSpec('Papameters')
PluginResult = TypeVar('PluginResult')
SlotResult = Optional[List[PluginResult]]
SlotFunction = Callable[SlotPapameters, SlotResult]
PluginFunction = Callable[SlotPapameters, PluginResult]

@dataclass
class AddictionalArguments:
    how_many: Optional[Union[str, int]]

class Slot:
    def __init__(self, slot_function: SlotFunction, arguments: AddictionalArguments) -> None:
        self.slot_function = slot_function
        self.arguments = arguments
        self.plugins = []

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.args) -> SlotResult:
        return self.slot_function(*args, **kwargs)

    def plugin(self, plugin_name: str) -> Callable[[PluginFunction], PluginFunction]:
        def decorator(plugin_function: PluginFunction) -> PluginFunction:
            self._compare_signatures(self.slot_function, plugin_function)
            self.plugins.append(plugin_function)
            return plugin_function
        return decorator

    def _compare_signatures(self, slot_function: SlotFunction, plugin_function: PluginFunction) -> None:
        pass


@overload
def slot(func: SlotFunction, /) -> SlotFunction: ...

@overload
def slot(*, a: str, b: str) -> Callable[[SlotFunction], SlotFunction]: ...

def slot(function: Optional[SlotFunction] = None, /, *, how_many: Optional[Union[str, int]] = None) -> Union[SlotFunction, Callable[[SlotFunction], SlotFunction]]:
    if function is not None:
        arguments = AddictionalArguments(
            how_many=how_many,
        )
        decorator = wraps(function)(Slot(function, arguments))
        return decorator

    return partial(slot, how_many=how_many)
