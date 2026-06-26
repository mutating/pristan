# mypy: warn-unused-ignores

import sys
from typing import Any, Callable, Dict, List

import pytest
from typing_extensions import reveal_type

import pristan.components.slot as slot_module
from pristan import slot
from pristan.common_types import (
    SlotDecoratorProtocol,
    SlotProtocol,
    SlotSelectionProtocol,
)
from pristan.errors import CannotGetVersionsError, StrangeTypeAnnotationError


@pytest.fixture(autouse=True)
def clean_entrypoints(monkeypatch):
    """Typing tests do not depend on installed entry points."""
    monkeypatch.setattr(slot_module, 'entry_points', lambda group=None: [])  # noqa: ARG005


@pytest.mark.mypy_testing
def test_typing_collection_result_matrix_preserves_exact_slot_types():
    """Cover decorator, `.one`, and typing collection combinations.

    Mypy sees this file statically, so the matrix keeps normal calls,
    `@slot`/`@slot()`, and `List`/`Dict` variants explicit.
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

    @bare_list_slot.plugin('bare_list')
    def bare_list_plugin(value: int) -> int:
        return value

    @bare_dictionary_slot.plugin('bare_dictionary')
    def bare_dictionary_plugin(value: int) -> int:
        return value

    @factory_list_slot.plugin('factory_list')
    def factory_list_plugin(value: int) -> int:
        return value

    @factory_dictionary_slot.plugin('factory_dictionary')
    def factory_dictionary_plugin(value: int) -> int:
        return value

    reveal_type(bare_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(bare_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(factory_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(factory_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(bare_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(bare_dictionary_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(factory_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(factory_dictionary_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(bare_dictionary_slot.keys())  # R: builtins.tuple[builtins.str, ...]
    reveal_type(factory_dictionary_slot.keys())  # R: builtins.tuple[builtins.str, ...]


@pytest.mark.mypy_testing
def test_slot_without_return_annotation_is_typed_as_any_in_both_forms():
    """Unannotated slots and selections keep Any call results through `.one`.

    Covers `@slot`/`@slot()` and both plugin decorator forms.
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
    reveal_type(notify.one(1))  # R: Any
    reveal_type(notify_too.one(1))  # R: Any
    reveal_type(notify['plugin_without_parentheses'].one(1))  # R: Any
    reveal_type(notify_too['plugin_with_parentheses'].one(1))  # R: Any

    plugin_without_parentheses(1)
    plugin_with_parentheses(1)


