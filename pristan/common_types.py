import sys
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    overload,
)

if sys.version_info >= (3, 10):
    from typing import ParamSpec  # pragma: no cover
else:
    from typing_extensions import ParamSpec  # pragma: no cover

SlotParameters = ParamSpec('SlotParameters')

PluginResult = TypeVar('PluginResult')
SlotCallResult = TypeVar('SlotCallResult')
SlotCallResultCovariant = TypeVar('SlotCallResultCovariant', covariant=True)  # noqa: PLC0105
PluginResultCovariant = TypeVar('PluginResultCovariant', covariant=True)  # noqa: PLC0105

SlotResult = Optional[Union[List[PluginResult], Dict[str, PluginResult]]]
SlotFunction = Callable[SlotParameters, SlotCallResult]
PluginFunction = Callable[SlotParameters, PluginResult]


class PluginProtocol(Protocol[SlotParameters, PluginResultCovariant]):  # pragma: no cover
    name: str
    requested_name: str

    def __call__(self, *args: SlotParameters.args, **kwargs: SlotParameters.kwargs) -> PluginResultCovariant: ...


class BaseSlotViewProtocol(Protocol[SlotParameters, SlotCallResultCovariant, PluginResultCovariant]):  # pragma: no cover
    def __call__(self, *args: SlotParameters.args, **kwargs: SlotParameters.kwargs) -> SlotCallResultCovariant: ...

    def __iter__(self) -> Iterator[PluginProtocol[SlotParameters, PluginResultCovariant]]: ...

    def __bool__(self) -> bool: ...

    def __len__(self) -> int: ...


class SlotSelectionProtocol(BaseSlotViewProtocol[SlotParameters, SlotCallResultCovariant, PluginResultCovariant], Protocol[SlotParameters, SlotCallResultCovariant, PluginResultCovariant]):
    pass


class SlotProtocol(BaseSlotViewProtocol[SlotParameters, SlotCallResultCovariant, PluginResult], Protocol[SlotParameters, SlotCallResultCovariant, PluginResult]):  # pragma: no cover
    @overload
    def plugin(self, plugin_function_or_name: Optional[str] = None, unique: bool = False, engine: Optional[Union[List[str], str]] = None, run_once: bool = False) -> Callable[[Callable[SlotParameters, PluginResult]], Callable[SlotParameters, PluginResult]]: ...

    @overload
    def plugin(self, plugin_function_or_name: Callable[SlotParameters, PluginResult], unique: bool = False, engine: Optional[Union[List[str], str]] = None, run_once: bool = False) -> Callable[SlotParameters, PluginResult]: ...

    def keys(self) -> Tuple[str, ...]: ...

    def __getitem__(self, key: str) -> SlotSelectionProtocol[SlotParameters, SlotCallResultCovariant, PluginResult]: ...

    def __contains__(self, item: object) -> bool: ...


class SlotDecoratorProtocol(Protocol):  # pragma: no cover
    @overload
    def __call__(self, function: Callable[SlotParameters, List[PluginResult]], /) -> SlotProtocol[SlotParameters, List[PluginResult], PluginResult]: ...

    @overload
    def __call__(self, function: Callable[SlotParameters, Dict[str, PluginResult]], /) -> SlotProtocol[SlotParameters, Dict[str, PluginResult], PluginResult]: ...

    @overload
    def __call__(self, function: Callable[SlotParameters, None], /) -> SlotProtocol[SlotParameters, None, Any]: ...
