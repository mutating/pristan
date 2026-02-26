from functools import partial, wraps
from typing import Callable, Optional, Union, overload

from pristan.common_types import SlotFunction
from pristan.components.slot import Slot


@overload
def slot(func: SlotFunction, /) -> SlotFunction: ...

@overload
def slot(*, a: str, b: str) -> Callable[[SlotFunction], SlotFunction]: ...

def slot(function: Optional[SlotFunction] = None, /, *, signature: Optional[str] = None, name: Optional[str] = None, max_plugins: Optional[int] = None, type_check: bool = True) -> Union[SlotFunction, Callable[[SlotFunction], SlotFunction]]:
    if function is not None:
        return wraps(function)(Slot(function, signature, name, max_plugins, type_check))

    return partial(slot, signature=signature, name=name, max_plugins=max_plugins, type_check=type_check)
