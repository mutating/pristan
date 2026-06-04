from functools import partial, wraps
from typing import Any, Callable, Dict, List, Optional, overload

from pristan.common_types import (
    PluginResult,
    SlotDecoratorProtocol,
    SlotParameters,
    SlotProtocol,
)
from pristan.components.slot import Slot


@overload
def slot(function: Callable[SlotParameters, List[PluginResult]], /, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False) -> SlotProtocol[SlotParameters, List[PluginResult], PluginResult]: ...  # pragma: no branch, PLR0913, A002

@overload
def slot(function: Callable[SlotParameters, Dict[str, PluginResult]], /, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False) -> SlotProtocol[SlotParameters, Dict[str, PluginResult], PluginResult]: ...  # pragma: no branch, PLR0913, A002

@overload
def slot(function: Callable[SlotParameters, None], /, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False) -> SlotProtocol[SlotParameters, None, Any]: ...  # pragma: no branch, PLR0913, A002

@overload
def slot(function: str = ..., /, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False) -> SlotDecoratorProtocol: ...  # pragma: no branch, PLR0913, A002

def slot(function: Optional[object] = None, /, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False) -> Any:  # noqa: PLR0913, A002
    if callable(function):
        return wraps(function)(Slot(function, signature, name, max, type_check, entrypoint_group, unique))

    if isinstance(function, str):
        if name is not None and name != function:
            raise ValueError('You have specified two different names for the slot.')
        name = function

    return partial(slot, signature=signature, name=name, max=max, type_check=type_check, entrypoint_group=entrypoint_group, unique=unique)
