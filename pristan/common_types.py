from typing import Callable, List, Optional, ParamSpec, TypeVar, Union, Dict

SlotPapameters = ParamSpec('SlotPapameters')
PluginResult = TypeVar('PluginResult')
SlotResult = Optional[Union[List[PluginResult], Dict[str, PluginResult]]]
SlotFunction = Callable[SlotPapameters, Optional[Union[List[PluginResult], Dict[str, PluginResult]]]]
PluginFunction = Callable[SlotPapameters, PluginResult]
