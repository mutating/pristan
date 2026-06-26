from functools import partial, wraps
from typing import Any, Callable, Dict, List, Optional, overload

from pristan.common_types import (
    PluginResult,
    SlotDecoratorProtocol,
    SlotParameters,
    SlotProtocol,
    SlotSignature,
)
from pristan.components.slot import Slot


@overload
def slot(function: Callable[SlotParameters, List[PluginResult]], /, *, signature: Optional[SlotSignature] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False, explicit_plugin_names: bool = False) -> SlotProtocol[SlotParameters, List[PluginResult], PluginResult]: ...  # pragma: no branch, PLR0913, A002

@overload
def slot(function: Callable[SlotParameters, Dict[str, PluginResult]], /, *, signature: Optional[SlotSignature] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False, explicit_plugin_names: bool = False) -> SlotProtocol[SlotParameters, Dict[str, PluginResult], PluginResult]: ...  # pragma: no branch, PLR0913, A002

@overload
def slot(function: Callable[SlotParameters, None], /, *, signature: Optional[SlotSignature] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False, explicit_plugin_names: bool = False) -> SlotProtocol[SlotParameters, None, Any]: ...  # pragma: no branch, PLR0913, A002

@overload
def slot(function: str = ..., /, *, signature: Optional[SlotSignature] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False, explicit_plugin_names: bool = False) -> SlotDecoratorProtocol: ...  # pragma: no branch, PLR0913, A002

def slot(function: Optional[object] = None, /, *, signature: Optional[SlotSignature] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True, entrypoint_group: str = 'pristan', unique: bool = False, explicit_plugin_names: bool = False) -> Any:  # noqa: PLR0913, A002
    """
    Create a callable plugin slot from a decorated function.

    Slots are usually created by decorating a function. Plugins can be attached
    next to the slot with the slot's ``.plugin`` decorator:

    >>> from pristan import slot
    >>> @slot
    ... def collect_values() -> list[int]:
    ...     return []
    >>> @collect_values.plugin
    ... def collect_integer() -> int:
    ...     return 1
    >>> collect_values()
    [1]

    Plugins exposed through Python entry points are discovered lazily. Operations
    that call the slot, select plugins, report the slot's internal plugin state,
    or mutate that state resolve entry points before they inspect or change the
    plugin collection.

    Operations that mutate the slot's plugin collection are protected by the slot
    mutex. Plugin registration through ``.plugin(...)`` is synchronized as well
    and is the registration path used by modules loaded from entry points.
    """

    if callable(function):
        return wraps(function)(Slot(function, signature=signature, slot_name=name, max=max, type_check=type_check, entrypoint_group=entrypoint_group, unique=unique, explicit_plugin_names=explicit_plugin_names))

    if isinstance(function, str):
        if name is not None and name != function:
            raise ValueError('You have specified two different names for the slot.')
        name = function

    return partial(slot, signature=signature, name=name, max=max, type_check=type_check, entrypoint_group=entrypoint_group, unique=unique, explicit_plugin_names=explicit_plugin_names)