@pytest.mark.mypy_testing
def test_slot_configuration_arguments_include_explicit_plugin_names():
    """Configured decorators keep normal and `.one` calls typed under strict naming."""
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

    @slot_with_positional_name.plugin('positional_plugin')
    def positional_plugin(value: int) -> int:
        return value

    @unique_slot_with_positional_name.plugin('unique_positional_plugin')
    def unique_positional_plugin(value: int) -> int:
        return value

    @slot_with_keyword_name.plugin('keyword_plugin')
    def keyword_plugin(value: int) -> int:
        return value

    @unique_slot.plugin('unique_plugin')
    def unique_plugin(value: int) -> int:
        return value

    @explicit_plugin_names_slot.plugin('explicit_plugin')
    def explicit_plugin(value: int) -> int:
        return value

    @configured_slot.plugin('configured_plugin')
    def configured_plugin(value: int) -> int:
        return value

    @configured_slot_with_signature_list.plugin('signature_list_plugin')
    def signature_list_plugin(value: int, context: str = '') -> int:  # noqa: ARG001
        return value

    reveal_type(slot_with_positional_name(1))  # R: builtins.list[builtins.int]
    reveal_type(unique_slot_with_positional_name(1))  # R: builtins.list[builtins.int]
    reveal_type(slot_with_keyword_name(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(unique_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(explicit_plugin_names_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list(1, 'context'))  # R: builtins.list[builtins.int]
    reveal_type(slot_with_positional_name.one(1))  # R: builtins.list[builtins.int]
    reveal_type(unique_slot_with_positional_name.one(1))  # R: builtins.list[builtins.int]
    reveal_type(slot_with_keyword_name.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(unique_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(explicit_plugin_names_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list.one(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_slot_with_signature_list.one(1, 'context'))  # R: builtins.list[builtins.int]
    configured_slot_with_signature_list(1, 2)  # E: [arg-type]


@pytest.mark.mypy_testing
def test_slot_direct_call_configuration_arguments_include_explicit_plugin_names():
    """Direct-call overloads preserve call, plugin, and `.one` result types.

    Covers factory options, signatures, result shapes, and plugin iteration.
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
        reveal_type(signature_list_notify_slot.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], None, Any]
        reveal_type(signature_list_notify_slot.one(1))  # R: None
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
def test_slot_direct_call_one_preserves_result_types():
    """Direct-call slot forms expose `.one` with the same result types."""
    def collect_list(value: int) -> List[int]:  # noqa: ARG001
        return []

    def collect_dict(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    def notify(value: int):  # noqa: ARG001
        return None

    default_list_slot = slot(collect_list)
    list_slot = slot(collect_list, unique=True, explicit_plugin_names=True)
    signature_list_slot = slot(collect_list, signature=['.'])
    dict_slot = slot(collect_dict, signature='.', name='collect', max=2, type_check=False, entrypoint_group='custom', unique=True)
    signature_list_dict_slot = slot(collect_dict, signature=['.'])
    notify_slot = slot(notify, unique=True)

    @default_list_slot.plugin('default_list')
    def default_list_plugin(value: int) -> int:
        return value

    @list_slot.plugin('list_plugin')
    def list_plugin(value: int) -> int:
        return value

    @signature_list_slot.plugin('signature_list')
    def signature_list_plugin(value: int) -> int:
        return value

    @dict_slot.plugin('dict_plugin')
    def dict_plugin(value: int) -> int:
        return value

    @signature_list_dict_slot.plugin('signature_list_dict')
    def signature_list_dict_plugin(value: int) -> int:
        return value

    @notify_slot.plugin('notify')
    def notify_plugin(value: int) -> str:
        return str(value)

    reveal_type(default_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(signature_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(dict_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(signature_list_dict_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(notify_slot.one(1))  # R: Any


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_slot_direct_call_one_preserves_built_in_result_types():
    """Direct-call slot forms expose `.one` with built-in generic result types."""
    def collect_list(value: int) -> list[int]:  # noqa: ARG001
        return []

    def collect_dict(value: int) -> dict[str, int]:  # noqa: ARG001
        return {}

    default_list_slot = slot(collect_list)
    list_slot = slot(collect_list, unique=True, explicit_plugin_names=True)
    signature_list_slot = slot(collect_list, signature=['.'])
    dict_slot = slot(collect_dict, signature='.', name='collect', max=2, type_check=False, entrypoint_group='custom', unique=True)
    signature_list_dict_slot = slot(collect_dict, signature=['.'])

    @default_list_slot.plugin('default_list')
    def default_list_plugin(value: int) -> int:
        return value

    @list_slot.plugin('list_plugin')
    def list_plugin(value: int) -> int:
        return value

    @signature_list_slot.plugin('signature_list')
    def signature_list_plugin(value: int) -> int:
        return value

    @dict_slot.plugin('dict_plugin')
    def dict_plugin(value: int) -> int:
        return value

    @signature_list_dict_slot.plugin('signature_list_dict')
    def signature_list_dict_plugin(value: int) -> int:
        return value

    reveal_type(default_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(signature_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(dict_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(signature_list_dict_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]


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
    """Popped selections keep their call and `.one` result types."""
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

    popped_list_selection = collect_list.pop('name')
    popped_dict_selection = collect_dict.pop('name')

    popped_list_selection_view: SlotSelectionProtocol[[int], List[int], int] = popped_list_selection
    popped_dict_selection_view: SlotSelectionProtocol[[int], Dict[str, int], int] = popped_dict_selection

    reveal_type(popped_list_selection.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(popped_dict_selection.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(popped_list_selection.one.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(popped_dict_selection.one.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(popped_list_selection(1))  # R: builtins.list[builtins.int]
    reveal_type(popped_dict_selection(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(popped_list_selection.one(1))  # R: builtins.list[builtins.int]
    reveal_type(popped_dict_selection.one(1))  # R: builtins.dict[builtins.str, builtins.int]

    popped_list_selection_view(1)
    popped_dict_selection_view(1)


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
    """Loose built-in containers keep Any payload types through `.one`."""
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
    reveal_type(collect_list.one())  # R: builtins.list[Any]
    reveal_type(collect_dict.one())  # R: builtins.dict[builtins.str, Any]
    reveal_type(collect_list['list_plugin'].one())  # R: builtins.list[Any]
    reveal_type(collect_dict['dict_plugin'].one())  # R: builtins.dict[builtins.str, Any]


@pytest.mark.mypy_testing
def test_slot_with_loose_typing_list_and_dict_annotations_keeps_any_payload_type():
    """Loose typing containers keep Any payload types through `.one`."""
    @slot
    def collect_list() -> List:
        return []

    @slot
    def collect_dict() -> Dict:
        return {}

    @collect_list.plugin
    def list_plugin() -> str:
        return 'value'

    @collect_dict.plugin
    def dict_plugin() -> str:
        return 'value'

    reveal_type(collect_list())  # R: builtins.list[Any]
    reveal_type(collect_dict())  # R: builtins.dict[builtins.str, Any]
    reveal_type(collect_list.one())  # R: builtins.list[Any]
    reveal_type(collect_dict.one())  # R: builtins.dict[builtins.str, Any]
    reveal_type(collect_list['list_plugin'].one())  # R: builtins.list[Any]
    reveal_type(collect_dict['dict_plugin'].one())  # R: builtins.dict[builtins.str, Any]


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
    """Cover decorator, `.one`, and built-in collection combinations.

    Mypy sees this file statically, so the matrix keeps built-in list/dict and
    configured variants explicit.
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

    @slot(name='builtin_keyword')
    def keyword_list_slot(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot('builtin_positional')
    def positional_list_slot(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot(unique=True)
    def unique_list_slot(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot(explicit_plugin_names=True)
    def explicit_plugin_names_slot(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot(signature='.', max=1, type_check=False)
    def configured_list_slot(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot(signature=['..', '.'])
    def configured_list_slot_with_signature_list(value: int, context: str = '') -> list[int]:  # noqa: ARG001
        return []

    @bare_dictionary_slot.plugin('bare_dictionary')
    def bare_dictionary_plugin(value: int) -> int:
        return value

    @bare_list_slot.plugin('bare_list')
    def bare_list_plugin(value: int) -> int:
        return value

    @factory_dictionary_slot.plugin('factory_dictionary')
    def factory_dictionary_plugin(value: int) -> int:
        return value

    @factory_list_slot.plugin('factory_list')
    def factory_list_plugin(value: int) -> int:
        return value

    @keyword_list_slot.plugin('keyword')
    def keyword_plugin(value: int) -> int:
        return value

    @positional_list_slot.plugin('positional')
    def positional_plugin(value: int) -> int:
        return value

    @unique_list_slot.plugin('unique')
    def unique_plugin(value: int) -> int:
        return value

    @explicit_plugin_names_slot.plugin('explicit')
    def explicit_plugin(value: int) -> int:
        return value

    @configured_list_slot.plugin('configured')
    def configured_plugin(value: int) -> int:
        return value

    @configured_list_slot_with_signature_list.plugin('signature_list')
    def signature_list_plugin(value: int, context: str = '') -> int:  # noqa: ARG001
        return value

    reveal_type(bare_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(bare_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(factory_dictionary_slot(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(factory_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(keyword_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(positional_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(unique_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(explicit_plugin_names_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_list_slot(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_list_slot_with_signature_list(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_list_slot_with_signature_list(1, 'context'))  # R: builtins.list[builtins.int]
    reveal_type(bare_dictionary_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(bare_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(factory_dictionary_slot.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(factory_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(keyword_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(positional_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(unique_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(explicit_plugin_names_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_list_slot.one(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_list_slot_with_signature_list.one(1))  # R: builtins.list[builtins.int]
    reveal_type(configured_list_slot_with_signature_list.one(1, 'context'))  # R: builtins.list[builtins.int]
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
    """Popped built-in generic selections keep call, `.one`, and default-pop types."""
    @slot
    def collect(value: int) -> list[int]:  # noqa: ARG001
        return []

    @collect.plugin('name')
    def plugin(value: int) -> int:
        return value

    popped_selection = collect.pop('name')
    reveal_type(popped_selection.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(popped_selection.one.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(popped_selection(1))  # R: builtins.list[builtins.int]
    reveal_type(popped_selection.one(1))  # R: builtins.list[builtins.int]
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


@pytest.mark.mypy_testing
def test_typing_generics_one_preserves_result_types():
    """`.one` keeps typing-generic call result types for slots and selections."""
    @slot
    def collect_list(value: int) -> List[int]:  # noqa: ARG001
        return []

    @slot
    def collect_dict(value: int) -> Dict[str, int]:  # noqa: ARG001
        return {}

    @collect_list.plugin('list_plugin')
    def list_plugin(value: int) -> int:
        return value

    @collect_dict.plugin('dict_plugin')
    def dict_plugin(value: int) -> int:
        return value

    list_selection = collect_list['list_plugin']
    dict_selection = collect_dict['dict_plugin']

    reveal_type(collect_list.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(collect_dict.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(list_selection.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(dict_selection.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(list_selection.one.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(dict_selection.one.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(collect_list.one(1))  # R: builtins.list[builtins.int]
    reveal_type(collect_dict.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(list_selection.one(1))  # R: builtins.list[builtins.int]
    reveal_type(dict_selection.one(1))  # R: builtins.dict[builtins.str, builtins.int]

    wrong_list_selection_call: Callable[[str], List[int]] = collect_list.one.__call__  # E: [assignment]  # noqa: F841
    wrong_dict_selection_call: Callable[[str], Dict[str, int]] = collect_dict.one.__call__  # E: [assignment]  # noqa: F841
    wrong_selected_list_selection_call: Callable[[str], List[int]] = list_selection.one.__call__  # E: [assignment]  # noqa: F841
    wrong_selected_dict_selection_call: Callable[[str], Dict[str, int]] = dict_selection.one.__call__  # E: [assignment]  # noqa: F841
    wrong_list_result: Dict[str, int] = collect_list.one(1)  # E: [assignment]  # noqa: F841
    wrong_dict_result: List[int] = collect_dict.one(1)  # E: [assignment]  # noqa: F841
    wrong_selection_list_result: Dict[str, int] = list_selection.one(1)  # E: [assignment]  # noqa: F841
    wrong_selection_dict_result: List[int] = dict_selection.one(1)  # E: [assignment]  # noqa: F841


@pytest.mark.mypy_testing
def test_one_preserves_accepted_and_rejected_call_shapes():
    """`.one` preserves accepted and rejected call shapes for slots and selections."""
    @slot
    def collect(value: int, label: str = 'default', *, enabled: bool = True) -> List[str]:  # noqa: ARG001
        return []

    @collect.plugin('name')
    def plugin(value: int, label: str = 'default', *, enabled: bool = True) -> str:
        return f'{value + 1}:{label}:{enabled}'

    selection = collect['name']

    reveal_type(collect.one(1))  # R: builtins.list[builtins.str]
    reveal_type(collect.one(1, 'label', enabled=False))  # R: builtins.list[builtins.str]
    reveal_type(selection.one(1))  # R: builtins.list[builtins.str]
    reveal_type(selection.one(1, 'label', enabled=False))  # R: builtins.list[builtins.str]

    with pytest.raises(TypeError):
        collect.one('value')  # E: [arg-type]
    with pytest.raises(TypeError):
        collect.one()  # E: [call-arg]
    with pytest.raises(TypeError):
        collect.one(1, unknown=True)  # E: [call-arg]
    with pytest.raises(TypeError):
        selection.one('value')  # E: [arg-type]
    with pytest.raises(TypeError):
        selection.one()  # E: [call-arg]
    with pytest.raises(TypeError):
        selection.one(1, unknown=True)  # E: [call-arg]


@pytest.mark.skipif(sys.version_info < (3, 9), reason='built-in generics require Python 3.9+')
@pytest.mark.mypy_testing
def test_built_in_generics_one_preserves_result_types():
    """`.one` keeps built-in generic call result types for slots and selections."""
    @slot
    def collect_list(value: int) -> list[int]:  # noqa: ARG001
        return []

    @slot
    def collect_dict(value: int) -> dict[str, int]:  # noqa: ARG001
        return {}

    @collect_list.plugin('list_plugin')
    def list_plugin(value: int) -> int:
        return value

    @collect_dict.plugin('dict_plugin')
    def dict_plugin(value: int) -> int:
        return value

    list_selection = collect_list['list_plugin']
    dict_selection = collect_dict['dict_plugin']

    reveal_type(collect_list.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(collect_dict.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(list_selection.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(dict_selection.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(list_selection.one.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.list[builtins.int], builtins.int]
    reveal_type(dict_selection.one.one)  # R: pristan.common_types.SlotSelectionProtocol[[value: builtins.int], builtins.dict[builtins.str, builtins.int], builtins.int]
    reveal_type(collect_list.one(1))  # R: builtins.list[builtins.int]
    reveal_type(collect_dict.one(1))  # R: builtins.dict[builtins.str, builtins.int]
    reveal_type(list_selection.one(1))  # R: builtins.list[builtins.int]
    reveal_type(dict_selection.one(1))  # R: builtins.dict[builtins.str, builtins.int]

    wrong_list_selection_call: Callable[[str], list[int]] = collect_list.one.__call__  # E: [assignment]  # noqa: F841
    wrong_dict_selection_call: Callable[[str], dict[str, int]] = collect_dict.one.__call__  # E: [assignment]  # noqa: F841
    wrong_selected_list_selection_call: Callable[[str], list[int]] = list_selection.one.__call__  # E: [assignment]  # noqa: F841
    wrong_selected_dict_selection_call: Callable[[str], dict[str, int]] = dict_selection.one.__call__  # E: [assignment]  # noqa: F841
    wrong_list_result: Dict[str, int] = collect_list.one(1)  # E: [assignment]  # noqa: F841
    wrong_dict_result: List[int] = collect_dict.one(1)  # E: [assignment]  # noqa: F841
    wrong_selection_list_result: Dict[str, int] = list_selection.one(1)  # E: [assignment]  # noqa: F841
    wrong_selection_dict_result: List[int] = dict_selection.one(1)  # E: [assignment]  # noqa: F841


@pytest.mark.mypy_testing
def test_one_protocols_accept_slot_and_selection():
    """Protocols expose `.one` with the same callable surface as concrete values."""
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    @collect.plugin('name')
    def plugin(value: int) -> int:
        return value

    def call_slot(target: 'SlotProtocol[[int], List[int], int]') -> List[int]:
        return target.one(1)

    def call_selection(target: 'SlotSelectionProtocol[[int], List[int], int]') -> List[int]:
        return target.one(1)

    reveal_type(call_slot(collect))  # R: builtins.list[builtins.int]
    reveal_type(call_selection(collect['name']))  # R: builtins.list[builtins.int]


@pytest.mark.mypy_testing
def test_one_read_only_surface_rejects_assignment_and_deletion():
    """`.one` rejects assignment and deletion on slots and selections."""
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    selection = collect['name']
    collect_view: SlotProtocol[[int], List[int], int] = collect
    selection_view: SlotSelectionProtocol[[int], List[int], int] = selection

    with pytest.raises(AttributeError):
        collect.one = selection  # E: [misc]
    with pytest.raises(AttributeError):
        selection.one = selection  # E: [misc]
    with pytest.raises(AttributeError):
        del collect_view.one
    with pytest.raises(AttributeError):
        del selection_view.one


@pytest.mark.mypy_testing
def test_pop_with_default_exposes_one_after_selection_narrowing():
    """Pop with a default exposes `.one` in the narrowed selection branch."""
    @slot
    def collect(value: int) -> List[int]:  # noqa: ARG001
        return []

    @collect.plugin('name')
    def plugin(value: int) -> int:
        return value

    popped_or_default = collect.pop('name', 'fallback')

    if isinstance(popped_or_default, str):
        reveal_type(popped_or_default)  # R: builtins.str
    else:
        reveal_type(popped_or_default.one(1))  # R: builtins.list[builtins.int]
