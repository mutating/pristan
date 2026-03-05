from ast import Constant, Expr, Pass, parse
from functools import cached_property
from importlib.metadata import PackageNotFoundError, version
from inspect import getmodule
from typing import (
    Any,
    Callable,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from denial import InnerNoneType
from getsources import getclearsource
from packaging.version import Version
from printo import descript_data_object

sentinel = InnerNoneType()

class SlotCodeRepresenter:
    def __init__(self, function: Callable[..., Any]) -> None:
        self.function = function
        self.returning_type  # noqa: B018

    def __repr__(self) -> str:
        return descript_data_object(type(self).__name__, [self.function], {})

    @cached_property
    def base_module(self) -> Optional[str]:
        module = getmodule(self.function)
        if module is not None:
            return module.__name__.split('.')[0]
        return None  # pragma: no cover

    @cached_property
    def package_version(self) -> Optional[Version]:
        if self.base_module is None:
            return None  # pragma: no cover
        try:
            version_identifier = version(self.base_module)
            return Version(version_identifier)
        except PackageNotFoundError:
            return None

    @cached_property
    def returning_type(self) -> Union[InnerNoneType, Type[Any]]:
        hints = get_type_hints(self.function)
        return_hint = hints.get('return', sentinel)

        if return_hint is sentinel:
            return sentinel

        if list in (return_hint, get_origin(return_hint)):
            args = get_args(return_hint)
            if args:
                return args[0]  # type: ignore[no-any-return]
            return sentinel

        if dict in (return_hint, get_origin(return_hint)):
            args = get_args(return_hint)
            if args:
                if args[0] is not str or len(args) != 2:
                    raise TypeError('Incorrect type annotation for the dict.')
                return args[1]  # type: ignore[no-any-return]
            return sentinel

        return return_hint  # type: ignore[no-any-return]

    @cached_property
    def returns_list(self) -> bool:
        hints = get_type_hints(self.function)
        return_hint = hints.get('return', sentinel)

        if return_hint is sentinel:
            return False

        return list in (return_hint, get_origin(return_hint))

    @cached_property
    def returns_dict(self) -> bool:
        hints = get_type_hints(self.function)
        return_hint = hints.get('return', sentinel)

        if return_hint is sentinel:
            return False

        return dict in (return_hint, get_origin(return_hint))

    @cached_property
    def is_empty(self) -> bool:
        converted_source_code = getclearsource(self.function)

        tree = parse(converted_source_code)
        body = tree.body[0].body  # type: ignore[attr-defined]

        for body_statement in body:
            if not (isinstance(body_statement, Pass) or (isinstance(body_statement, Expr) and isinstance(body_statement.value, Constant) and (body_statement.value.value is Ellipsis or isinstance(body_statement.value.value, str)))):
                return False

        return True
