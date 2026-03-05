from typing import List, DefaultDict, Generator, Any, Optional
from collections import defaultdict
from functools import partial

from printo import descript_data_object

from pristan.errors import PrimadonnaPluginError


class PluginsGroup:
    """
    The class is a collection of plugins.

    All collection operations are not thread-safe.
    """

    def __init__(self, caller: 'SlotCaller', plugins: Optional[List['Plugin[PluginResult]']] = None) -> None:
        self.caller = caller
        self.plugins: List['Plugin[PluginResult]'] = []
        self.plugins_by_requested_names: DefaultDict[str, List['Plugin[PluginResult]']] = defaultdict(list)

        if plugins:
            self.add(*plugins)

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, [self.caller], {'plugins': self.plugins}, filters={'plugins': lambda x: bool(self.plugins)})

    def __nonzero__(self) -> bool:
        return bool(self.plugins)

    def __len__(self) -> int:
        return len(self.plugins)

    def __iter__(self) -> Generator['Plugin[PluginResult]', None, None]:
        yield from self.plugins

    def __contains__(self, item: Any) -> bool:
        from pristan.components.plugin import Plugin

        if isinstance(item, str):
            if item.isidentifier():
                return item in self.plugins_by_requested_names
            elif self._is_identifier_with_number(item):
                splitted = item.split('-')
                first_part = splitted[0]
                if first_part not in self.plugins_by_requested_names:
                    return False
                for plugin in self.plugins_by_requested_names[first_part]:
                    if plugin.name == item:
                        return True
                return False
            else:
                raise ValueError(f'The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, “name-22”. "{item}" is not a valid name for a plugin.')
        elif isinstance(item, Plugin):
            return item.requested_name in self.plugins_by_requested_names and any(x.name == item.name for x in self.plugins_by_requested_names[item.requested_name])
        else:
            raise TypeError()

    def __getitem__(self, key: str):
        if key.isidentifier():
            if key in self.plugins_by_requested_names:
                return partial(self.caller, [x for x in self.plugins_by_requested_names[key]])
            else:
                return partial(self.caller, [])

        elif self._is_identifier_with_number(key):
            ...
        else:
            raise KeyError()



    @staticmethod
    def _is_identifier_with_number(name: str) -> bool:
        return '-' in name and (lambda parts: len(parts) == 2 and parts[0].isidentifier() and parts[1].isdigit())(name.split('-'))

    def add(self, *plugins: 'Plugin[PluginResult]') -> None:
        for plugin in plugins:
            self.plugins.append(plugin)
            self.plugins_by_requested_names[plugin.requested_name].append(plugin)

    def delete_last_by_name(self, name: str) -> None:
        self.plugins_by_requested_names[name].pop()
        self.plugins.pop()
