from typing import Callable, List, Optional, ParamSpec, TypeVar

SlotPapameters = ParamSpec('SlotPapameters')
PluginResult = TypeVar('PluginResult')
SlotResult = Optional[List[PluginResult]]
SlotFunction = Callable[SlotPapameters, Optional[List[PluginResult]]]
PluginFunction = Callable[SlotPapameters, PluginResult]
