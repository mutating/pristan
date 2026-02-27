from functools import partial, wraps
from typing import Callable, Optional, Union, overload

from pristan.common_types import PluginResult, SlotFunction, SlotPapameters
from pristan.components.slot import Slot


# TODO: concider to delete all "type: ignore" comments with "unused-ignore"'s in this file if python 3.8 deleted from the matrix
@overload
def slot(func: SlotFunction[SlotPapameters, PluginResult], /) -> SlotFunction[SlotPapameters, PluginResult]: ...  # pragma: no branch  # type: ignore[type-arg]

@overload
def slot(*, a: str, b: str) -> Callable[[SlotFunction[SlotPapameters, PluginResult]], SlotFunction[SlotPapameters, PluginResult]]: ...  # pragma: no branch  # type: ignore[type-arg]

def slot(function: Optional[SlotFunction[SlotPapameters, PluginResult]] = None, /, *, signature: Optional[str] = None, name: Optional[str] = None, max_plugins: Optional[int] = None, type_check: bool = True) -> Union[SlotFunction[SlotPapameters, PluginResult], Callable[[SlotFunction[SlotPapameters, PluginResult]], SlotFunction[SlotPapameters, PluginResult]]]:  # type: ignore[misc, type-arg]
    if function is not None:
        return wraps(function)(Slot(function, signature, name, max_plugins, type_check))  # type: ignore[arg-type, return-value, unused-ignore]

    return partial(slot, signature=signature, name=name, max_plugins=max_plugins, type_check=type_check)  # type: ignore[arg-type, unused-ignore]
