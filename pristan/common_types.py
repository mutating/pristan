from typing import Callable, Dict, List, Optional, TypeVar, Union

try:
    from typing import ParamSpec
except ImportError:  # pragma: no cover
    from typing_extensions import ParamSpec  # type: ignore[assignment, unused-ignore]

SlotPapameters = ParamSpec('SlotPapameters')
PluginResult = TypeVar('PluginResult')
SlotResult = Optional[Union[List[PluginResult], Dict[str, PluginResult]]]
SlotFunction = Callable[SlotPapameters, Optional[Union[List[PluginResult], Dict[str, PluginResult]]]]
PluginFunction = Callable[SlotPapameters, PluginResult]
