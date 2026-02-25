from functools import cached_property
from inspect import getsource, getmodule
from ast import parse, Pass, Expr, Constant
from typing import Type, Union, Any, Optional, get_args, get_origin, get_type_hints
from importlib.metadata import version, PackageNotFoundError

from getsources import getclearsource
from denial import InnerNoneType
from packaging.version import Version


sentinel = InnerNoneType()

class SlotCodeRepresenter:
    def __init__(self, function: Callable[..., Any]) -> None:
        self.function = function

    @cached_property
    def base_module(self) -> str:
        return getmodule(self.function).__name__.split('.')[0]

    @cached_property
    def package_version(self) -> Optional[Version]:
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

        elif list in (return_hint, get_origin(return_hint)):
            args = get_args(return_hint)
            if args:
                return args[0]
            else:
                return sentinel

        elif dict in (return_hint, get_origin(return_hint)):
            args = get_args(return_hint)
            if args:
                if not args[0] is str or len(args) != 2:
                    raise TypeError('Incorrect type annotation for the dict.')
                return args[1]
            else:
                return sentinel

        return return_hint

    @cached_property
    def returns_list(self) -> bool:
        hints = get_type_hints(self.function)
        return_hint = hints.get('return', sentinel)

        if return_hint is sentinel:
            return False

        elif list in (return_hint, get_origin(return_hint)):
            return True

        return False

    @cached_property
    def returns_dict(self) -> bool:
        hints = get_type_hints(self.function)
        return_hint = hints.get('return', sentinel)

        if return_hint is sentinel:
            return False

        elif dict in (return_hint, get_origin(return_hint)):
            return True

        return False

    @cached_property
    def is_empty(self) -> bool:
        converted_source_code = getclearsource(self.function)

        tree = parse(converted_source_code)
        body = tree.body[0].body

        for body_statement in body:
            if not (isinstance(body_statement, Pass) or (isinstance(body_statement, Expr) and isinstance(body_statement.value, Constant) and (body_statement.value.value is Ellipsis or isinstance(body_statement.value.value, str)))):
                return False

        return True
