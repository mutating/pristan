# ruff: noqa: ARG001, B015, B018, F821, F841
# mypy: warn-unused-ignores

__test__ = False

import sys
from typing import Any, Callable, Dict, List, Union

import pytest

from pristan import slot
from pristan.common_types import (
    SlotDecoratorProtocol,
    SlotProtocol,
    SlotSelectionProtocol,
)


@pytest.mark.mypy_testing
def test_slot_returns_exact_dict_type_with_typing_dict_without_parentheses():
    @slot
    def collect(value: int) -> Dict[str, int]:
        return {}

    callable_view: Callable[[int], Dict[str, int]] = collect
    slot_view: SlotProtocol[[int], Dict[str, int], int] = collect

    reveal_type(collect(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(collect.keys())  # R: builtins.tuple[builtins.str, ...]

    def consume(payload: Dict[str, int]):
        pass

    consume(collect(1))
    callable_view(1)
    slot_view(1)


@pytest.mark.mypy_testing
def test_slot_returns_exact_list_type_with_typing_list_with_parentheses():
    @slot()
    def collect(value: int) -> List[int]:
        return []

    callable_view: Callable[[int], List[int]] = collect
    slot_view: SlotProtocol[[int], List[int], int] = collect

    reveal_type(collect(1))  # R: builtins.list[builtins.int]

    def consume(payload: List[int]):
        pass

    consume(collect(1))
    callable_view(1)
    slot_view(1)


@pytest.mark.mypy_testing
def test_slot_returns_exact_list_and_dict_types_with_typing_collections_in_both_decorator_forms():
    @slot
    def collect_list(value: int) -> List[int]:
        return []

    @slot()
    def collect_dict(value: int) -> Dict[str, int]:
        return {}

    list_view: SlotProtocol[[int], List[int], int] = collect_list
    dict_view: SlotProtocol[[int], Dict[str, int], int] = collect_dict

    reveal_type(collect_list(1))  # R: builtins.list[builtins.int]
    reveal_type(collect_dict(1))  # R: builtins.dict[builtins.str, builtins.int]

    list_view(1)
    dict_view(1)


@pytest.mark.mypy_testing
def test_slot_without_return_annotation_returns_none_in_both_forms():
    @slot
    def notify(value: int):
        return None

    @slot()
    def notify_too(value: int):
        return None

    @notify.plugin
    def plugin_without_parentheses(value: int) -> str:
        return str(value)

    @notify_too.plugin()
    def plugin_with_parentheses(value: int) -> int:
        return value

    reveal_type(notify(1))  # R: Any
    reveal_type(notify_too(1))  # R: Any

    def consume(payload: Any):
        pass

    consume(notify(1))
    consume(notify_too(1))
    plugin_without_parentheses(1)
    plugin_with_parentheses(1)


@pytest.mark.mypy_testing
def test_slot_configuration_arguments_are_typed():
    @slot('some_another_slot_name')
    def slot_with_positional_name(value: int) -> List[int]:
        return []

    @slot('some_unique_slot_name', unique=True)
    def unique_slot_with_positional_name(value: int) -> List[int]:
        return []

    @slot(name='some_named_slot')
    def slot_with_keyword_name(value: int) -> Dict[str, int]:
        return {}

    @slot(unique=True)
    def unique_slot(value: int) -> List[int]:
        return []

    @slot(signature='..', max=1, type_check=False, entrypoint_group='new_namespace', unique=True)
    def configured_slot(value: int) -> List[int]:
        return []

    @slot(signature=['..', '.'])
    def configured_slot_with_signature_list(value: int, context: str = '') -> List[int]:
        return []

    reveal_type(slot_with_positional_name(1))  # R: builtins.list[builtins.int]
    reveal_type(unique_slot_with_positional_name(1))  # R: builtins.list[builtins.int]
    reveal_type(slot_with_keyword_name(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(unique_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list(1, 'context'))  # R: builtins.list[builtins.int]
    configured_slot_with_signature_list(1, 2)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_slot_direct_call_configuration_arguments_are_typed():
    """Direct-call slot overloads preserve call and plugin result types.

    The configured direct-call form accepts the same keyword options as the
    decorator-factory form, including `unique`. The assignments to
    `SlotProtocol` and the reveal checks prove that default and configured
    direct calls keep precise list and dict result types, including when a
    signature list is passed. They also distinguish the documented `Any` result
    for an unannotated slot from `None` for an explicitly annotated one.
    Iteration over slots with signature lists proves that plugin result types
    are kept as well.
    """
    def collect_list(value: int) -> List[int]:
        return []

    def collect_dict(value: int) -> Dict[str, int]:
        return {}

    def notify(value: int):
        return None

    def typed_notify(value: int) -> None:
        return None

    default_list_slot = slot(collect_list)
    list_slot = slot(collect_list, unique=True)
    signature_list_slot = slot(collect_list, signature=['.'])
    dict_slot = slot(collect_dict, signature='.', name='collect', max=2, type_check=False, entrypoint_group='custom', unique=True)
    signature_list_dict_slot = slot(collect_dict, signature=['.'])
    notify_slot = slot(notify, unique=True)
    signature_list_notify_slot = slot(typed_notify, signature=['.'])

    default_list_view: SlotProtocol[[int], List[int], int] = default_list_slot
    list_view: SlotProtocol[[int], List[int], int] = list_slot
    signature_list_view: SlotProtocol[[int], List[int], int] = signature_list_slot
    dict_view: SlotProtocol[[int], Dict[str, int], int] = dict_slot
    signature_list_dict_view: SlotProtocol[[int], Dict[str, int], int] = signature_list_dict_slot
    notify_view: SlotProtocol[[int], None, Any] = notify_slot
    signature_list_notify_view: SlotProtocol[[int], None, Any] = signature_list_notify_slot

    reveal_type(default_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(signature_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(dict_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(signature_list_dict_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(notify_slot(1))  # R: Any
    reveal_type(signature_list_notify_slot(1))  # R: None
    signature_list_slot('value')  # E: [arg-type]
    signature_list_slot()  # E: [call-arg]

    default_list_view(1)
    list_view(1)
    signature_list_view(1)
    dict_view(1)
    signature_list_dict_view(1)
    notify_view(1)
    signature_list_notify_view(1)

    for signature_list_plugin in signature_list_slot:
        reveal_type(signature_list_plugin(1))  # R: builtins.int
        signature_list_plugin('value')  # E: [arg-type]
        signature_list_plugin()  # E: [call-arg]

    for signature_list_dict_plugin in signature_list_dict_slot:
        reveal_type(signature_list_dict_plugin(1))  # R: builtins.int

    for signature_list_notify_plugin in signature_list_notify_slot:
        reveal_type(signature_list_notify_plugin(1))  # R: Any


@pytest.mark.mypy_testing
def test_plugin_decorator_variants_preserve_callable_types():
    @slot
    def collect(value: int) -> List[int]:
        return []

    @collect.plugin
    def plugin_without_parentheses(value: int) -> int:
        return value

    @collect.plugin()
    def plugin_with_parentheses(value: int) -> int:
        return value + 1

    @collect.plugin('another_plugin_name')
    def plugin_with_name(value: int) -> int:
        return value + 2

    @collect.plugin(unique=True)
    def plugin_with_unique(value: int) -> int:
        return value + 3

    @collect.plugin(engine='>1.0.0')
    def plugin_with_engine_string(value: int) -> int:
        return value + 4

    @collect.plugin(engine=['>1.0.0', '<2.0.0'])
    def plugin_with_engine_list(value: int) -> int:
        return value + 5

    @collect.plugin(run_once=True)
    def plugin_with_run_once(value: int) -> int:
        return value + 6

    callable_1: Callable[[int], int] = plugin_without_parentheses
    callable_2: Callable[[int], int] = plugin_with_parentheses
    callable_3: Callable[[int], int] = plugin_with_name
    callable_4: Callable[[int], int] = plugin_with_unique
    callable_5: Callable[[int], int] = plugin_with_engine_string
    callable_6: Callable[[int], int] = plugin_with_engine_list
    callable_7: Callable[[int], int] = plugin_with_run_once

    reveal_type(collect.keys())  # R: builtins.tuple[builtins.str, ...]

    callable_1(1)
    callable_2(1)
    callable_3(1)
    callable_4(1)
    callable_5(1)
    callable_6(1)
    callable_7(1)


@pytest.mark.mypy_testing
def test_slot_selection_has_narrower_public_type():
    @slot
    def collect(value: int) -> List[int]:
        return []

    selection = collect['name']
    selection_view: SlotSelectionProtocol[[int], List[int], int] = selection
    callable_view: Callable[[int], List[int]] = selection

    reveal_type(selection(1))  # R: builtins.list[builtins.int]
    reveal_type(collect.keys())  # R: builtins.tuple[builtins.str, ...]

    length: int = len(selection)
    slot_length: int = len(collect)
    has_plugin_name: bool = 'name' in collect

    for plugin in collect:
        name: str = plugin.name

    selection_view(1)
    callable_view(1)
    slot_length
    has_plugin_name


@pytest.mark.mypy_testing
def test_non_existent_slot_selection_keeps_slot_call_contract():
    @slot
    def collect(value: int) -> Dict[str, int]:
        return {}

    selection = collect['non_existent_key']
    selection_view: SlotSelectionProtocol[[int], Dict[str, int], int] = selection
    callable_view: Callable[[int], Dict[str, int]] = selection

    reveal_type(selection(1))  # R: builtins.dict[builtins.str, builtins.int]

    def consume(payload: Dict[str, int]):
        pass

    consume(selection(1))
    selection_view(1)
    callable_view(1)


@pytest.mark.mypy_testing
def test_slot_pop_returns_selection_type():
    @slot
    def collect_list(value: int) -> List[int]:
        return []

    @slot
    def collect_dict(value: int) -> Dict[str, int]:
        return {}

    popped_list = collect_list.pop('name')
    popped_dict = collect_dict.pop('name')

    popped_list_view: SlotSelectionProtocol[[int], List[int], int] = popped_list
    popped_dict_view: SlotSelectionProtocol[[int], Dict[str, int], int] = popped_dict

    reveal_type(popped_list(1))  # R: builtins.list[builtins.int]
    reveal_type(popped_dict(1))  # R: builtins.dict[builtins.str, builtins.int]

    del collect_list['name']
    popped_list_view(1)
    popped_dict_view(1)


@pytest.mark.mypy_testing
def test_slot_pop_with_default_returns_union():
    @slot
    def collect(value: int) -> List[int]:
        return []

    popped_or_text: Union[SlotSelectionProtocol[[int], List[int], int], str] = collect.pop('name', 'fallback')
    popped_or_number: Union[SlotSelectionProtocol[[int], List[int], int], int] = collect.pop('name', 1)

    reveal_type(collect.pop('name', 'fallback'))  # R: Union[pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int], builtins.str]


@pytest.mark.mypy_testing
def test_iterated_plugins_preserve_slot_parameter_types():
    @slot
    def collect(value: int) -> List[int]:
        return []

    @collect.plugin
    def plugin(value: int) -> int:
        return value

    for loaded_plugin in collect:
        callable_view: Callable[[int], int] = loaded_plugin
        reveal_type(loaded_plugin(1))  # R: builtins.int
        loaded_plugin('wrong')  # E: [arg-type]

        callable_view(1)


@pytest.mark.mypy_testing
def test_plugin_argument_validation_is_typed():
    @slot
    def collect(value: int) -> List[int]:
        return []

    collect.plugin(engine=[1])  # E: [list-item]
    collect.plugin('named', engine=[1])  # E: [list-item]
    collect.plugin(engine=['>1.0.0', 1])  # E: [list-item]


@pytest.mark.mypy_testing
def test_slot_bad_factory_arguments_stay_type_errors():
    """Pin invalid slot(...) calls via code-specific expectations.

    Calls producing bundled overload diagnostics use targeted ignores together
    with warn-unused-ignores. Calls with a single precise diagnostic use inline
    expected-error annotations. Either form fails if an invalid call becomes
    accepted.
    """
    slot(1)  # type: ignore[call-overload]
    slot(name=1)  # type: ignore[call-overload]
    slot(signature=1)  # type: ignore[call-overload]
    slot(signature=[1])  # E: [list-item]
    slot(signature=('.',))  # type: ignore[call-overload]
    slot(max='1')  # type: ignore[call-overload]
    slot(type_check='yes')  # type: ignore[call-overload]
    slot(entrypoint_group=None)  # type: ignore[call-overload]
    slot(unique='yes')  # type: ignore[call-overload]

    def collect(value: int) -> List[int]:
        return []

    slot(collect, unique='yes')  # type: ignore[call-overload]
    slot(collect, signature=[1])  # E: [list-item]
    slot(collect, signature=('.',))  # type: ignore[call-overload]


@pytest.mark.mypy_testing
def test_plugin_bad_factory_arguments_stay_type_errors():
    """Pin invalid slot.plugin(...) calls via code-specific ignores.

    The fragility is the same as for slot(...): mypy emits an overload error
    together with several note lines on the same source line, and the plugin
    cannot model all of them inline. Specific ignores plus warn-unused-ignores
    let us assert that these calls must remain invalid.
    """

    @slot
    def collect(value: int) -> List[int]:
        return []

    collect.plugin(1)  # type: ignore[call-overload]
    collect.plugin(unique='yes')  # type: ignore[call-overload]
    collect.plugin(engine=1)  # type: ignore[call-overload]
    collect.plugin(run_once='yes')  # type: ignore[call-overload]


@pytest.mark.mypy_testing
def test_slot_factory_results_are_typed_as_slot_decorators():
    bare_factory: SlotDecoratorProtocol = slot()
    named_factory: SlotDecoratorProtocol = slot('named_slot')
    keyword_named_factory: SlotDecoratorProtocol = slot(name='other_named_slot')

    @bare_factory
    def collect_with_bare_factory(value: int) -> List[int]:
        return []

    @named_factory
    def collect_with_named_factory(value: int) -> Dict[str, int]:
        return {}

    @keyword_named_factory
    def collect_with_keyword_named_factory(value: int) -> List[int]:
        return []

    reveal_type(collect_with_bare_factory(1))  # R: builtins.list[builtins.int]
    reveal_type(collect_with_named_factory(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(collect_with_keyword_named_factory(1))  # R: builtins.list[builtins.int]


@pytest.mark.mypy_testing
def test_slot_selection_is_not_assignable_to_full_slot_protocol():
    @slot
    def collect(value: int) -> List[int]:
        return []

    full_slot: SlotProtocol[[int], List[int], int] = collect['name']  # E: [assignment]


@pytest.mark.mypy_testing
def test_exact_result_type_is_not_widened_for_typing_collections():
    @slot
    def collect_list(value: int) -> List[int]:
        return []

    @slot
    def collect_dict(value: int) -> Dict[str, int]:
        return {}

    def consume_list(payload: List[int]):
        pass

    def consume_dict(payload: Dict[str, int]):
        pass

    consume_dict(collect_list(1))  # E: [arg-type]
    consume_list(collect_dict(1))  # E: [arg-type]
    consume_dict(collect_list['name'](1))  # E: [arg-type]


@pytest.mark.mypy_testing
def test_plugin_return_type_mismatch_is_reported_for_typing_collections():
    @slot
    def collect_list(value: int) -> List[int]:
        return []

    @collect_list.plugin  # E: [arg-type]
    def bad_list_plugin(value: int) -> str:
        return str(value)

    @slot
    def collect_dict(value: int) -> Dict[str, int]:
        return {}

    @collect_dict.plugin()  # E: [arg-type]
    def bad_dict_plugin(value: int) -> str:
        return str(value)


@pytest.mark.mypy_testing
def test_selection_does_not_expose_full_slot_api():
    @slot
    def collect(value: int) -> List[int]:
        return []

    selection = collect['name']

    selection.plugin('name')  # E: [attr-defined]
    selection.keys()  # E: [attr-defined]
    selection['nested']  # E: [index]
    'name' in selection  # E: [operator]


@pytest.mark.mypy_testing
def test_popped_selection_does_not_expose_full_slot_api():
    @slot
    def collect(value: int) -> List[int]:
        return []

    popped = collect.pop('name')

    popped.plugin('name')  # E: [attr-defined]
    popped.keys()  # E: [attr-defined]
    popped['nested']  # E: [index]
    'name' in popped  # E: [operator]


@pytest.mark.mypy_testing
def test_collection_api_reports_wrong_argument_types():
    @slot
    def collect(value: int) -> List[int]:
        return []

    collect.keys(1)  # E: [call-arg]
    collect[1]  # E: [index]
    collect.pop(1)  # type: ignore[call-overload]
    collect.pop()  # type: ignore[call-overload]
    collect.pop('name', 1, 2)  # type: ignore[call-overload]
    del collect[1]  # E: [arg-type]

    keys_as_list: List[str] = collect.keys()  # E: [assignment]
    wrong_selection: int = collect['name']  # E: [assignment]
    wrong_popped_selection: int = collect.pop('name')  # E: [assignment]


@pytest.mark.mypy_testing
def test_slot_with_loose_list_and_dict_annotations_keeps_any_payload_type():
    @slot
    def collect_list() -> list:
        return []

    @slot
    def collect_dict() -> dict:
        return {}

    @collect_list.plugin
    def list_plugin() -> str:
        return 'value'

    @collect_dict.plugin
    def dict_plugin() -> str:
        return 'value'

    reveal_type(collect_list())  # R: builtins.list[Any]
    reveal_type(collect_dict())  # R: builtins.dict[builtins.str, Any]


@pytest.mark.mypy_testing
def test_decorated_plugin_type_is_not_widened():
    @slot
    def collect(value: int) -> List[int]:
        return []

    @collect.plugin
    def plugin_without_parentheses(value: int) -> int:
        return value

    @collect.plugin()
    def plugin_with_parentheses(value: int) -> int:
        return value + 1

    wrong_1: Callable[[int], str] = plugin_without_parentheses  # E: [assignment]
    wrong_2: Callable[[int], str] = plugin_with_parentheses  # E: [assignment]


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_slot_returns_exact_dict_and_list_types_with_built_in_generics():
    @slot
    def collect_dict(value: int) -> dict[str, int]:
        return {}

    @slot()
    def collect_list(value: int) -> list[int]:
        return []

    callable_dict: Callable[[int], dict[str, int]] = collect_dict
    callable_list: Callable[[int], list[int]] = collect_list
    slot_dict: SlotProtocol[[int], dict[str, int], int] = collect_dict
    slot_list: SlotProtocol[[int], list[int], int] = collect_list
    selection: SlotSelectionProtocol[[int], list[int], int] = collect_list['name']

    reveal_type(collect_dict(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(collect_list(1))  # R: builtins.list[builtins.int]
    reveal_type(collect_list['name'](1))  # R: builtins.list[builtins.int]

    def consume_dict(payload: dict[str, int]):
        pass

    def consume_list(payload: list[int]):
        pass

    consume_dict(collect_dict(1))
    consume_list(collect_list(1))
    callable_dict(1)
    callable_list(1)
    slot_dict(1)
    slot_list(1)
    selection(1)


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_slot_returns_exact_list_and_dict_types_with_built_in_generics_in_both_decorator_forms():
    @slot
    def collect_list(value: int) -> list[int]:
        return []

    @slot()
    def collect_dict(value: int) -> dict[str, int]:
        return {}

    list_view: SlotProtocol[[int], list[int], int] = collect_list
    dict_view: SlotProtocol[[int], dict[str, int], int] = collect_dict

    reveal_type(collect_list(1))  # R: builtins.list[builtins.int]
    reveal_type(collect_dict(1))  # R: builtins.dict[builtins.str, builtins.int]

    list_view(1)
    dict_view(1)


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_built_in_generic_results_are_not_widened():
    @slot
    def collect_list(value: int) -> list[int]:
        return []

    @slot
    def collect_dict(value: int) -> dict[str, int]:
        return {}

    def consume_list(payload: list[int]):
        pass

    def consume_dict(payload: dict[str, int]):
        pass

    consume_dict(collect_list(1))  # E: [arg-type]
    consume_list(collect_dict(1))  # E: [arg-type]
    consume_dict(collect_list['name'](1))  # E: [arg-type]


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_slot_pop_returns_selection_type_for_built_in_generics():
    @slot
    def collect(value: int) -> list[int]:
        return []

    popped = collect.pop('name')
    popped_or_text: Union[SlotSelectionProtocol[[int], list[int], int], str] = collect.pop('name', 'fallback')

    reveal_type(popped(1))  # R: builtins.list[builtins.int]

    del collect['name']


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_plugin_return_type_mismatch_is_reported_for_built_in_generics():
    @slot
    def collect_list(value: int) -> list[int]:
        return []

    @collect_list.plugin  # E: [arg-type]
    def bad_list_plugin(value: int) -> str:
        return str(value)

    @slot
    def collect_dict(value: int) -> dict[str, int]:
        return {}

    @collect_dict.plugin(run_once=True)  # E: [arg-type]
    def bad_dict_plugin(value: int) -> str:
        return str(value)
