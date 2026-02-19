from dataclasses import dataclass
from functools import partial, wraps
from typing import Callable, List, Optional, ParamSpec, TypeVar, Union, Any, Type, DefaultDict, overload
from collections import defaultdict
from threading import Lock

from sigmatch import PossibleCallMatcher
from sigmatch.errors import SignatureMismatchError
from simtypes import check
from denial import InnerNoneType

from symplug.errors import TooManyPluginsError, PrimadonnaPluginError
from symplug.components.slot_code_representer import SlotCodeRepresenter, sentinel as return_type_sentinel


SlotPapameters = ParamSpec('Papameters')
PluginResult = TypeVar('PluginResult')
SlotResult = Optional[List[PluginResult]]
SlotFunction = Callable[SlotPapameters, SlotResult]
PluginFunction = Callable[SlotPapameters, PluginResult]

@dataclass
class AddictionalArguments:
    how_many: Optional[Union[str, int]]


class Plugin:
    def __init__(self, name: str, plugin_function: PluginFunction, expected_result_type: Union[InnerNoneType, Type[Any]]) -> None:
        self.plugin_function = plugin_function
        self.requested_name = name
        self.name = name
        self.expected_result_type = expected_result_type

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.args) -> PluginResult:
        result = self.plugin_function(*args, **kwargs)

        if self.expected_result_type is not return_type_sentinel and not check(result, self.expected_result_type):
            raise TypeError()

        return result

    def set_name(self, name: str) -> None:
        self.name = name


class Slot:
    def __init__(self, slot_function: SlotFunction, arguments: AddictionalArguments, signature: Optional[str], slot_name: Optional[str], max: Optional[int]) -> None:
        if max is not None and max < 0:
            raise ValueError('The maximum number of plugins cannot be less than zero.')

        self.slot_function = slot_function
        self.code_representation = SlotCodeRepresenter(slot_function)
        self.arguments = arguments
        self.signature = signature
        self.slot_name = slot_name
        self.max_number_of_plugins = max
        self.plugins: List[Plugin] = []
        self.plugins_by_requested_names: DefaultDict[str, Plugin] = defaultdict(list)
        self.lock = Lock()

        self._compare_signatures(self.slot_function, self.slot_function)

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.args) -> SlotResult:
        if not self.code_representation.is_empty and not self.plugins:
            plugins = [Plugin(self.slot_name if self.slot_name is not None else self.slot_function.__name__, self.slot_function, self.code_representation.returns_type)]
        else:
            plugins = self.plugins

        if self.code_representation.returns_list:
            return [plugin(*args, **kwargs) for plugin in plugins]

        elif self.code_representation.returns_dict:
            return {plugin.name: plugin(*args, **kwargs) for plugin in plugins}

        return self.slot_function(*args, **kwargs)

    def plugin(self, plugin_name: str, unique: bool = False) -> Callable[[PluginFunction], PluginFunction]:
        if not plugin_name.isidentifier:
            raise ValueError('The plugin name must be a valid Python identifier.')

        def decorator(plugin_function: PluginFunction) -> PluginFunction:
            self._compare_signatures(self.slot_function, plugin_function)
            self._add_plugin(plugin_name, plugin_function, unique)
            return plugin_function

        return decorator

    def _add_plugin(self, name: str, function: PluginFunction, unique: bool) -> None:
        if not self.code_representation.returns_list and not self.code_representation.returns_dict and self.code_representation.returns_type is not return_type_sentinel and self.plugins:
            raise TypeError('You cannot register more than one plugin if the slot is not specified as returning a collection.')

        plugin = Plugin(name, function, self.code_representation.returns_type)

        with self.lock:
            if len(self.plugins) == self.max_number_of_plugins:
                raise TooManyPluginsError(f'The maximum number of plugins for this slot is {self.max_number_of_plugins}.')
            self.plugins.append(plugin)
            if self.plugins_by_requested_names[name] and unique:
                raise PrimadonnaPluginError(f'Plugin "{name}" claims to be unique, but there are other plugins with the same name.')
            self.plugins_by_requested_names[name].append(plugin)
            if len(self.plugins_by_requested_names[name]) > 1:
                plugin.set_name(f'{name}-{len(self.plugins_by_requested_names[name])}')

    def _compare_signatures(self, slot_function: SlotFunction, plugin_function: PluginFunction) -> None:
        if self.signature is not None:
            PossibleCallMatcher(self.signature).match(plugin_function, raise_exception=True)
        elif not PossibleCallMatcher.from_callable(slot_function) & PossibleCallMatcher.from_callable(plugin_function):
            raise SignatureMismatchError('No common calling method has been found between the slot and the plugin.')


@overload
def slot(func: SlotFunction, /) -> SlotFunction: ...

@overload
def slot(*, a: str, b: str) -> Callable[[SlotFunction], SlotFunction]: ...

def slot(function: Optional[SlotFunction] = None, /, *, how_many: Optional[Union[str, int]] = None, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None) -> Union[SlotFunction, Callable[[SlotFunction], SlotFunction]]:
    if function is not None:
        arguments = AddictionalArguments(
            how_many=how_many,
        )
        decorator = wraps(function)(Slot(function, arguments, signature, name, max))
        return decorator

    return partial(slot, how_many=how_many, signature=signature, name=name)
