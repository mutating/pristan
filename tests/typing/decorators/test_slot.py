# mypy: warn-unused-ignores

import sys
from typing import Any, Callable, Dict, List

import pytest
from typing_extensions import reveal_type

from pristan import slot
from pristan.common_types import (
    SlotDecoratorProtocol,
    SlotProtocol,
    SlotSelectionProtocol,
)
from pristan.errors import CannotGetVersionsError, StrangeTypeAnnotationError


@pytest.mark.mypy_testing
def test_typing_collection_result_matrix_preserves_exact_slot_types():
    """Explicitly cover decorator and typing collection combinations.

    `pytest-mypy-testing` checks this source statically, so pytest fixtures such
    as `folder_slot`, `list_type`, and `dict_type` would not create typed mypy
    variants. Keeping the matrix in one function preserves the `@slot`/`@slot()`
    and `List`/`Dict` coverage without duplicating separate mypy items.
    """
    @slot
    def bare_list_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot
    def bare_dictionary_slot(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    @slot()
    def factory_list_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot()
    def factory_dictionary_slot(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    reveal_type(bare_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(bare_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(factory_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(factory_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(bare_dictionary_slot.keys())  # R: builtins.tuple[builtins.str, ...]
    reveal_type(factory_dictionary_slot.keys())  # R: builtins.tuple[builtins.str, ...]


@pytest.mark.mypy_testing
def test_slot_without_return_annotation_is_typed_as_any_in_both_forms():
    """Unannotated slots keep Any call results in both decorator forms.

    The reveal checks cover `@slot` and `@slot()`, while the plugin calls keep
    both plugin decorator forms runnable at runtime.
    """
    @slot
    def notify(value: int):  # noqa: ARG001
        return None

    @slot()
    def notify_too(value: int):  # noqa: ARG001
        return None

    @notify.plugin
    def plugin_without_parentheses(value: int) -> str:
        return str(value)

    @notify_too.plugin()
    def plugin_with_parentheses(value: int) -> int:
        return value

    reveal_type(notify(1))  # R: Any
    reveal_type(notify_too(1))  # R: Any

    plugin_without_parentheses(1)
    plugin_with_parentheses(1)


@pytest.mark.mypy_testing
def test_slot_configuration_arguments_include_explicit_plugin_names():
    @slot('some_another_slot_name')
    def slot_with_positional_name(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot('some_unique_slot_name', unique=True)
    def unique_slot_with_positional_name(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot(name='some_named_slot')
    def slot_with_keyword_name(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    @slot(unique=True)
    def unique_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot(explicit_plugin_names=True)
    def explicit_plugin_names_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot(signature='.', max=1, type_check=False, entrypoint_group='new_namespace', unique=True)
    def configured_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot(signature=['..', '.'])
    def configured_slot_with_signature_list(value: int, context: str = '') -> List[int]:  # noqa: ARG001
        return []

    reveal_type(slot_with_positional_name(1))  # R: builtins.list[builtins.int]
    reveal_type(unique_slot_with_positional_name(1))  # R: builtins.list[builtins.int]
    reveal_type(slot_with_keyword_name(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(unique_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(explicit_plugin_names_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list(1, 'context'))  # R: builtins.list[builtins.int]
    configured_slot_with_signature_list(1, 2)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_slot_direct_call_configuration_arguments_include_explicit_plugin_names():
    """Direct-call slot overloads preserve call and plugin result types.

    The configured direct-call form accepts the same keyword options as the
    decorator-factory form, including `unique` and `explicit_plugin_names`.
    Assignments and reveal checks cover default and configured direct calls,
    signature strings and lists, custom options, precise list and dict results,
    and the unannotated `Any` result. The `typed_notify` block keeps the static
    `None` expectation covered while documenting the current runtime
    `StrangeTypeAnnotationError`. Iteration over slots with signature lists
    proves that plugin result types are kept as well.
    """
    def collect_list(value: int) -> List[int]:  # noqa: ARG001
        return []

    def collect_dict(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    def notify(value: int):  # noqa: ARG001
        return None

    def typed_notify(value: int) -> None:  # noqa: ARG001
        return None

    default_list_slot = slot(collect_list)
    list_slot = slot(collect_list, unique=True, explicit_plugin_names=True)
    signature_list_slot = slot(collect_list, signature=['.'])
    dict_slot = slot(collect_dict, signature='.', name='collect', max=2, type_check=False, entrypoint_group='custom', unique=True)
    signature_list_dict_slot = slot(collect_dict, signature=['.'])
    notify_slot = slot(notify, unique=True)

    with pytest.raises(StrangeTypeAnnotationError):  # noqa: PT012
        signature_list_notify_slot = slot(typed_notify, signature=['.'])
        signature_list_notify_view: SlotProtocol[[int], None, Any] = signature_list_notify_slot
        reveal_type(signature_list_notify_slot(1))  # R: None
        signature_list_notify_view(1)

        for signature_list_notify_plugin in signature_list_notify_slot:
            reveal_type(signature_list_notify_plugin(1))  # R: Any

    default_list_view: SlotProtocol[[int], List[int], int] = default_list_slot
    list_view: SlotProtocol[[int], List[int], int] = list_slot
    signature_list_view: SlotProtocol[[int], List[int], int] = signature_list_slot
    dict_view: SlotProtocol[[int], Dict[str, int], int] = dict_slot
    signature_list_dict_view: SlotProtocol[[int], Dict[str, int], int] = signature_list_dict_slot
    notify_view: SlotProtocol[[int], None, Any] = notify_slot

    reveal_type(default_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(signature_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(dict_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(signature_list_dict_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(notify_slot(1))  # R: Any

    signature_list_slot('value')  # E: [arg-type]
    signature_list_slot()  # E: [call-arg]

    default_list_view(1)
    list_view(1)
    signature_list_view(1)
    dict_view(1)
    signature_list_dict_view(1)
    notify_view(1)

    for signature_list_plugin in signature_list_slot:
        reveal_type(signature_list_plugin(1))  # R: builtins.int
        with pytest.raises(TypeError):
            signature_list_plugin('value')  # E: [arg-type]
        with pytest.raises(TypeError):
            signature_list_plugin()  # E: [call-arg]

    for signature_list_dict_plugin in signature_list_dict_slot:
        reveal_type(signature_list_dict_plugin(1))  # R: builtins.int


@pytest.mark.mypy_testing
def test_plugin_decorator_variants_preserve_callable_types():
    """Plugin decorator overload forms return the original callable type.

    Successful variants cover bare, parenthesized, named, unique, and run-once
    decorators. Engine-constrained forms stay inside `pytest.raises` because
    version discovery raises in this test environment.
    """
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    @collect.plugin
    def plugin_without_parentheses(value: int) -> int:
        return value

    @collect.plugin()
    def plugin_with_parentheses(value: int) -> int:
        return value

    @collect.plugin('another_plugin_name')
    def plugin_with_name(value: int) -> int:
        return value

    @collect.plugin(unique=True)
    def plugin_with_unique(value: int) -> int:
        return value

    with pytest.raises(CannotGetVersionsError):
        collect.plugin(engine='>1.0.0')(plugin_with_parentheses)

    with pytest.raises(CannotGetVersionsError):
        collect.plugin(engine=['>1.0.0', '<2.0.0'])(plugin_with_parentheses)

    @collect.plugin(run_once=True)
    def plugin_with_run_once(value: int) -> int:
        return value

    plugin_callables: List[Callable[[int], int]] = [
        plugin_without_parentheses,
        plugin_with_parentheses,
        plugin_with_name,
        plugin_with_unique,
        plugin_with_run_once,
    ]

    for plugin_callable in plugin_callables:
        plugin_callable(1)


@pytest.mark.mypy_testing
def test_slot_selection_has_narrower_public_type():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    selection = collect['name']
    selection_view: SlotSelectionProtocol[[int], List[int], int] = selection
    callable_view: Callable[[int], List[int]] = selection

    reveal_type(selection(1))  # R: builtins.list[builtins.int]
    reveal_type(collect.keys())  # R: builtins.tuple[builtins.str, ...]
    reveal_type(len(selection))  # R: builtins.int
    reveal_type(len(collect))  # R: builtins.int
    reveal_type('name' in collect)  # R: builtins.bool

    for plugin in collect:
        reveal_type(plugin.name)  # R: builtins.str

    selection_view(1)
    callable_view(1)


@pytest.mark.mypy_testing
def test_non_existent_slot_selection_keeps_slot_call_contract():
    @slot
    def collect(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    selection = collect['non_existent_key']
    selection_view: SlotSelectionProtocol[[int], Dict[str, int], int] = selection
    callable_view: Callable[[int], Dict[str, int]] = selection

    reveal_type(selection(1))  # R: builtins.dict[builtins.str, builtins.int]

    selection_view(1)
    callable_view(1)


@pytest.mark.mypy_testing
def test_slot_pop_returns_selection_type():
    @slot
    def collect_list(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot
    def collect_dict(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    @collect_list.plugin('name')
    def list_plugin(value: int) -> int:
        return value

    @collect_dict.plugin('name')
    def dict_plugin(value: int) -> int:
        return value

    popped_list = collect_list.pop('name')
    popped_dict = collect_dict.pop('name')

    popped_list_view: SlotSelectionProtocol[[int], List[int], int] = popped_list
    popped_dict_view: SlotSelectionProtocol[[int], Dict[str, int], int] = popped_dict

    reveal_type(popped_list(1))  # R: builtins.list[builtins.int]
    reveal_type(popped_dict(1))  # R: builtins.dict[builtins.str, builtins.int]

    popped_list_view(1)
    popped_dict_view(1)


@pytest.mark.mypy_testing
def test_slot_pop_with_default_returns_union():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    reveal_type(collect.pop('name', 'fallback'))  # R: Union[pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int], builtins.str]
    reveal_type(collect.pop('name', 1))  # R: Union[pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int], builtins.int]


@pytest.mark.mypy_testing
def test_slot_and_selection_bool_methods_are_typed():
    """Slot protocols and returned selections expose __bool__ as bool.

    The slot construction forms are listed explicitly because mypy sees only
    this source file. Pytest fixtures such as `folder_slot` would not create
    separate static variants for `@slot`, `@slot()`, configured decorators, and
    direct calls.
    """
    @slot
    def bare_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot()
    def factory_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot(name='keyword')
    def keyword_slot(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    @slot('positional')
    def positional_slot(value: int) -> List[int]:  # noqa: ARG001
        return []

    def direct_function(value: int) -> List[int]:  # noqa: ARG001
        return []

    @bare_slot.plugin('name')
    def bare_plugin(value: int) -> int:
        return value

    selection = bare_slot['name']
    popped = bare_slot.pop('name')
    slot_view: SlotProtocol[[int], List[int], int] = bare_slot
    selection_view: SlotSelectionProtocol[[int], List[int], int] = selection

    reveal_type(bare_slot.__bool__())  # R: builtins.bool
    reveal_type(factory_slot.__bool__())  # R: builtins.bool
    reveal_type(keyword_slot.__bool__())  # R: builtins.bool
    reveal_type(positional_slot.__bool__())  # R: builtins.bool
    reveal_type(slot(direct_function).__bool__())  # R: builtins.bool
    reveal_type(slot(direct_function, name='direct').__bool__())  # R: builtins.bool
    reveal_type(slot_view.__bool__())  # R: builtins.bool
    reveal_type(selection.__bool__())  # R: builtins.bool
    reveal_type(selection_view.__bool__())  # R: builtins.bool
    reveal_type(popped.__bool__())  # R: builtins.bool


@pytest.mark.mypy_testing
def test_iterated_plugins_preserve_slot_parameter_types():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    @collect.plugin
    def plugin(value: int) -> int:
        return value

    for loaded_plugin in collect:
        callable_view: Callable[[int], int] = loaded_plugin
        reveal_type(loaded_plugin(1))  # R: builtins.int
        with pytest.raises(TypeError):
            loaded_plugin('wrong')  # E: [arg-type]

        callable_view(1)


@pytest.mark.mypy_testing
def test_plugin_argument_validation_is_typed():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    collect.plugin(engine=[1])  # E: [list-item]
    collect.plugin('named', engine=[1])  # E: [list-item]
    collect.plugin(engine=['>1.0.0', 1])  # E: [list-item]


@pytest.mark.mypy_testing
def test_slot_bad_factory_arguments_include_explicit_plugin_names_type_errors():
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
    slot(explicit_plugin_names='yes')  # type: ignore[call-overload]

    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    slot(collect, unique='yes')  # type: ignore[call-overload]
    slot(collect, explicit_plugin_names='yes')  # type: ignore[call-overload]
    with pytest.raises(TypeError):
        slot(collect, signature=[1])  # E: [list-item]
    with pytest.raises(TypeError):
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
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    with pytest.raises(TypeError):
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
    def collect_with_bare_factory(value: int) -> List[int]:  # noqa: ARG001
        return []

    @named_factory
    def collect_with_named_factory(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    @keyword_named_factory
    def collect_with_keyword_named_factory(value: int) -> List[int]:  # noqa: ARG001
        return []

    reveal_type(collect_with_bare_factory(1))  # R: builtins.list[builtins.int]
    reveal_type(collect_with_named_factory(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(collect_with_keyword_named_factory(1))  # R: builtins.list[builtins.int]


@pytest.mark.mypy_testing
def test_slot_selection_is_not_assignable_to_full_slot_protocol():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    full_slot: SlotProtocol[[int], List[int], int] = collect['name']  # E: [assignment]  # noqa: F841


@pytest.mark.mypy_testing
def test_exact_result_type_is_not_widened_for_typing_collections():
    @slot
    def collect_list(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot
    def collect_dict(value: int) -> Dict[str, int]:  # noqa: ARG001
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
    def collect_list(value: int) -> List[int]:  # noqa: ARG001
        return []

    @collect_list.plugin  # E: [arg-type]
    def bad_list_plugin(value: int) -> str:
        return str(value)

    @slot
    def collect_dict(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    @collect_dict.plugin()  # E: [arg-type]
    def bad_dict_plugin(value: int) -> str:
        return str(value)


@pytest.mark.mypy_testing
def test_selection_does_not_expose_full_slot_api():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    selection = collect['name']

    with pytest.raises(AttributeError):
        selection.plugin('name')  # E: [attr-defined]
    with pytest.raises(AttributeError):
        selection.keys()  # E: [attr-defined]
    with pytest.raises(TypeError):
        selection['nested']  # E: [index]
    assert 'name' not in selection  # E: [operator]


@pytest.mark.mypy_testing
def test_popped_selection_does_not_expose_full_slot_api():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    @collect.plugin('name')
    def plugin(value: int) -> int:
        return value

    popped = collect.pop('name')

    with pytest.raises(AttributeError):
        popped.plugin('name')  # E: [attr-defined]
    with pytest.raises(AttributeError):
        popped.keys()  # E: [attr-defined]
    with pytest.raises(TypeError):
        popped['nested']  # E: [index]
    assert 'name' not in popped  # E: [operator]


@pytest.mark.mypy_testing
def test_collection_api_reports_wrong_argument_types():
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    with pytest.raises(TypeError):
        collect.keys(1)  # E: [call-arg]
    with pytest.raises(KeyError):
        collect[1]  # E: [index]
    with pytest.raises(KeyError):
        collect.pop(1)  # type: ignore[call-overload]
    with pytest.raises(TypeError):
        collect.pop()  # type: ignore[call-overload]
    with pytest.raises(TypeError):
        collect.pop('name', 1, 2)  # type: ignore[call-overload]
    with pytest.raises(KeyError):
        del collect[1]  # E: [arg-type]

    keys_as_list: List[str] = collect.keys()  # E: [assignment]  # noqa: F841
    wrong_selection: int = collect['name']  # E: [assignment]  # noqa: F841

    @collect.plugin('name')
    def plugin(value: int) -> int:
        return value

    wrong_popped_selection: int = collect.pop('name')  # E: [assignment]  # noqa: F841


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
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    @collect.plugin
    def plugin_without_parentheses(value: int) -> int:
        return value

    @collect.plugin()
    def plugin_with_parentheses(value: int) -> int:
        return value + 1

    wrong_1: Callable[[int], str] = plugin_without_parentheses  # E: [assignment]  # noqa: F841
    wrong_2: Callable[[int], str] = plugin_with_parentheses  # E: [assignment]  # noqa: F841


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_built_in_generic_result_matrix_preserves_exact_slot_types():
    """Explicitly cover decorator and built-in collection combinations.

    The static matrix mirrors the typing-collection test because fixtures and
    pytest parametrization do not specialize the source that mypy receives.
    """
    @slot
    def bare_dictionary_slot(value: int) -> dict[str, int]:  # noqa: ARG001
        return {}

    @slot
    def bare_list_slot(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot()
    def factory_dictionary_slot(value: int) -> dict[str, int]:  # noqa: ARG001
        return {}

    @slot()
    def factory_list_slot(value: int) -> list[int]:  # noqa: ARG001
        return []

    reveal_type(bare_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(bare_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(factory_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(factory_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(bare_list_slot['name'](1))  # R: builtins.list[builtins.int]
    reveal_type(factory_list_slot['name'](1))  # R: builtins.list[builtins.int]


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_built_in_generic_results_are_not_widened():
    @slot
    def collect_list(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot
    def collect_dict(value: int) -> dict[str, int]:  # noqa: ARG001
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
    def collect(value: int) -> list[int]:  # noqa: ARG001
        return []

    @collect.plugin('name')
    def plugin(value: int) -> int:
        return value

    popped = collect.pop('name')
    reveal_type(popped(1))  # R: builtins.list[builtins.int]
    reveal_type(collect.pop('name', 'fallback'))  # R: Union[pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int], builtins.str]


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_plugin_return_type_mismatch_is_reported_for_built_in_generics():
    @slot
    def collect_list(value: int) -> list[int]:  # noqa: ARG001
        return []

    @collect_list.plugin  # E: [arg-type]
    def bad_list_plugin(value: int) -> str:
        return str(value)

    @slot
    def collect_dict(value: int) -> dict[str, int]:  # noqa: ARG001
        return {}

    @collect_dict.plugin(run_once=True)  # E: [arg-type]
    def bad_dict_plugin(value: int) -> str:
        return str(value)
