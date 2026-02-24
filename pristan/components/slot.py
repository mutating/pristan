from typing import Callable, List, Dict, Optional, DefaultDict
from collections import defaultdict
from threading import Lock

from sigmatch import PossibleCallMatcher
from sigmatch.errors import SignatureMismatchError

from packaging.version import Version

from pristan.errors import TooManyPluginsError, PrimadonnaPluginError
from pristan.components.slot_code_representer import SlotCodeRepresenter, sentinel as return_type_sentinel
from pristan.common_types import SlotPapameters, SlotResult, SlotFunction, PluginFunction
from pristan.components.plugin import Plugin


class Slot:
    def __init__(self, slot_function: SlotFunction, signature: Optional[str], slot_name: Optional[str], max: Optional[int], type_check: bool) -> None:
        if max is not None and max < 0:
            raise ValueError('The maximum number of plugins cannot be less than zero.')

        self.slot_function = slot_function
        self.code_representation = SlotCodeRepresenter(slot_function)
        self.signature = signature
        self.slot_name = slot_name
        self.max_number_of_plugins = max
        self.type_check = type_check
        self.plugins: List[Plugin] = []
        self.plugins_by_requested_names: DefaultDict[str, Plugin] = defaultdict(list)
        self.lock = Lock()

        self._compare_signatures(self.slot_function, self.slot_function)

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.args) -> SlotResult:
        if not self.code_representation.is_empty and not self.plugins:
            if self.code_representation.returns_list:
                if self.code_representation.returning_type is return_type_sentinel:
                    returns_type = List
                else:
                    returns_type = List[self.code_representation.returning_type]
            elif self.code_representation.returns_dict and self.code_representation.returning_type is return_type_sentinel:
                if self.code_representation.returning_type is return_type_sentinel:
                    returns_type = Dict
                else:
                    returns_type = Dict[str, self.code_representation.returning_type]
            else:
                returns_type = self.code_representation.returning_type

            plugins = [Plugin(self.slot_name if self.slot_name is not None else self.slot_function.__name__, self.slot_function, returns_type, self.type_check, False)]
        else:
            plugins = self.plugins

        if self.code_representation.returns_list:
            return [plugin(*args, **kwargs) for plugin in plugins]

        elif self.code_representation.returns_dict:
            return {plugin.name: plugin(*args, **kwargs) for plugin in plugins}

        for plugin in plugins:
            plugin(*args, **kwargs)

    def plugin(self, plugin_name: str, unique: bool = False) -> Callable[[PluginFunction], PluginFunction]:
        if callable(plugin_name) or not plugin_name.isidentifier:
            raise ValueError('The plugin name must be a valid Python identifier.')

        def decorator(plugin_function: PluginFunction) -> PluginFunction:
            self._compare_signatures(self.slot_function, plugin_function)
            self._add_plugin(plugin_name, plugin_function, unique)
            return plugin_function

        return decorator

    def _add_plugin(self, name: str, function: PluginFunction, unique: bool) -> None:
        if not self.code_representation.returns_list and not self.code_representation.returns_dict and self.code_representation.returning_type is not return_type_sentinel and self.plugins:
            raise TypeError('You cannot register more than one plugin if the slot is not specified as returning a collection.')

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

    def _compare_signatures(self, slot_function: SlotFunction, plugin_function: PluginFunction) -> None:
        if self.signature is not None:
            PossibleCallMatcher(self.signature).match(plugin_function, raise_exception=True)
        elif not PossibleCallMatcher.from_callable(slot_function) & PossibleCallMatcher.from_callable(plugin_function):
            raise SignatureMismatchError('No common calling method has been found between the slot and the plugin.')
