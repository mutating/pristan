from typing import Callable, List, Optional, ParamSpec, TypeVar


SlotPapameters = ParamSpec('Papameters')
PluginResult = TypeVar('PluginResult')
SlotResult = Optional[List[PluginResult]]
SlotFunction = Callable[SlotPapameters, SlotResult]
PluginFunction = Callable[SlotPapameters, PluginResult]
