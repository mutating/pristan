from functools import partial, wraps
from typing import Callable, Optional, Union, overload

from symplug.common_types import SlotFunction
from symplug.components.slot import Slot


@overload
def slot(func: SlotFunction, /) -> SlotFunction: ...

@overload
def slot(*, a: str, b: str) -> Callable[[SlotFunction], SlotFunction]: ...

def slot(function: Optional[SlotFunction] = None, /, *, signature: Optional[str] = None, name: Optional[str] = None, max: Optional[int] = None, type_check: bool = True) -> Union[SlotFunction, Callable[[SlotFunction], SlotFunction]]:
    if function is not None:
        decorator = wraps(function)(Slot(function, signature, name, max, type_check))
        return decorator

    return partial(slot, signature=signature, name=name, max=max, type_check=type_check)
