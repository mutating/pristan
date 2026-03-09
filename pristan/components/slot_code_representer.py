from ast import Constant, Expr, Pass, Return, parse
from ast import Dict as ASTDict
from ast import List as ASTList
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

from pristan.errors import CannotGetVersionsError


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

        return all(
            (
                isinstance(body_statement, Pass) or (isinstance(body_statement, Expr) and isinstance(body_statement.value, Constant) and (body_statement.value.value is Ellipsis or isinstance(body_statement.value.value, str)))
                for body_statement in body
            ),
        ) or (
            len(body) == 1 and isinstance(body[0], Return)
            and (
                (self.returns_list and isinstance(body[0].value, ASTList) and not body[0].value.elts)
                or ((self.returns_dict and isinstance(body[0].value, ASTDict) and not body[0].value.keys and not body[0].value.values))
            )
        )

    def check_package_version(self, expression: Optional[str]) -> bool:
        if expression is None:
            return True

        if self.package_version is None:
            raise CannotGetVersionsError('It is not possible to obtain the name of the package in which the slot is declared.')

        expression = expression.strip()

        start_signs = {
            '==': lambda x: self.package_version == Version(x),
            '>=': lambda x: self.package_version >= Version(x),
            '<=': lambda x: self.package_version <= Version(x),
            '>': lambda x: self.package_version > Version(x),
            '<': lambda x: self.package_version < Version(x),
        }

        for start in start_signs:
            if expression.startswith(start):
                if start_signs[start](expression[len(start):]):
                    return True

        return False
