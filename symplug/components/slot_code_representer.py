from functools import cached_property
from inspect import getsource
from ast import parse, Pass, Expr, Constant
from typing import List, Type, Dict, Union, Any, get_args, get_origin, get_type_hints

from dill.source import getsource as dill_getsource  # type: ignore[import-untyped]
from denial import InnerNoneType


sentinel = InnerNoneType()

class SlotCodeRepresenter:
    def __init__(self, function: Callable[..., Any]) -> None:
        self.function = function

    @cached_property
    def returns_type(self) -> Union[InnerNoneType, Type[Any]]:
        hints = get_type_hints(self.function)
        return_hint = hints.get('return', sentinel)

        if return_hint is sentinel:
            return sentinel

        elif get_origin(return_hint) is list:
            args = get_args(return_hint)
            if args:
                return args[0]
            else:
                return sentinel

        elif get_origin(return_hint) is dict:
            args = get_args(return_hint)
            if args:
                if not args[0] is str or len(args) != 2:
                    raise TypeError()
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

        elif get_origin(return_hint) is list:
            return True

        return False

    @cached_property
    def returns_dict(self) -> bool:
        hints = get_type_hints(self.function)
        return_hint = hints.get('return', sentinel)

        if return_hint is sentinel:
            return False

        elif get_origin(return_hint) is dict:
            return True

        return False

    @cached_property
    def is_empty(self) -> bool:
        try:
            source_code: str = getsource(self.function)
        except OSError:
            source_code = dill_getsource(self.function)

        converted_source_code = self._clear_spaces_from_source_code(source_code)

        tree = parse(converted_source_code)
        body = tree.body[0].body

        for body_statement in body:
            if not (isinstance(body_statement, Pass) or (isinstance(body_statement, Expr) and isinstance(body_statement.value, Constant) and (body_statement.value.value is Ellipsis or isinstance(body_statement.value.value, str)))):
                return False

        return True

    @staticmethod
    def _clear_spaces_from_source_code(source_code: str) -> str:
        splitted_source_code = source_code.split('\n')

        indent = 0
        for letter in splitted_source_code[0]:
            if letter.isspace():
                indent += 1
            else:
                break

        new_splitted_source_code = [x[indent:] for x in splitted_source_code]

        return '\n'.join(new_splitted_source_code)
