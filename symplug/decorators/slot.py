from typing import Optional, Callable, Any, ParamSpec, TypeVar, overload, Union, Optional
from functools import wraps, partial

from symplug.errors import StrangeUseOfTheDecorator


Papameters = ParamSpec('Papameters')
Result = TypeVar('Result')
Function = Callable[Papameters, Result]


@overload
def slot(func: Function, /) -> Function: ...

@overload
def slot(*, a: str, b: str) -> Callable[[Function], Function]: ...


def slot(function: Optional[Function] = None, /, *, how_many: Optional[Union[str, int]] = None) -> Union[Function, Callable[[Function], Function]]:
    if function is not None:
        @wraps(function)
        def decorator(*args: Papameters.args, **kwargs: Papameters.kwargs) -> Result:
            print('run! how_many =', how_many)
            return function(*args, **kwargs)

        return decorator

    else:
        return partial(slot, how_many=how_many)
