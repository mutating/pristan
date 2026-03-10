from typing import Callable, Dict, List, Optional, TypeVar, Union

try:
    # TODO: ParamSpec appeared with python 3.10, so delete this try-except if python 3.9 deleted from the matrix
    from typing import ParamSpec  # type: ignore[attr-defined, unused-ignore]
except ImportError:  # pragma: no cover
    from typing_extensions import ParamSpec  # type: ignore[assignment, unused-ignore]

SlotPapameters = ParamSpec('SlotPapameters')
PluginResult = TypeVar('PluginResult')
SlotResult = Optional[Union[List[PluginResult], Dict[str, PluginResult]]]
SlotFunction = Callable[SlotPapameters, Optional[Union[List[PluginResult], Dict[str, PluginResult]]]]  # type: ignore[valid-type, misc, unused-ignore]
PluginFunction = Callable[SlotPapameters, PluginResult]  # type: ignore[valid-type, misc, unused-ignore]
