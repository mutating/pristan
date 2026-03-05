from collections import defaultdict
from typing import Any, DefaultDict, Generator, Generic, List, Optional

from printo import descript_data_object

from pristan.common_types import PluginResult
from pristan.components.plugin import Plugin


class PluginsGroup(Generic[PluginResult]):
    """
    The class is a collection of plugins.

    All collection operations are totally not thread-safe.
    """

    def __init__(self, caller: 'SlotCaller', plugins: Optional[List[Plugin[PluginResult]]] = None) -> None:  # type: ignore[name-defined] # noqa: F821
        self.caller = caller
        self.plugins: List[Plugin[PluginResult]] = []
        self.plugins_by_requested_names: DefaultDict[str, List[Plugin[PluginResult]]] = defaultdict(list)

        if plugins:
            self.add(*plugins)

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, [self.caller], {'plugins': self.plugins}, filters={'plugins': lambda x: bool(self.plugins)})  # noqa: ARG005

    def __bool__(self) -> bool:
        return bool(self.plugins)

    def __len__(self) -> int:
        return len(self.plugins)

    def __iter__(self) -> Generator[Plugin[PluginResult], None, None]:
        yield from self.plugins

    def __contains__(self, item: Any) -> bool:
        from pristan.components.plugin import Plugin  # noqa: PLC0415

        if isinstance(item, str):
            if item.isidentifier():
                return item in self.plugins_by_requested_names
            if self._is_identifier_with_number(item):
                splitted = item.split('-')
                first_part = splitted[0]
                second_part = splitted[1]
                if second_part == '1':
                    return first_part in self
                if first_part not in self.plugins_by_requested_names:
                    return False
                for plugin in self.plugins_by_requested_names[first_part]:
                    if plugin.name == item:
                        return True
                return False
            raise ValueError(f'The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, “name-22”. "{item}" is not a valid name for a plugin.')

        if isinstance(item, Plugin):
            return item.requested_name in self.plugins_by_requested_names and any(x.name == item.name for x in self.plugins_by_requested_names[item.requested_name])

        raise TypeError('Checking for inclusion is only possible for strings of a valid format or for plugin objects.')

    def __getitem__(self, key: str) -> 'CallerWithPlugins':  # type: ignore[name-defined] # noqa: F821
        from pristan.components.slot_caller import CallerWithPlugins  # noqa: PLC0415

        if isinstance(key, str):
            if key.isidentifier():
                if key in self.plugins_by_requested_names:
                    return CallerWithPlugins(self.caller, [x for x in self.plugins_by_requested_names[key]])
                return CallerWithPlugins(self.caller, [])

            if self._is_identifier_with_number(key):
                splitted = key.split('-')
                first_part = splitted[0]
                second_part = splitted[1]
                if first_part not in self.plugins_by_requested_names:
                    return CallerWithPlugins(self.caller, [])
                for plugin in self.plugins_by_requested_names[first_part]:
                    if (second_part == '1' and plugin.name == first_part) or plugin.name == key:
                        return CallerWithPlugins(self.caller, [plugin])
                return CallerWithPlugins(self.caller, [])

        raise KeyError('You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").')

    @staticmethod
    def _is_identifier_with_number(name: str) -> bool:
        return '-' in name and (lambda parts: len(parts) == 2 and parts[0].isidentifier() and parts[1].isdigit() and parts[1] != '0')(name.split('-'))  # noqa: PLC3002

    def add(self, *plugins: 'Plugin[PluginResult]') -> None:
        for plugin in plugins:
            self.plugins.append(plugin)
            self.plugins_by_requested_names[plugin.requested_name].append(plugin)

    def delete_last_by_name(self, name: str) -> None:
        self.plugins_by_requested_names[name].pop()
        self.plugins.pop()
