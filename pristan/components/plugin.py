from typing import Any, Generic, Type, Union
from threading import Lock

from denial import InnerNoneType
from printo import repred
from simtypes import check

from pristan.common_types import PluginFunction, PluginResult, SlotPapameters
from pristan.components.slot_code_representer import sentinel as return_type_sentinel
from pristan.errors import NumberOfCallsError


@repred(positionals=['name'])  # type: ignore[arg-type]
class Plugin(Generic[PluginResult]):
    # TODO: consider to delete this "type: ignore" if python 3.9 deleted from the matrix
    def __init__(self, name: str, plugin_function: PluginFunction[SlotPapameters, PluginResult], expected_result_type: Union[InnerNoneType, Type[Any]], type_check: bool, unique: bool, run_once: bool = False) -> None:  # type: ignore[type-arg, unused-ignore]
        self.plugin_function = plugin_function
        self.requested_name = name
        self.name = name
        self.expected_result_type = expected_result_type
        self.type_check = type_check
        self.unique = unique
        self.run_once = run_once
        self.call_count = 0
        self.lock = Lock()

    def __call__(self, *args: SlotPapameters.args, **kwargs: SlotPapameters.kwargs) -> PluginResult:
        if self.run_once:
            with self.lock:
                if self.call_count:
                    raise NumberOfCallsError(f'A limit of 1 has been set on the number of calls for plugin "{self.name}". And this plugin has already been called previously.')
                self.call_count += 1

        # TODO: try to delete this "type: ignore" comments if python 3.8 deleted from CI
        result = self.plugin_function(*args, **kwargs)  # type: ignore[arg-type, unused-ignore]

        if self.type_check and self.expected_result_type is not return_type_sentinel and not check(result, self.expected_result_type, strict=True):  # type: ignore[arg-type]
            raise TypeError(f'The type {type(result).__name__} of the plugin\'s "{self.name}" return value {result!r} does not match the expected type {self._get_class_name(self.expected_result_type)}.')  # type: ignore[union-attr, unused-ignore]

        return result  # type: ignore[no-any-return, unused-ignore]

    def set_name(self, name: str) -> None:
        self.name = name

    @staticmethod
    def _get_class_name(_type: Any) -> str:
        try:
            return _type.__name__  # type: ignore[no-any-return]
        except AttributeError:  # pragma: no cover
            return str(_type)
