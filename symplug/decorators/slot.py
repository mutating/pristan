from functools import partial, wraps
from typing import Callable, Optional, ParamSpec, TypeVar, Union, overload
from dataclasses import dataclass

Papameters = ParamSpec('Papameters')
SlotResult = TypeVar('SlotResult')
Function = Callable[Papameters, SlotResult]

@dataclass
class AddictionalArguments:
    how_many: Optional[Union[str, int]]


class Slot:
    def __init__(self, function: Function, arguments: AddictionalArguments) -> None:
        self.function = function
        self.arguments = arguments

    def __call__(self, *args: Papameters.args, **kwargs: Papameters.args) -> SlotResult:
        return self.function(*args, **kwargs)




@overload
def slot(func: Function, /) -> Function: ...

@overload
def slot(*, a: str, b: str) -> Callable[[Function], Function]: ...


def slot(function: Optional[Function] = None, /, *, how_many: Optional[Union[str, int]] = None) -> Union[Function, Callable[[Function], Function]]:
    if function is not None:
        arguments = AddictionalArguments(
            how_many=how_many,
        )
        decorator = wraps(function)(Slot(function, arguments))
        return decorator

    return partial(slot, how_many=how_many)
