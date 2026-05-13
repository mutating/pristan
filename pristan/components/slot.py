try:
    from importlib_metadata import (  # type: ignore[import-not-found, unused-ignore]
        entry_points,
    )
except ImportError:  # pragma: no cover
    from importlib.metadata import (  # type: ignore[assignment, unused-ignore]
        entry_points,
    )

from threading import RLock
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from denial import InnerNoneType
from printo import not_none, repred
from sigmatch import PossibleCallMatcher
from sigmatch.errors import SignatureMismatchError

from pristan.common_types import (
    PluginFunction,
    PluginProtocol,
    PluginResult,
    SlotFunction,
    SlotParameters,
    SlotResult,
)
from pristan.components.plugin import Plugin
from pristan.components.plugins_group import PluginsGroup
from pristan.components.slot_caller import CallerWithPlugins, SlotCaller
from pristan.components.slot_code_representer import SlotCodeRepresenter
from pristan.components.slot_code_representer import sentinel as return_type_sentinel
from pristan.errors import (
    PrimadonnaPluginError,
    StrangeTypeAnnotationError,
    TooManyPluginsError,
)

DefaultType = TypeVar('DefaultType')
pop_default_sentinel = InnerNoneType()


# TODO: consider to delete all the "type: ignore"d comments if python 3.9 deleted from the matrix
@repred(
    positionals=['slot_function'],
    filters={
        'signature': not_none,
        'slot_name': not_none,
        'max': not_none,
        'type_check': lambda x: x != True,
        'entrypoint_group': lambda x: x != 'pristan',
    },
)
class Slot(Generic[PluginResult]):
    def __init__(self, slot_function: SlotFunction[SlotParameters, SlotResult[PluginResult]], signature: Optional[str], slot_name: Optional[str], max: Optional[int], type_check: bool, entrypoint_group: str) -> None:  # noqa: PLR0913, A002
        if max is not None and max < 0:
            raise ValueError('The maximum number of plugins cannot be less than zero.')

        self.slot_function = slot_function
        self.code_representation = SlotCodeRepresenter(self.slot_function)

        if not self.code_representation.returns_list and not self.code_representation.returns_dict and self.code_representation.returning_type is not return_type_sentinel:
            raise StrangeTypeAnnotationError('The return type annotation for a slot must be either a list or a dict, or remain empty.')

        self.signature = signature
        self.slot_name = slot_name
        self.slot_function = slot_function
        self.max_number_of_plugins = max
        self.type_check = type_check
        self.entrypoint_group = entrypoint_group

        self.lock = RLock()

        self.caller: SlotCaller[PluginResult] = SlotCaller(self.code_representation, self.slot_name, self.slot_function, self.type_check)
        self.plugins: PluginsGroup[PluginResult] = PluginsGroup(self.caller)
        self.backed_caller = CallerWithPlugins(self.caller, self.plugins.plugins)

        self._compare_signatures(self.slot_function, self.slot_function)  # type: ignore[arg-type]

        self.loaded = False

    def __call__(self, *args: SlotParameters.args, **kwargs: SlotParameters.kwargs) -> SlotResult[PluginResult]:
        self._load_entrypoints()
        return self.backed_caller(*args, **kwargs)

    def __iter__(self) -> Generator[PluginProtocol[SlotParameters, PluginResult], None, None]:
        self._load_entrypoints()
        yield from self.plugins

    def __getitem__(self, key: str) -> CallerWithPlugins[PluginResult]:
        self._load_entrypoints()
        return self.plugins[key]  # type: ignore[no-any-return]

    def __delitem__(self, key: str) -> None:
        self._pop_plugins(key)

    def __contains__(self, item: Any) -> bool:
        return item in self.plugins

    def __len__(self) -> int:
        return len(self.plugins)

    @overload
    def pop(self, key: str) -> CallerWithPlugins[PluginResult]:
        ...  # pragma: no cover

    @overload
    def pop(self, key: str, default: DefaultType) -> Union[CallerWithPlugins[PluginResult], DefaultType]:
        ...  # pragma: no cover

    def pop(self, key: str, default: Any = pop_default_sentinel) -> Any:
        try:
            removed_plugins = self._pop_plugins(key)
        except KeyError:
            if default is pop_default_sentinel:
                raise
            return default

        return CallerWithPlugins(self.caller, removed_plugins)

    def _pop_plugins(self, key: str) -> List[Plugin[PluginResult]]:
        self._load_entrypoints()
        with self.lock:
            return self.plugins.pop(key)

    @overload
    def plugin(self, plugin_function_or_name: Optional[str] = None, unique: bool = False, engine: Optional[Union[List[str], str]] = None, run_once: bool = False) -> Callable[[Callable[SlotParameters, PluginResult]], Callable[SlotParameters, PluginResult]]:
        ...  # pragma: no cover

    @overload
    def plugin(self, plugin_function_or_name: Callable[SlotParameters, PluginResult], unique: bool = False, engine: Optional[Union[List[str], str]] = None, run_once: bool = False) -> Callable[SlotParameters, PluginResult]: ...  # pragma: no cover

    def plugin(self, plugin_function_or_name: Optional[Union[PluginFunction[SlotParameters, PluginResult], str]] = None, unique: bool = False, engine: Optional[Union[List[str], str]] = None, run_once: bool = False) -> Union[Callable[[Callable[SlotParameters, PluginResult]], Callable[SlotParameters, PluginResult]], Callable[SlotParameters, PluginResult]]:
        if isinstance(plugin_function_or_name, str):
            if not plugin_function_or_name.isidentifier():
                raise ValueError('The plugin name must be a valid Python identifier.')
            get_plugin_name: Callable[[PluginFunction[SlotParameters, PluginResult]], str] = lambda function: plugin_function_or_name  # noqa: E731, ARG005

        elif callable(plugin_function_or_name):
            get_plugin_name = lambda function: plugin_function_or_name.__name__  # noqa: E731, ARG005

        elif plugin_function_or_name is None:
            get_plugin_name = lambda function: function.__name__  # noqa: E731

        else:
            raise TypeError('Only a function or plugin name followed by a function can be passed to the decorator.')

        def decorator(plugin_function: Callable[SlotParameters, PluginResult]) -> Callable[SlotParameters, PluginResult]:
            # TODO: consider to delete this "type: ignore" if python 3.8 deleted from the matrix
            self._compare_signatures(self.slot_function, plugin_function)  # type: ignore[arg-type]
            self._add_plugin(get_plugin_name(plugin_function), plugin_function, unique, engine, run_once)
            return plugin_function

        if plugin_function_or_name is None or isinstance(plugin_function_or_name, str):
            return decorator

        return decorator(plugin_function_or_name)

    def keys(self) -> Tuple[str, ...]:
        self._load_entrypoints()
        return tuple(self.plugins.plugins_by_requested_names.keys())

    def _load_entrypoints(self) -> None:
        with self.lock:
            if not self.loaded:
                for point in entry_points(group=self.entrypoint_group):
                    point.load()
                self.loaded = True

    def _add_plugin(self, name: str, function: PluginFunction[SlotParameters, PluginResult], unique: bool, engine: Optional[Union[str, List[str]]], run_once: bool) -> None:
        plugin: Plugin[PluginResult] = Plugin(name, function, self.code_representation.returning_type, self.type_check, unique, run_once)

        with self.lock:
            if len(self.plugins) == self.max_number_of_plugins:
                raise TooManyPluginsError(f'The maximum number of plugins for this slot is {self.max_number_of_plugins}.')

            if self.code_representation.check_package_version(engine):
                self.plugins.add(plugin)
                if len(self.plugins.plugins_by_requested_names[name]) > 1:
                    plugin.set_name(f'{name}-{len(self.plugins.plugins_by_requested_names[name])}')
                    for other_plugin in self.plugins.plugins_by_requested_names[name]:
                        if other_plugin.unique:
                            self.plugins.delete_last_by_name(name)
                            raise PrimadonnaPluginError(f'Plugin "{other_plugin.name}" claims to be unique, but there are other plugins with the same name.')

    def _compare_signatures(self, slot_function: SlotFunction[SlotParameters, SlotResult[PluginResult]], plugin_function: PluginFunction[SlotParameters, PluginResult]) -> None:
        if self.signature is not None:
            PossibleCallMatcher(self.signature).match(plugin_function, raise_exception=True)
        elif not PossibleCallMatcher.from_callable(slot_function) & PossibleCallMatcher.from_callable(plugin_function):
            raise SignatureMismatchError('No common calling method has been found between the slot and the plugin.')
