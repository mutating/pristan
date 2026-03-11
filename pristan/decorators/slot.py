from functools import partial, wraps
from typing import Callable, Optional, Union, overload

from pristan.common_types import PluginResult, SlotFunction, SlotPapameters
from pristan.components.slot import Slot


# TODO: concider to delete all "type: ignore" comments with "unused-ignore"'s in this file if python 3.8 deleted from the matrix
@overload
def slot(function: SlotFunction[SlotPapameters, PluginResult], /) -> SlotFunction[SlotPapameters, PluginResult]: ...  # type: ignore[type-arg, unused-ignore] # pragma: no branch

@overload
def slot(*, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan') -> Callable[[SlotFunction[SlotPapameters, PluginResult]], SlotFunction[SlotPapameters, PluginResult]]: ...  # type: ignore[type-arg, unused-ignore] # pragma: no branch

@overload
def slot(function: str, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan') -> Callable[[SlotFunction[SlotPapameters, PluginResult]], SlotFunction[SlotPapameters, PluginResult]]: ...  # type: ignore[type-arg, unused-ignore] # pragma: no branch

def slot(function: Optional[Union[SlotFunction[SlotPapameters, PluginResult], str]] = None, /, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan') -> Union[SlotFunction[SlotPapameters, PluginResult], Callable[[SlotFunction[SlotPapameters, PluginResult]], SlotFunction[SlotPapameters, PluginResult]]]:  # type: ignore[misc, type-arg, unused-ignore] # noqa: PLR0913, A002
    if callable(function):
        return wraps(function)(Slot(function, signature, name, max, type_check, entrypoint_group))  # type: ignore[arg-type, return-value, unused-ignore]

    if isinstance(function, str):
        if name is not None and name != function:
            raise ValueError('You have specified two different names for the slot.')
        name = function

    return partial(slot, signature=signature, name=name, max=max, type_check=type_check, entrypoint_group=entrypoint_group)  # type: ignore[arg-type, unused-ignore]
