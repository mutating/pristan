from collections import defaultdict
from threading import Lock
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    Union,
)

from denial import InnerNoneType
from sigmatch import PossibleCallMatcher
from sigmatch.errors import SignatureMismatchError

from pristan.common_types import (
    PluginFunction,
    PluginResult,
    SlotFunction,
    SlotPapameters,
    SlotResult,
)
from pristan.components.plugin import Plugin
from pristan.components.slot_code_representer import SlotCodeRepresenter
from pristan.components.slot_code_representer import sentinel as return_type_sentinel
from pristan.errors import (
    PrimadonnaPluginError,
    StrangeTypeAnnotationError,
    TooManyPluginsError,
)


class Slot(Generic[PluginResult]):
    def __init__(self, slot_function: SlotFunction[SlotPapameters, SlotResult[PluginResult]], signature: Optional[str], slot_name: Optional[str], max_plugins: Optional[int], type_check: bool) -> None:  # type: ignore[type-arg]
        if max_plugins is not None and max_plugins < 0:
            raise ValueError('The maximum number of plugins cannot be less than zero.')

        self.slot_function = slot_function
        self.code_representation = SlotCodeRepresenter(self.slot_function)

        if not self.code_representation.returns_list and not self.code_representation.returns_dict and self.code_representation.returning_type is not return_type_sentinel:
            raise StrangeTypeAnnotationError('The return type annotation for a slot must be either a list or a dict, or remain empty.')

        self.signature = signature
        self.slot_name = slot_name
        self.max_number_of_plugins = max_plugins
        self.type_check = type_check
        self.plugins: List[Plugin[PluginResult]] = []
        self.plugins_by_requested_names: DefaultDict[str, List[Plugin[PluginResult]]] = defaultdict(list)
        self.lock = Lock()

        # TODO: consider to delete this "type: ignore" if python 3.9 deleted from the matrix
        self._compare_signatures(self.slot_function, self.slot_function)  # type: ignore[arg-type, unused-ignore]

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.kwargs) -> SlotResult[PluginResult]:  # type: ignore[return]
        if not self.code_representation.is_empty and not self.plugins:
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

        plugins = self.plugins

        if self.code_representation.returns_list:
            return [plugin(*args, **kwargs) for plugin in plugins]

        if self.code_representation.returns_dict:
            return {plugin.name: plugin(*args, **kwargs) for plugin in plugins}

        for plugin in plugins:
            plugin(*args, **kwargs)

    def plugin(self, plugin_name: str, unique: bool = False) -> Callable[[PluginFunction[SlotPapameters, PluginResult]], PluginFunction[SlotPapameters, PluginResult]]:  # type: ignore[type-arg]
        if callable(plugin_name) or not plugin_name.isidentifier():
            raise ValueError('The plugin name must be a valid Python identifier.')

        def decorator(plugin_function: PluginFunction[SlotPapameters, PluginResult]) -> PluginFunction[SlotPapameters, PluginResult]:  # type: ignore[type-arg]
            # TODO: consider to delete this "type: ignore" if python 3.8 deleted from the matrix
            self._compare_signatures(self.slot_function, plugin_function)  # type: ignore[arg-type, unused-ignore]
            self._add_plugin(plugin_name, plugin_function, unique)
            return plugin_function

        return decorator

    def _add_plugin(self, name: str, function: PluginFunction[SlotPapameters, PluginResult], unique: bool) -> None:  # type: ignore[type-arg]
        plugin = Plugin(name, function, self.code_representation.returning_type, self.type_check, unique)

        with self.lock:
            if len(self.plugins) == self.max_number_of_plugins:
                raise TooManyPluginsError(f'The maximum number of plugins for this slot is {self.max_number_of_plugins}.')
            self.plugins.append(plugin)
            self.plugins_by_requested_names[name].append(plugin)
            if len(self.plugins_by_requested_names[name]) > 1:
                plugin.set_name(f'{name}-{len(self.plugins_by_requested_names[name])}')
                for other_plugin in self.plugins_by_requested_names[name]:
                    if other_plugin.unique:
                        self.plugins_by_requested_names[name].pop()
                        self.plugins.pop()
                        raise PrimadonnaPluginError(f'Plugin "{other_plugin.name}" claims to be unique, but there are other plugins with the same name.')

    def _compare_signatures(self, slot_function: SlotFunction[SlotPapameters, SlotResult[PluginResult]], plugin_function: PluginFunction[SlotPapameters, PluginResult]) -> None:  # type: ignore[type-arg]
        if self.signature is not None:
            PossibleCallMatcher(self.signature).match(plugin_function, raise_exception=True)
        elif not PossibleCallMatcher.from_callable(slot_function) & PossibleCallMatcher.from_callable(plugin_function):
            raise SignatureMismatchError('No common calling method has been found between the slot and the plugin.')
