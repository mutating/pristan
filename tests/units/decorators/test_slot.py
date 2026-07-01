from sys import version_info
from threading import RLock
from typing import List

import pytest
from full_match import match
from locklib import LockTraceWrapper
from packaging.version import Version
from sigmatch.errors import SignatureMismatchError

import pristan.components.slot as slot_module
from pristan import slot
from pristan.decorators.slot import Slot
from pristan.errors import (
    CannotGetVersionsError,
    ExplicitNameRequiredError,
    NumberOfCallsError,
    PrimadonnaPluginError,
    StrangeTypeAnnotationError,
    TooManyPluginsError,
)


def test_slot_is_not_a_function():
    """Both @slot and @slot() replace the decorated function binding with a Slot wrapper."""
    @slot
    def some_slot():
        ...

    @slot()
    def some_slot_2():
        ...

    assert isinstance(some_slot, Slot)
    assert isinstance(some_slot_2, Slot)


def test_public_slot_creation_forms_support_bool(monkeypatch):
    """Every public slot construction form exposes the same bool semantics.

    Empty slots are false, slots with a non-empty default body are true, and the
    default bodies are not executed during truthiness checks.
    """
    monkeypatch.setattr(slot_module, 'entry_points', lambda group=None: [])  # noqa: ARG005

    @slot
    def bare_empty():
        ...

    @slot
    def bare_non_empty():
        raise AssertionError('bare default body was executed')

    @slot()
    def factory_empty():
        pass

    @slot()
    def factory_non_empty():
        raise AssertionError('factory default body was executed')

    @slot(name='keyword-empty')
    def keyword_empty():
        ...

    @slot(name='keyword-non-empty')
    def keyword_non_empty():
        raise AssertionError('keyword default body was executed')

    @slot('positional-empty')
    def positional_empty():
        pass

    @slot('positional-non-empty')
    def positional_non_empty():
        raise AssertionError('positional default body was executed')

    def direct_empty():
        ...

    def direct_non_empty():
        raise AssertionError('direct default body was executed')

    for empty_slot in (
        bare_empty,
        factory_empty,
        keyword_empty,
        positional_empty,
        slot(direct_empty),
        slot(direct_empty, name='direct-empty'),
    ):
        assert not bool(empty_slot)

    for non_empty_slot in (
        bare_non_empty,
        factory_non_empty,
        keyword_non_empty,
        positional_non_empty,
        slot(direct_non_empty),
        slot(direct_non_empty, name='direct-non-empty'),
    ):
        assert bool(non_empty_slot)


def test_public_slot_with_local_plugin_is_truthy(monkeypatch):
    """A local plugin makes an otherwise empty public slot truthy.

    This checks the plugin side of the bool rule separately from the public
    construction-form matrix, so the empty-slot cases stay genuinely empty.
    """
    monkeypatch.setattr(slot_module, 'entry_points', lambda group=None: [])  # noqa: ARG005

    @slot
    def empty_slot():
        ...

    @empty_slot.plugin
    def plugin():
        raise AssertionError('plugin was executed')

    assert bool(empty_slot)


def test_slot_have_not_comparing_signature_with_itself():
    """An explicit slot signature is enforced against the decorated slot function itself; signature='..' requires two positional arguments, so a zero-argument slot raises before any plugin registration."""
    with pytest.raises(SignatureMismatchError, match=match('The signature of the callable object does not match the expected one.')):
        @slot(signature='..')
        def some_slot():
            ...


def test_plugin_have_not_comparing_signature_to_passed_one_to_slot(folder_plugin):
    """With signature='..', plugin registration is checked against the explicit two-argument signature, so a zero-argument plugin is rejected even though the slot function itself is valid."""
    @slot(signature='..')
    def some_slot(a, b):
        ...

    with pytest.raises(SignatureMismatchError, match=match('The signature of the callable object does not match the expected one.')):
        @folder_plugin(some_slot)
        def plugin():
            ...


def test_plugin_have_not_comparing_signature_to_slot(folder_slot, folder_plugin):
    """Reject plugins at registration when a slot that omits signature= cannot be called the same way as the plugin, across public slot and plugin decorator forms."""
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    with pytest.raises(SignatureMismatchError, match=match('No common calling method has been found between the slot and the plugin.')):
        @folder_plugin(some_slot)
        def plugin():
            ...


def test_slot_and_plugin_support_all_passed_signatures(folder_plugin, list_type):
    """A slot and its plugins must support every call shape in the list.

    The optional context parameter lets the slot and plugin accept both
    declared call shapes, and the assertions exercise each one.
    """
    @slot(signature=['..', '.'])
    def on_event(event, context=None) -> list_type:  # noqa: ARG001
        return []

    @folder_plugin(on_event)
    def plugin(event, context=None):
        if context is None:
            return event
        return f'{event}:{context}'

    assert on_event('event') == ['event']
    assert on_event('event', 'context') == ['event:context']


def test_direct_call_slot_enforces_signature_list(list_type):
    """Direct-call slot construction enforces every listed call shape."""
    def on_event(event, context=None) -> list_type:  # noqa: ARG001
        return []

    event_slot = slot(on_event, signature=['..', '.'])

    @event_slot.plugin
    def plugin(event, context=None):
        return event, context

    with pytest.raises(SignatureMismatchError, match=match('This is a difficult situation, there is no guarantee that a call with a variable number of positional arguments will fill all the slots of positional arguments.')):
        @event_slot.plugin
        def invalid_plugin(event, context):
            return event, context

    assert len(event_slot) == 1
    assert event_slot('event') == [('event', None)]
    assert event_slot('event', 'context') == [('event', 'context')]


def test_plugin_with_required_second_argument_does_not_match_all_passed_signatures():
    """A plugin requiring two arguments fails the one-argument call shape."""
    @slot(signature=['..', '.'])
    def on_event(event, context=None):
        ...

    with pytest.raises(SignatureMismatchError, match=match('This is a difficult situation, there is no guarantee that a call with a variable number of positional arguments will fill all the slots of positional arguments.')):
        @on_event.plugin
        def invalid_plugin(event, context):
            return event, context

    assert len(on_event) == 0


def test_plugin_with_only_one_argument_does_not_match_all_passed_signatures():
    """A plugin accepting one argument fails the two-argument call shape."""
    @slot(signature=['..', '.'])
    def on_event(event, context=None):
        ...

    with pytest.raises(SignatureMismatchError, match=match('The signature of the callable object does not match the expected one.')):
        @on_event.plugin
        def invalid_plugin(event):
            return event

    assert len(on_event) == 0


def test_slot_has_to_match_all_passed_signatures(list_type):
    """A slot must support every listed call shape, not only one of them.

    The same required-two-argument function remains valid with the equivalent
    single string signature, isolating the additional list requirement.
    """
    with pytest.raises(SignatureMismatchError, match=match('This is a difficult situation, there is no guarantee that a call with a variable number of positional arguments will fill all the slots of positional arguments.')):
        @slot(signature=['..', '.'])
        def on_event(event, context) -> list_type:
            return [(event, context)]

    @slot(signature='..')
    def on_event_with_single_signature(event, context) -> list_type:
        return [(event, context)]

    assert on_event_with_single_signature('event', 'context') == [('event', 'context')]


def test_one_signature_in_list_enforces_its_call_shape(list_type):
    """A one-element signature list enforces its single call shape."""
    @slot(signature=['..'])
    def collect(a, b) -> list_type:  # noqa: ARG001
        return []

    @collect.plugin
    def plugin(a, b):
        return a + b

    with pytest.raises(SignatureMismatchError, match=match('The signature of the callable object does not match the expected one.')):
        @collect.plugin
        def invalid_plugin(a):
            return a

    assert collect(1, 2) == [3]


def test_empty_signature_list_is_not_allowed():
    """An empty signature list is rejected because it declares no calls."""
    with pytest.raises(ValueError, match=match('The slot signature may be omitted, specified as a string, or specified as a non-empty list of strings; an empty list was provided.')):
        @slot(signature=[])
        def on_event():
            ...


def test_empty_signature_list_is_checked_before_return_annotation():
    """Signature-list validation takes priority over return annotations."""
    with pytest.raises(ValueError, match=match('The slot signature may be omitted, specified as a string, or specified as a non-empty list of strings; an empty list was provided.')):
        @slot(signature=[])
        def on_event() -> int:
            return 1


@pytest.mark.parametrize(
    'signature',
    [
        ('.',),
        ('..', '.'),
        ('invalid!',),
        ('invalid!', 'bad-name'),
        (1,),
        (1, False),
        1,
        True,
    ],
    ids=(
        'tuple_with_one_valid_string',
        'tuple_with_several_valid_strings',
        'tuple_with_one_invalid_string',
        'tuple_with_several_invalid_strings',
        'tuple_with_one_non_string',
        'tuple_with_several_non_strings',
        'integer_scalar',
        'boolean_scalar',
    ),
)
def test_unsupported_signature_containers_and_scalars_are_rejected(signature: object):
    """Only a string or a list may declare slot signature constraints.

    Tuple contents do not matter: tuples and scalar values are rejected before
    the unrelated return annotation is inspected.
    """
    with pytest.raises(TypeError, match=match('The slot signature must be either a string or a list of strings.')):
        @slot(signature=signature)  # type: ignore[call-overload]
        def on_event() -> int:
            return 1


@pytest.mark.parametrize(
    'signature',
    [
        pytest.param([1], id='one_non_string'),
        pytest.param(['.', 1], id='valid_string_then_non_string'),
    ],
)
def test_signature_list_can_contain_only_strings(signature: object):
    """Every item in an accepted signature list must itself be a string."""
    with pytest.raises(TypeError, match=match('Only strings can be used as symbolic representation of function parameters. You used "1" (int).')):
        @slot(signature=signature)  # type: ignore[call-overload]
        def on_event():
            ...


@pytest.mark.parametrize(
    'signature',
    [
        pytest.param(['invalid!'], id='one_invalid_description'),
        pytest.param(['.', 'invalid!'], id='valid_then_invalid_description'),
    ],
)
def test_signature_list_rejects_invalid_call_descriptions(signature: List[str]):
    """Each string in a signature list must be valid sigmatch syntax."""
    with pytest.raises(ValueError, match=match('Only strings of a certain format can be used as symbols for function arguments: arbitrary variable names, and ".", "*", "**" strings. You used "invalid!".')):
        @slot(signature=signature)
        def on_event():
            ...


def test_signature_matchers_use_declaration_snapshot(list_type):
    """Later list mutations do not add constraints to installed matchers."""
    signatures = ['..', '.']

    @slot(signature=signatures)
    def on_event(event, context=None) -> list_type:  # noqa: ARG001
        return []

    signatures.append('...')

    @on_event.plugin
    def plugin(event, context=None):
        return event, context

    assert on_event('event') == [('event', None)]
    assert on_event('event', 'context') == [('event', 'context')]


def test_signature_list_repr_uses_declaration_snapshot():
    """The slot repr keeps the signature list as it was when declared."""
    signatures = ['..', '.']

    @slot(signature=signatures)
    def on_event(event, context=None):
        ...

    signatures.append('...')

    assert repr(on_event) == 'Slot(on_event, signature=[\'..\', \'.\'])'


def test_run_1_plugin_without_hints(folder_slot, folder_plugin, slot_unique_options):
    """An unannotated slot with one registered plugin exposes it as a collection item, runs it instead of the non-empty default body, and returns None."""
    bread_crumbs = []

    @folder_slot(slot(**slot_unique_options))
    def some_slot(a, b):
        bread_crumbs.append(a + b)

    @folder_plugin(some_slot)
    def some_plugin(a, b):
        bread_crumbs.append(a + b + 1)

    assert some_slot.keys() == ('some_plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['some_plugin']
    assert [x.name for x in some_slot['some_plugin']] == ['some_plugin']
    assert some_slot(1, 2) is None

    assert bread_crumbs == [4]


def test_run_1_plugin_with_emplty_list_hint(folder_slot, folder_plugin, list_type, slot_unique_options):
    """A slot with one registered plugin and a bare list/typing.List return annotation aggregates the plugin result into a one-item list and skips the non-empty default body."""
    bread_crumbs = []

    @folder_slot(slot(**slot_unique_options))
    def some_slot(a, b) -> list_type:  # type: ignore[return]
        bread_crumbs.append(a + b)

    @folder_plugin(some_slot)
    def some_plugin(a, b):
        bread_crumbs.append(a + b + 1)
        return a + b + 2

    assert some_slot.keys() == ('some_plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['some_plugin']
    assert [x.name for x in some_slot['some_plugin']] == ['some_plugin']
    assert some_slot(1, 2) == [5]

    assert bread_crumbs == [4]


def test_2_not_unique_plugins_with_same_names(folder_slot, folder_plugin):
    """Default slot decorators allow duplicate requested names, exposing `kek`, `kek-2`, and `kek-3` while `some_slot['kek']` returns the whole group."""
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    @folder_plugin(some_slot)
    def kek(a, b):
        ...

    @folder_plugin(some_slot)
    def kek(a, b):  # noqa: F811
        ...

    @folder_plugin(some_slot)
    def kek(a, b):  # noqa: F811
        ...

    assert [x.name for x in some_slot] == ['kek', 'kek-2', 'kek-3']
    assert [x.name for x in some_slot['kek']] == ['kek', 'kek-2', 'kek-3']


def test_direct_call_slot_keeps_default_non_unique_policy(list_type):
    """Direct-call slot creation keeps duplicate plugin names allowed by default.

    The direct-call form `slot(function)` bypasses decorator-factory syntax but
    should use the same default policy. This test registers two plugins with
    the same requested name on that slot.
    It proves the default policy is still non-unique by checking the suffixed
    installed names, the base-name selection, and both slot-level and
    selection-level calls.
    """
    def slot_function(value) -> list_type:
        return [value][1:]

    some_slot = slot(slot_function)

    @some_slot.plugin('plugin')
    def plugin_1(value):
        return value + 1

    @some_slot.plugin('plugin')
    def plugin_2(value):
        return value + 2

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 2
    assert [x.name for x in some_slot] == ['plugin', 'plugin-2']
    assert [x.name for x in some_slot['plugin']] == ['plugin', 'plugin-2']
    assert some_slot(1) == [2, 3]
    assert some_slot['plugin'](1) == [2, 3]


@pytest.mark.parametrize(
    'slot_options',
    [
        {},
        {'explicit_plugin_names': False},
    ],
    ids=('default', 'explicit_plugin_names=False'),
)
def test_explicit_plugin_names_disabled_allows_inferred_plugin_names(slot_options, list_type):
    """Default and explicitly disabled strict naming still infer plugin names."""
    @slot(**slot_options)
    def some_slot(value) -> list_type:
        return [value][1:]

    @some_slot.plugin
    def plugin(value):
        return value + 1

    @some_slot.plugin()
    def plugin_2(value):
        return value + 2

    assert some_slot.keys() == ('plugin', 'plugin_2')
    assert [x.name for x in some_slot] == ['plugin', 'plugin_2']
    assert some_slot(1) == [2, 3]


def test_explicit_plugin_names_direct_call_slot_rejects_inferred_names(list_type):
    """The direct `slot(function, ...)` form enforces explicit plugin names."""
    def slot_function(value) -> list_type:
        return [value][1:]

    some_slot = slot(slot_function, explicit_plugin_names=True)

    def inferred_plugin(value):
        return value + 1

    with pytest.raises(ExplicitNameRequiredError, match=match('Slot "slot_function" requires explicit plugin names.')):
        some_slot.plugin(inferred_plugin)

    with pytest.raises(ExplicitNameRequiredError, match=match('Slot "slot_function" requires explicit plugin names.')):
        some_slot.plugin()(inferred_plugin)

    assert some_slot.keys() == ()
    assert len(some_slot) == 0

    @some_slot.plugin('plugin')
    def named_plugin(value):
        return value + 2

    assert some_slot.keys() == ('plugin',)
    assert [x.name for x in some_slot] == ['plugin']
    assert some_slot(1) == [3]


@pytest.mark.parametrize(
    'registration_name',
    [
        'bare',
        'parenthesized',
        'unique',
        'engine',
        'run_once',
    ],
)
def test_explicit_plugin_names_rejects_inferred_plugin_names(registration_name):
    """No-name decorators fail before registration or signature validation."""
    @slot(explicit_plugin_names=True)
    def some_slot():
        ...

    def plugin(value):  # noqa: ARG001
        return None

    registrations = {
        'bare': lambda function: some_slot.plugin(function),
        'parenthesized': lambda function: some_slot.plugin()(function),
        'unique': lambda function: some_slot.plugin(unique=True)(function),
        'engine': lambda function: some_slot.plugin(engine='>1000.0.0')(function),
        'run_once': lambda function: some_slot.plugin(run_once=True)(function),
    }

    with pytest.raises(ExplicitNameRequiredError, match=match('Slot "some_slot" requires explicit plugin names.')):
        registrations[registration_name](plugin)

    assert some_slot.keys() == ()
    assert len(some_slot) == 0


def test_explicit_plugin_names_keeps_invalid_plugin_decorator_argument_error():
    """Invalid plugin decorator arguments keep their original error type."""
    @slot(explicit_plugin_names=True)
    def some_slot():
        ...

    with pytest.raises(TypeError, match=match('Only a function or plugin name followed by a function can be passed to the decorator.')):
        some_slot.plugin(123)


def test_explicit_plugin_names_named_plugin_unique_option_is_enforced(list_type):
    """Strict slots still honor plugin-level uniqueness after explicit naming."""
    @slot(explicit_plugin_names=True)
    def some_slot() -> list_type:
        return []

    @some_slot.plugin('first', unique=True)
    def first_plugin():
        return 'first'

    with pytest.raises(PrimadonnaPluginError, match=match('Plugin "first" claims to be unique, but there are other plugins with the same name.')):
        @some_slot.plugin('first')
        def duplicate_first_plugin():
            return 'duplicate'

    assert some_slot.keys() == ('first',)
    assert [x.name for x in some_slot] == ['first']
    assert some_slot() == ['first']


def test_explicit_plugin_names_named_plugin_engine_option_filters_plugins(list_type):
    """Strict slots still apply engine constraints after explicit naming."""
    @slot(explicit_plugin_names=True)
    def some_slot() -> list_type:
        return []

    some_slot.code_representation.package_version = Version('0.0.1')

    @some_slot.plugin('accepted', engine='>0.0.0')
    def accepted_plugin():
        return 'accepted'

    @some_slot.plugin('rejected', engine='>1000.0.0')
    def rejected_plugin():
        return 'rejected'

    assert some_slot.keys() == ('accepted',)
    assert [x.name for x in some_slot] == ['accepted']
    assert 'rejected' not in some_slot
    assert some_slot() == ['accepted']


def test_explicit_plugin_names_named_plugin_run_once_option_is_enforced(list_type):
    """Strict slots still honor run-once plugins after explicit naming."""
    @slot(explicit_plugin_names=True)
    def some_slot() -> list_type:
        return []

    @some_slot.plugin('plugin', run_once=True)
    def plugin():
        return 'plugin'

    assert some_slot.keys() == ('plugin',)
    assert [x.name for x in some_slot] == ['plugin']
    assert some_slot() == ['plugin']

    with pytest.raises(NumberOfCallsError, match=match('A limit of 1 has been set on the number of calls for plugin "plugin". And this plugin has already been called previously.')):
        some_slot()


def test_2_plugins_with_same_names_and_first_one_is_unique(folder_slot, folder_plugin):
    """An existing unique plugin rejects later same-name plugins in an otherwise non-unique slot instead of allowing duplicate suffixing, and the failed registration leaves only the original base-name plugin."""
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    @some_slot.plugin('kek', unique=True)
    def kek(a, b):
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Plugin "kek" claims to be unique, but there are other plugins with the same name.')):
        @folder_plugin(some_slot)
        def kek(a, b):
            ...

    assert [x.name for x in some_slot] == ['kek']
    assert [x.name for x in some_slot['kek'].plugins] == ['kek']


def test_2_plugins_with_same_names_and_second_one_is_unique(folder_slot, folder_plugin):
    """Reject a second duplicate plugin that claims uniqueness after it would be named "kek-2", with the error naming that attempted plugin and only the original "kek" left visible."""
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    @folder_plugin(some_slot)
    def kek(a, b):
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Plugin "kek-2" claims to be unique, but there are other plugins with the same name.')):
        @some_slot.plugin('kek', unique=True)
        def plugin_2(a, b):
            ...

    assert [x.name for x in some_slot] == ['kek']
    assert [x.name for x in some_slot['kek']] == ['kek']


def test_slot_unique_allows_multiple_plugins_with_distinct_names(folder_slot, list_type):
    """A unique slot accepts several plugins when their requested names differ.

    The unique policy should reject only repeated requested names, not limit a
    slot to one plugin. This test registers two distinct names and verifies the
    public collection views, individual selections, and aggregate slot result.
    """
    @folder_slot(slot(unique=True))
    def some_slot(value) -> list_type:
        return [value][1:]

    @some_slot.plugin('first')
    def first_plugin(value):
        return value + 1

    @some_slot.plugin('second')
    def second_plugin(value):
        return value + 2

    assert some_slot.keys() == ('first', 'second')
    assert len(some_slot) == 2
    assert [x.name for x in some_slot] == ['first', 'second']
    assert [x.name for x in some_slot['first']] == ['first']
    assert [x.name for x in some_slot['second']] == ['second']
    assert some_slot(1) == [2, 3]
    assert some_slot['first'](1) == [2]
    assert some_slot['second'](1) == [3]


def test_slot_unique_allows_reusing_plugin_name_after_removal(folder_slot, list_type):
    """A unique slot allows a requested plugin name to be reused after removal.

    Slot-level uniqueness is enforced against currently registered requested
    names. This test registers a plugin, removes its base-name bucket through
    the public collection API, and then registers a different plugin with the
    same requested name. The final assertions prove the second plugin keeps the
    base name without a suffix and is the only plugin called by the slot.
    """
    @folder_slot(slot(unique=True))
    def some_slot() -> list_type:
        return []

    @some_slot.plugin('plugin')
    def plugin_1():
        return 'first'

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert some_slot() == ['first']

    del some_slot['plugin']

    assert some_slot.keys() == ()
    assert len(some_slot) == 0
    assert 'plugin' not in some_slot

    @some_slot.plugin('plugin')
    def plugin_2():
        return 'second'

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert 'plugin-2' not in some_slot
    assert some_slot() == ['second']


def test_slot_unique_rejects_duplicate_plugin_names(folder_slot):
    """A unique slot rejects a second plugin with the same requested name.

    The duplicate registration must fail with the shared plugin error type and
    the slot-level message. The assertions after the exception prove that the
    failed plugin was not installed under either the base name or a suffixed
    fallback name.
    """
    @folder_slot(slot(unique=True))
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin_1():
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Slot "some_slot" requires unique plugin names, but "plugin" is already registered.')):
        @some_slot.plugin('plugin')
        def plugin_2():
            ...

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert 'plugin-2' not in some_slot


def test_slot_unique_error_has_priority_over_plugin_unique_error(folder_slot):
    """Slot-level uniqueness owns duplicate-name conflicts before plugin-level uniqueness.

    The second plugin also asks to be unique, which would normally produce the
    plugin-level uniqueness message. On a `slot(unique=True)` duplicate, the
    slot policy should fail first, so the test checks the slot-level message and
    that no second plugin remains registered.
    """
    @folder_slot(slot(unique=True))
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin_1():
        ...

    with pytest.raises(PrimadonnaPluginError, match=match('Slot "some_slot" requires unique plugin names, but "plugin" is already registered.')):
        @some_slot.plugin('plugin', unique=True)
        def plugin_2():
            ...

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert 'plugin-2' not in some_slot


def test_slot_unique_keeps_max_priority_before_duplicate_check(folder_slot):
    """The max-plugin limit is still checked before slot-level duplicate names.

    A second plugin with the same requested name would violate `unique=True`,
    but this slot is already full after one registration. The expected
    `TooManyPluginsError` proves the existing max-limit ordering was preserved.
    """
    @folder_slot(slot(unique=True, max=1))
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin_1():
        ...

    with pytest.raises(TooManyPluginsError, match=match('The maximum number of plugins for this slot is 1.')):
        @some_slot.plugin('plugin')
        def plugin_2():
            ...

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert 'plugin-2' not in some_slot


def test_slot_unique_ignores_duplicate_name_when_engine_rejects_plugin(folder_slot, list_type):
    """Engine-incompatible plugins do not participate in slot-level uniqueness.

    The second plugin repeats an existing requested name, but its `engine`
    constraint rejects it before duplicate-name enforcement. The test pins the
    discovered package version to make that engine constraint fail, checks that
    no suffixed plugin appears, and then calls the slot to prove only the
    accepted plugin is installed and executed.
    """
    @folder_slot(slot(unique=True))
    def some_slot() -> list_type:
        return []

    some_slot.code_representation.package_version = Version('0.0.1')

    @some_slot.plugin('plugin')
    def plugin_1():
        return 'accepted'

    @some_slot.plugin('plugin', engine='>1000.0.0')
    def plugin_2():
        return 'rejected'

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert 'plugin-2' not in some_slot
    assert some_slot() == ['accepted']


def test_exceeding_the_limit_0_of_plugins(folder_plugin):
    """max=0 creates a valid slot that rejects every plugin, including the first, with TooManyPluginsError."""
    @slot(max=0)
    def some_slot(a, b):
        ...

    with pytest.raises(TooManyPluginsError, match=match('The maximum number of plugins for this slot is 0.')):
        @folder_plugin(some_slot)
        def kek(a, b):
            ...


def test_exceeding_the_limit_1_of_plugins(folder_plugin):
    """A slot capped at one plugin accepts the first registration and raises TooManyPluginsError for a second registration, for both plugin decorator forms."""
    @slot(max=1)
    def some_slot(a, b):
        ...

    @folder_plugin(some_slot)
    def kek(a, b):
        ...

    with pytest.raises(TooManyPluginsError, match=match('The maximum number of plugins for this slot is 1.')):
        @folder_plugin(some_slot)
        def kek2(a, b):
            ...


def test_exceeding_the_limit_1000_of_plugins(folder_plugin):
    """A slot with max=1000 accepts 1000 explicitly named plugins and rejects the next public plugin registration with TooManyPluginsError."""
    allowed_number_of_plugins = 1000

    @slot(max=allowed_number_of_plugins)
    def some_slot(a, b):
        ...

    for index in range(allowed_number_of_plugins):
        @some_slot.plugin(f'kek{index}')
        def kek(a, b):
            ...

    with pytest.raises(TooManyPluginsError, match=match('The maximum number of plugins for this slot is 1000.')):
        @folder_plugin(some_slot)
        def kek(a, b):
            ...


def test_strange_slot_return_type_annotation(folder_slot):
    """Reject explicit slot return annotations that are not list or dict containers for both @slot forms."""
    with pytest.raises(StrangeTypeAnnotationError, match=match('The return type annotation for a slot must be either a list or a dict, or remain empty.')):
        @folder_slot(slot)
        def some_slot(a, b) -> int:  # type: ignore[empty-body]
            ...


def test_typed_none_slot_still_raises_before_one_can_resolve():
    """None-annotated slots fail during decoration before `.one` can be read."""
    with pytest.raises(StrangeTypeAnnotationError, match=match('The return type annotation for a slot must be either a list or a dict, or remain empty.')):
        @slot
        def some_slot() -> None:
            pass


def test_plugin_name_is_not_valid_python_identifier(folder_slot):
    """Invalid explicit plugin names such as 'lol kek' raise ValueError as soon as the plugin decorator is created."""
    @folder_slot(slot)
    def some_slot(a, b):
        ...

    with pytest.raises(ValueError, match=match('The plugin name must be a valid Python identifier.')):
        @some_slot.plugin('lol kek')
        def some_plugin(a, b):
            ...


def test_slot_return_type_is_dict_but_keys_are_not_str(folder_slot, subscribable_dict_type):
    """Dict slot annotations require str keys because results are keyed by plugin name, so int-keyed annotations are rejected at decoration time."""
    with pytest.raises(TypeError, match=match('Incorrect type annotation for the dict.')):
        @folder_slot(slot)
        def some_slot(a, b) -> subscribable_dict_type[int, int]:
            ...


def test_run_slot_with_empty_dict_annotation(folder_slot, folder_plugin, dict_type):
    """Slots annotated with bare dict/Dict aggregate plugin results by installed plugin name, including suffixed duplicates, without constraining value types."""
    @folder_slot(slot)
    def some_slot(a, b) -> dict_type:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    @folder_plugin(some_slot)
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == {'function_1': 4, 'function_2': 5, 'function_2-2': 6}


def test_run_slot_with_not_empty_dict_annotation(folder_slot, folder_plugin, subscribable_dict_type):
    """A dict[str, int] or typing.Dict[str, int] slot aggregates int plugin returns under final plugin names, including the `function_2-2` duplicate suffix."""
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, int]:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    @folder_plugin(some_slot)
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == {'function_1': 4, 'function_2': 5, 'function_2-2': 6}


def test_run_slot_with_not_empty_wrong_dict_annotation(folder_slot, folder_plugin, subscribable_dict_type):
    """Parameterized dict slots use str keys for plugin names and enforce the value type on each plugin result, so dict[str, str] rejects an integer return."""
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "function_1" return value 4 does not match the expected type str.')):
        some_slot(1, 2)


def test_run_slot_with_not_empty_wrong_dict_annotation_but_type_check_is_off(subscribable_dict_type, folder_plugin):
    """Disabling type checking lets a parameterized dict slot collect plugin results that violate the annotated value type while preserving name keys and duplicate-name suffixes."""
    @slot(type_check=False)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    @folder_plugin(some_slot)
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == {'function_1': 4, 'function_2': 5, 'function_2-2': 6}


def test_run_slot_with_empty_list_annotation(folder_slot, folder_plugin, list_type):
    """Slots annotated with a bare list aggregate plugin results in registration order without element-type checks, even when plugin names collide."""
    @folder_slot(slot)
    def some_slot(a, b) -> list_type:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    @folder_plugin(some_slot)
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_with_not_empty_list_annotation(folder_slot, folder_plugin, subscribable_list_type):
    """A parameterized list slot accepts plugin results matching its element type and returns them as an ordered list, including duplicate-named plugin functions."""
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[int]:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    @folder_plugin(some_slot)
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_with_not_empty_wrong_list_annotation(folder_slot, folder_plugin, subscribable_list_type):
    """Parameterized list slot annotations enforce their item type on plugin results during normal list aggregation, so both builtin and typing.List variants raise on the first int result where str is required."""
    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "function_1" return value 4 does not match the expected type str.')):
        some_slot(1, 2)


def test_run_slot_with_not_empty_wrong_list_annotation_but_type_check_is_off(subscribable_list_type, folder_plugin):
    """type_check=False suppresses plugin result validation without disabling list aggregation, so int results under a str-parameterized list slot are returned as [4, 5, 6]."""
    @slot(type_check=False)
    def some_slot(a, b) -> subscribable_list_type[str]:
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        return a + b + 1

    @folder_plugin(some_slot)
    def function_2(a, b):
        return a + b + 2

    @folder_plugin(some_slot)
    def function_2(a, b):  # noqa: F811
        return a + b + 3

    assert some_slot(1, 2) == [4, 5, 6]


def test_run_slot_without_type_annotation(folder_slot, folder_plugin):
    """An unannotated slot still runs every registered plugin, but discards their return values and returns None."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b):
        ...

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(a + b + 1)
        return bread_crumbs[-1]

    @folder_plugin(some_slot)
    def function_2(a, b):
        bread_crumbs.append(a + b + 2)
        return bread_crumbs[-1]

    @folder_plugin(some_slot)
    def function_2(a, b):  # noqa: F811
        bread_crumbs.append(a + b + 3)
        return bread_crumbs[-1]

    assert some_slot(1, 2) is None
    assert bread_crumbs == [4, 5, 6]


def test_run_not_empty_default_function_without_plugins_without_annotations(folder_slot, folder_plugin):
    """Unannotated slots return None while running side effects from a non-empty default body before plugin registration and from the plugin afterward."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b):
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) is None
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) is None
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_empty_dict_annotation(folder_slot, folder_plugin, dict_type, slot_unique_options):
    """Bare dict/Dict slots use the non-empty body only as the no-plugin fallback, then expose the registered plugin through collection APIs and aggregate its result by name."""
    bread_crumbs = []

    @folder_slot(slot(**slot_unique_options))
    def some_slot(a, b) -> dict_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return {'some_slot': bread_crumbs[-1]}

    assert some_slot(1, 2) == {'some_slot': 'run_slot_3'}
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot.keys() == ('function_1',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['function_1']
    assert [x.name for x in some_slot['function_1']] == ['function_1']
    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_not_empty_dict_annotation(folder_slot, folder_plugin, subscribable_dict_type):
    """Dict[str, str] slots return the default body's own dict when no plugins exist, then skip the body and aggregate registered plugin returns by name."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return {'some_slot': bread_crumbs[-1]}

    assert some_slot(1, 2) == {'some_slot': 'run_slot_3'}
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_empty_list_annotation(folder_slot, folder_plugin, list_type, slot_unique_options):
    """Bare list-annotated slots run a non-empty body only as the no-plugin fallback, then expose the single registered plugin through collection APIs and aggregate its result into a list."""
    bread_crumbs = []

    @folder_slot(slot(**slot_unique_options))
    def some_slot(a, b) -> list_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return [bread_crumbs[-1]]

    assert some_slot(1, 2) == ['run_slot_3']
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot.keys() == ('function_1',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['function_1']
    assert [x.name for x in some_slot['function_1']] == ['function_1']
    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


def test_run_not_empty_default_function_without_plugins_with_not_empty_list_annotation(folder_slot, folder_plugin, subscribable_list_type):
    """Typed-list slots fall back to their non-empty body only when no plugins are registered, then skip it and aggregate a registered scalar string result into the annotated list."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return [bread_crumbs[-1]]

    assert some_slot(1, 2) == ['run_slot_3']
    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_dict_annotation_with_wrong_return_type_new_pythons(folder_slot, folder_plugin, dict_type):
    """On Python 3.10+, an unsubscripted dict/typing.Dict slot validates a non-empty no-plugin fallback as a dict. A scalar fallback raises TypeError with expected `Dict`, and after plugin registration calls skip the fallback and aggregate the plugin result by name."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> dict_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type Dict.')):
        some_slot(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(not (version_info[:2] == (3, 8) or version_info[:2] == (3, 9)), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_dict_annotation_with_wrong_return_type(folder_slot, folder_plugin, dict_type):
    """On Python 3.8/3.9, an unsubscripted dict/typing.Dict slot rejects a scalar no-plugin fallback with the legacy `typing.Dict` TypeError. After plugin registration, calls skip the fallback and aggregate the plugin result by name."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> dict_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type typing.Dict.')):
        some_slot(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_dict_annotation_with_wrong_return_type_new_pythons(folder_slot, folder_plugin, subscribable_dict_type):
    """On Python 3.10+, parameterized dict fallback bodies reject scalar returns and dict key/value mismatches while rendering the expected type as `Dict`. After plugin registration, calls skip the fallback and aggregate the plugin return by name."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return 12

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_dict_type[str, str]:  # noqa: ARG001
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_dict_type[str, str]:
        return {a + b: bread_crumbs[-1]}

    @folder_slot(slot)
    def some_slot_4(a, b) -> subscribable_dict_type[str, str]:
        return {bread_crumbs[-1]: a + b}

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot" return value 12 does not match the expected type Dict.')):
        some_slot(1, 2)

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot_2" return value \'run_slot_3\' does not match the expected type Dict.')):
        some_slot_2(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_3" return value {3: \'run_slot_3\'} does not match the expected type Dict.')):
        some_slot_3(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_4" return value {\'run_slot_3\': 3} does not match the expected type Dict.')):
        some_slot_4(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(not (version_info[:2] == (3, 8) or version_info[:2] == (3, 9)), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_dict_annotation_with_wrong_return_type(folder_slot, folder_plugin, subscribable_dict_type):
    """On Python 3.8/3.9, a parameterized dict slot validates a non-empty no-plugin fallback as a full `typing.Dict[str, str]` result, rejecting scalar returns and bad key/value types. After plugin registration, calls skip the fallback and aggregate plugin results by name."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_dict_type[str, str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return 12

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_dict_type[str, str]:  # noqa: ARG001
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_dict_type[str, str]:
        return {a + b: bread_crumbs[-1]}

    @folder_slot(slot)
    def some_slot_4(a, b) -> subscribable_dict_type[str, str]:
        return {bread_crumbs[-1]: a + b}

    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot" return value 12 does not match the expected type typing.Dict[str, str].')):
        some_slot(1, 2)

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot_2" return value \'run_slot_3\' does not match the expected type typing.Dict[str, str].')):
        some_slot_2(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_3" return value {3: \'run_slot_3\'} does not match the expected type typing.Dict[str, str].')):
        some_slot_3(1, 2)

    with pytest.raises(TypeError, match=match('The type dict of the plugin\'s "some_slot_4" return value {\'run_slot_3\': 3} does not match the expected type typing.Dict[str, str].')):
        some_slot_4(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == {'function_1': 'run_plugin_3'}
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_list_annotation_with_wrong_return_type_new_pythons(folder_slot, folder_plugin, list_type):
    """On Python 3.10+, an unsubscripted list/typing.List slot validates a non-empty no-plugin fallback as a list. String and integer fallbacks raise TypeError with expected `List`; after plugin registration, calls skip the fallback and aggregate plugin results into a list."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> list_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> list_type:
        return a + b

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type List.')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type List.')):
        some_slot_2(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(not (version_info[:2] == (3, 8) or version_info[:2] == (3, 9)), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_empty_list_annotation_with_wrong_return_type(folder_slot, folder_plugin, list_type):
    """On Python 3.8/3.9, an unsubscripted list/typing.List slot validates a non-empty no-plugin fallback as a list. Scalar fallbacks raise TypeError with expected `typing.List`; after plugin registration, calls skip the fallback and aggregate plugin results into a list."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> list_type:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> list_type:
        return a + b

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type typing.List.')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type typing.List.')):
        some_slot_2(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info >= (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_list_annotation_with_wrong_return_type(folder_slot, folder_plugin, subscribable_list_type):
    """
    On Python before 3.9, a parameterized List[str] slot validates the no-plugin fallback as the whole list result.

    A string scalar, an integer scalar, and a list with a non-str item all raise the legacy typing.List[str] TypeError. After a plugin is registered, the fallback is skipped and the plugin's str result is aggregated.
    """
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_list_type[str]:
        return a + b

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_list_type[str]:
        return [a + b]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type typing.List[str].')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type typing.List[str].')):
        some_slot_2(1, 2)
    with pytest.raises(TypeError, match=match('The type list of the plugin\'s "some_slot_3" return value [3] does not match the expected type typing.List[str].')):
        some_slot_3(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


@pytest.mark.skipif(version_info[:2] == (3, 8) or version_info[:2] == (3, 9), reason='On new versions of Python, there is an another mechanism of printing type annotations.')
def test_run_not_empty_default_function_without_plugins_with_not_empty_list_annotation_with_wrong_return_type_new_pythons(folder_slot, folder_plugin, subscribable_list_type):
    """Type-checked parameterized list slots validate a non-empty fallback body as the whole list result before any plugins exist. On Python 3.10+, bad scalar returns and wrong item types report expected type List, while a later registered plugin bypasses the fallback and is aggregated normally."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b) -> subscribable_list_type[str]:
        bread_crumbs.append(f'run_slot_{a + b}')
        return bread_crumbs[-1]

    @folder_slot(slot)
    def some_slot_2(a, b) -> subscribable_list_type[str]:
        return a + b

    @folder_slot(slot)
    def some_slot_3(a, b) -> subscribable_list_type[str]:
        return [a + b]

    with pytest.raises(TypeError, match=match('The type str of the plugin\'s "some_slot" return value \'run_slot_3\' does not match the expected type List.')):
        some_slot(1, 2)
    with pytest.raises(TypeError, match=match('The type int of the plugin\'s "some_slot_2" return value 3 does not match the expected type List.')):
        some_slot_2(1, 2)
    with pytest.raises(TypeError, match=match('The type list of the plugin\'s "some_slot_3" return value [3] does not match the expected type List.')):
        some_slot_3(1, 2)

    assert bread_crumbs == ['run_slot_3']

    bread_crumbs.pop()

    @folder_plugin(some_slot)
    def function_1(a, b):
        bread_crumbs.append(f'run_plugin_{a + b}')
        return bread_crumbs[-1]

    assert some_slot(1, 2) == ['run_plugin_3']
    assert bread_crumbs == ['run_plugin_3']


def test_getitem_bad_key(folder_slot, folder_plugin):
    """Invalid slot selection keys raise KeyError with the public invalid-key message instead of producing a selection. This covers malformed strings and non-string keys."""
    @folder_slot(slot)
    def some_slot():
        ...

    @folder_plugin(some_slot)
    def plugin():
        ...

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        ...

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        ...

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot['kek-kek']

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot['kek--']

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot[123]

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot[True]


def test_getitem_good_key(folder_slot, folder_plugin):
    """Bracket lookup on a slot selects plugins by valid base and numeric-suffix keys. Duplicate requested names are returned together by the base key, suffixes select exact duplicates with name-1 meaning the first plugin, and valid missing keys return an empty selection."""
    @folder_slot(slot)
    def some_slot():
        ...

    @folder_plugin(some_slot)
    def plugin():
        ...

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        ...

    @folder_plugin(some_slot)
    def plugin2():
        ...

    assert some_slot['plugin']
    assert len(some_slot['plugin']) == 2
    assert [x.name for x in some_slot['plugin']] == ['plugin', 'plugin-2']

    assert some_slot['plugin-1']
    assert len(some_slot['plugin-1']) == 1
    assert [x.name for x in some_slot['plugin-1']] == ['plugin']

    assert some_slot['plugin-2']
    assert len(some_slot['plugin-2']) == 1
    assert [x.name for x in some_slot['plugin-2']] == ['plugin-2']

    assert some_slot['plugin2']
    assert len(some_slot['plugin2']) == 1
    assert [x.name for x in some_slot['plugin2']] == ['plugin2']

    assert not some_slot['kek']
    assert len(some_slot['kek']) == 0
    assert [x.name for x in some_slot['kek']] == []

    assert not some_slot['kek-2']
    assert len(some_slot['kek-2']) == 0
    assert [x.name for x in some_slot['kek-2']] == []


def test_getitem_call(folder_slot, folder_plugin):
    """Item lookup returns a callable narrowed slot selection that calls matching plugins, including duplicate base-name plugins in registration order, and falls back to the slot body for a valid missing key."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot():
        bread_crumbs.append('some_slot')

    @folder_plugin(some_slot)
    def plugin():
        bread_crumbs.append('plugin_1')

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        bread_crumbs.append('plugin_2')

    @folder_plugin(some_slot)
    def plugin2():
        bread_crumbs.append('plugin_3')

    some_slot['plugin']()

    assert bread_crumbs == ['plugin_1', 'plugin_2']

    bread_crumbs.clear()

    some_slot['plugin2']()

    assert bread_crumbs == ['plugin_3']

    bread_crumbs.clear()

    some_slot['kek']()

    assert bread_crumbs == ['some_slot']

    bread_crumbs.clear()


def test_getitem_call_with_parameters(folder_slot, folder_plugin):
    """
    Calling a selected slot by key forwards arguments to the selected callables while preserving their defaults.

    Duplicate-name selections call both duplicate plugins, named selections call only that plugin, and a valid missing key falls back to the slot body with the same argument/default behavior.
    """
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b=3):
        bread_crumbs.append(f'some_slot_{a}_{b}')

    @folder_plugin(some_slot)
    def plugin(a, b=4):
        bread_crumbs.append(f'plugin_1_{a}_{b}')

    @folder_plugin(some_slot)
    def plugin(a, b=5):  # noqa: F811
        bread_crumbs.append(f'plugin_2_{a}_{b}')

    @folder_plugin(some_slot)
    def plugin2(a, b=6):
        bread_crumbs.append(f'plugin_3_{a}_{b}')

    some_slot['plugin'](1)

    assert bread_crumbs == ['plugin_1_1_4', 'plugin_2_1_5']

    bread_crumbs.clear()

    some_slot['plugin2'](1)

    assert bread_crumbs == ['plugin_3_1_6']

    bread_crumbs.clear()

    some_slot['kek'](1)

    assert bread_crumbs == ['some_slot_1_3']

    bread_crumbs.clear()

    some_slot['plugin'](1, 2)

    assert bread_crumbs == ['plugin_1_1_2', 'plugin_2_1_2']

    bread_crumbs.clear()

    some_slot['plugin2'](1, 2)

    assert bread_crumbs == ['plugin_3_1_2']

    bread_crumbs.clear()

    some_slot['kek'](1, 2)

    assert bread_crumbs == ['some_slot_1_2']

    bread_crumbs.clear()


def test_repr(folder_slot):
    """Pin the exact Slot repr produced by the public slot decorator. Default options are omitted, configured non-defaults appear in stable order, @slot and @slot() stay minimal, custom names render as slot_name whether passed as name=... or a positional string, and list signatures are shown as list values."""
    @folder_slot(slot)
    def some_slot(a, b=3):
        ...

    @slot(name='name')
    def some_slot_2(a, b=3):
        ...

    @slot(name='name2', signature='..')
    def some_slot_3(a, b=3):
        ...

    @slot(name='name3', signature='..', max=3)
    def some_slot_4(a, b=3):
        ...

    @slot(name='name4', signature='..', max=3, type_check=False)
    def some_slot_5(a, b=3):
        ...

    @slot('name5', signature='..', max=3, type_check=False)
    def some_slot_6(a, b=3):
        ...

    @slot('name6', signature='..', max=3, type_check=False, unique=True)
    def some_slot_7(a, b=3):
        ...

    @slot(name='name7', signature=['..', '.'])
    def some_slot_8(a, b=3):
        ...

    @slot(name='name8', explicit_plugin_names=True)
    def some_slot_9(a, b=3):
        ...

    assert repr(some_slot) == 'Slot(some_slot)'
    assert repr(some_slot_2) == 'Slot(some_slot_2, slot_name=\'name\')'
    assert repr(some_slot_3) == 'Slot(some_slot_3, signature=\'..\', slot_name=\'name2\')'
    assert repr(some_slot_4) == 'Slot(some_slot_4, signature=\'..\', slot_name=\'name3\', max=3)'
    assert repr(some_slot_5) == 'Slot(some_slot_5, signature=\'..\', slot_name=\'name4\', max=3, type_check=False)'
    assert repr(some_slot_6) == 'Slot(some_slot_6, signature=\'..\', slot_name=\'name5\', max=3, type_check=False)'
    assert repr(some_slot_7) == 'Slot(some_slot_7, signature=\'..\', slot_name=\'name6\', max=3, type_check=False, unique=True)'
    assert repr(some_slot_8) == 'Slot(some_slot_8, signature=[\'..\', \'.\'], slot_name=\'name7\')'
    assert repr(some_slot_9) == 'Slot(some_slot_9, slot_name=\'name8\', explicit_plugin_names=True)'


def test_getitem_repr(folder_slot, folder_plugin):
    """Base-name slot selection repr shows the live SlotCaller(slot=Slot(...)) and both duplicate plugins, including the generated -2 name."""
    @folder_slot(slot)
    def some_slot(a, b=3):
        ...

    @folder_plugin(some_slot)
    def plugin(a, b=3):
        ...

    @folder_plugin(some_slot)
    def plugin(a, b=3):  # noqa: F811
        ...

    assert repr(some_slot['plugin']) == 'CallerWithPlugins(caller=SlotCaller(slot=Slot(some_slot)), plugins=[Plugin(\'plugin\', plugin_function=plugin, expected_result_type=InnerNoneType(1), type_check=True, unique=False), Plugin(\'plugin-2\', plugin_function=plugin, expected_result_type=InnerNoneType(1), type_check=True, unique=False)])'


def test_keys(folder_slot, folder_plugin):
    """keys() reports requested plugin-name groups without duplicate suffixes, so duplicate `plugin` registrations and distinct `plugin2` appear as `('plugin', 'plugin2')` while an empty slot returns `()`."""
    @folder_slot(slot)
    def slot_1():
        ...

    @folder_plugin(slot_1)
    def plugin():
        ...

    @folder_plugin(slot_1)
    def plugin():  # noqa: F811
        ...

    @folder_plugin(slot_1)
    def plugin2():
        ...

    @folder_slot(slot)
    def slot_2():
        ...

    assert slot_1.keys() == ('plugin', 'plugin2')
    assert slot_2.keys() == ()


def test_getitem_is_loading_entry_points(folder_slot):
    """Indexing a public slot by name resolves lazy entry points even when the name selects no plugins."""
    @folder_slot(slot)
    def some_slot():
        ...

    assert not some_slot.loaded

    some_slot['kek']

    assert some_slot.loaded


def test_iter_is_loading_entry_points(folder_slot, folder_plugin):
    """Iterating a public slot resolves lazy entry points before yielding any plugin. The slot is already marked loaded inside the first loop iteration and remains loaded afterward."""
    @folder_slot(slot)
    def some_slot():
        ...

    @folder_plugin(some_slot)
    def plugin():
        ...

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        ...

    assert not some_slot.loaded

    for _ in some_slot:
        assert some_slot.loaded

    assert some_slot.loaded


def test_getting_keys_is_loading_entry_points(folder_slot, folder_plugin):
    """Reading public slot keys lazily loads entry points and reports duplicate requested plugin names as one base key."""
    @folder_slot(slot)
    def some_slot():
        ...

    @folder_plugin(some_slot)
    def plugin():
        ...

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        ...

    assert not some_slot.loaded

    assert some_slot.keys() == ('plugin',)

    assert some_slot.loaded


def test_delitem_removes_plugins_from_slot(folder_slot, folder_plugin):
    """
    Deleting a plugin by base name removes the entire requested-name group, including suffixed duplicates.

    Across public slot/plugin decorator variants, unrelated plugins remain registered and indexed, and the next call runs only those survivors rather than deleted plugins or the default body. This pins base-name deletion, not exact-key deletion or pop behavior.
    """
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot():
        bread_crumbs.append('slot')

    @folder_plugin(some_slot)
    def plugin():
        bread_crumbs.append('plugin_1')

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        bread_crumbs.append('plugin_2')

    @folder_plugin(some_slot)
    def plugin2():
        bread_crumbs.append('plugin2')

    del some_slot['plugin']

    assert [x.name for x in some_slot.plugins.plugins] == ['plugin2']
    assert some_slot.plugins.plugins_by_requested_names == {
        'plugin2': [some_slot.plugins.plugins[0]],
    }
    assert some_slot.keys() == ('plugin2',)
    assert len(some_slot) == 1
    assert 'plugin' not in some_slot

    some_slot()

    assert bread_crumbs == ['plugin2']


def test_pop_removes_plugin_and_returns_detached_selection(folder_slot):
    """Popping an exact duplicate key removes only that plugin, not the duplicate group, and returns a detached selection. For `pop('plugin-2')`, the parent compacts survivors so `plugin-2` can name a different plugin, while the returned selection still calls the removed plugin and the parent slot no longer does."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a):
        bread_crumbs.append(f'slot_{a}')

    @some_slot.plugin('plugin')
    def plugin_1(a):
        bread_crumbs.append(f'plugin_1_{a}')

    @some_slot.plugin('plugin')
    def plugin_2(a):
        bread_crumbs.append(f'plugin_2_{a}')

    @some_slot.plugin('plugin')
    def plugin_3(a):
        bread_crumbs.append(f'plugin_3_{a}')

    removed_plugins = some_slot.pop('plugin-2')

    assert [x.name for x in removed_plugins] == ['plugin-2']
    assert [x.name for x in some_slot.plugins.plugins] == ['plugin', 'plugin-2']
    assert some_slot.keys() == ('plugin',)

    removed_plugins(1)

    assert bread_crumbs == ['plugin_2_1']

    bread_crumbs.clear()

    some_slot(1)

    assert bread_crumbs == ['plugin_1_1', 'plugin_3_1']


def test_delitem_by_base_name_last_list_plugin_falls_back_to_slot_body(folder_slot, subscribable_list_type, slot_unique_options):
    """
    Deleting the only list-slot plugin by base name clears the collection and restores the slot body fallback.

    The fallback returns an empty list here, so a side effect is what proves the body ran instead of a stale plugin.
    """
    body_calls = []

    @folder_slot(slot(**slot_unique_options))
    def some_slot(a) -> subscribable_list_type[int]:
        body_calls.append(a)
        return []

    @some_slot.plugin('plugin')
    def plugin_1(a):
        return a

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert some_slot(1) == [1]
    assert body_calls == []

    del some_slot['plugin']

    assert some_slot.keys() == ()
    assert len(some_slot) == 0
    assert 'plugin' not in some_slot
    assert 'plugin-1' not in some_slot
    assert [x.name for x in some_slot] == []
    assert some_slot(1) == []
    assert body_calls == [1]


def test_pop_by_base_name_last_list_plugin_falls_back_to_slot_body(folder_slot, subscribable_list_type, slot_unique_options):
    """
    Popping the only list-slot plugin by base name returns a detached selection while restoring parent fallback.

    The detached selection can still call the removed plugin. The parent collection becomes empty, and later parent calls run the slot body fallback, which returns an empty list and is observed through a side effect.
    """
    body_calls = []

    @folder_slot(slot(**slot_unique_options))
    def some_slot(a) -> subscribable_list_type[int]:
        body_calls.append(a)
        return []

    @some_slot.plugin('plugin')
    def plugin_1(a):
        return a

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert some_slot(1) == [1]
    assert body_calls == []

    removed_plugins = some_slot.pop('plugin')

    assert [x.name for x in removed_plugins] == ['plugin']
    assert removed_plugins(2) == [2]
    assert some_slot.keys() == ()
    assert len(some_slot) == 0
    assert 'plugin' not in some_slot
    assert 'plugin-1' not in some_slot
    assert [x.name for x in some_slot] == []
    assert some_slot(2) == []
    assert body_calls == [2]


def test_delitem_by_base_name_removes_group_from_list_slot_call(folder_slot, subscribable_list_type):
    """Deleting plugins by base name removes the whole duplicate-name group from slot state and later list-aggregated calls while preserving other plugin groups."""
    @folder_slot(slot)
    def some_slot(a) -> subscribable_list_type[int]:  # noqa: ARG001
        return []

    @some_slot.plugin('plugin')
    def plugin_1(a):
        return a

    @some_slot.plugin('plugin')
    def plugin_2(a):
        return a + 1

    @some_slot.plugin('other')
    def other(a):
        return a + 2

    assert some_slot(1) == [1, 2, 3]

    del some_slot['plugin']

    assert some_slot.keys() == ('other',)
    assert len(some_slot) == 1
    assert 'plugin' not in some_slot
    assert 'plugin-1' not in some_slot
    assert 'plugin-2' not in some_slot
    assert 'other' in some_slot
    assert [x.name for x in some_slot] == ['other']
    assert some_slot(1) == [3]


def test_pop_by_base_name_returns_detached_group_and_keeps_survivors_in_list_slot_call(folder_slot, subscribable_list_type):
    """Base-name pop detaches all duplicate plugins with that declared name as a callable selection while the parent list slot keeps unrelated survivors."""
    @folder_slot(slot)
    def some_slot(a) -> subscribable_list_type[int]:  # noqa: ARG001
        return []

    @some_slot.plugin('plugin')
    def plugin_1(a):
        return a

    @some_slot.plugin('plugin')
    def plugin_2(a):
        return a + 1

    @some_slot.plugin('other')
    def other(a):
        return a + 2

    assert some_slot(1) == [1, 2, 3]

    removed_plugins = some_slot.pop('plugin')

    assert [x.name for x in removed_plugins] == ['plugin', 'plugin-2']
    assert removed_plugins(1) == [1, 2]
    assert some_slot.keys() == ('other',)
    assert len(some_slot) == 1
    assert 'plugin' not in some_slot
    assert 'plugin-1' not in some_slot
    assert 'plugin-2' not in some_slot
    assert 'other' in some_slot
    assert [x.name for x in some_slot] == ['other']
    assert some_slot(1) == [3]


def test_delitem_by_base_name_removes_group_from_dict_slot_call(folder_slot, subscribable_dict_type):
    """Deleting by base requested plugin name from a dict-returning slot removes every duplicate in that group before the next call, leaving unrelated plugin results intact."""
    @folder_slot(slot)
    def some_slot(a) -> subscribable_dict_type[str, int]:  # noqa: ARG001
        return {}

    @some_slot.plugin('plugin')
    def plugin_1(a):
        return a

    @some_slot.plugin('plugin')
    def plugin_2(a):
        return a + 1

    @some_slot.plugin('other')
    def other(a):
        return a + 2

    assert some_slot(1) == {'plugin': 1, 'plugin-2': 2, 'other': 3}

    del some_slot['plugin']

    assert some_slot.keys() == ('other',)
    assert len(some_slot) == 1
    assert 'plugin' not in some_slot
    assert 'plugin-1' not in some_slot
    assert 'plugin-2' not in some_slot
    assert 'other' in some_slot
    assert [x.name for x in some_slot] == ['other']
    assert some_slot(1) == {'other': 3}


def test_pop_by_base_name_returns_detached_group_and_keeps_survivors_in_dict_slot_call(folder_slot, subscribable_dict_type):
    """
    Base-name pop detaches all plugins sharing a requested name while preserving dict aggregation by actual name.

    The returned selection remains callable with duplicate suffixes, and the parent slot keeps unrelated survivors visible through keys, len, contains, iteration, and later calls.
    """
    @folder_slot(slot)
    def some_slot(a) -> subscribable_dict_type[str, int]:  # noqa: ARG001
        return {}

    @some_slot.plugin('plugin')
    def plugin_1(a):
        return a

    @some_slot.plugin('plugin')
    def plugin_2(a):
        return a + 1

    @some_slot.plugin('other')
    def other(a):
        return a + 2

    assert some_slot(1) == {'plugin': 1, 'plugin-2': 2, 'other': 3}

    removed_plugins = some_slot.pop('plugin')

    assert [x.name for x in removed_plugins] == ['plugin', 'plugin-2']
    assert removed_plugins(1) == {'plugin': 1, 'plugin-2': 2}
    assert some_slot.keys() == ('other',)
    assert len(some_slot) == 1
    assert 'plugin' not in some_slot
    assert 'plugin-1' not in some_slot
    assert 'plugin-2' not in some_slot
    assert 'other' in some_slot
    assert [x.name for x in some_slot] == ['other']
    assert some_slot(1) == {'other': 3}


def test_pop_returns_default_for_missing_key(folder_slot):
    """pop returns the exact supplied default for a missing valid plugin key, including None."""
    @folder_slot(slot)
    def some_slot():
        ...

    sentinel = object()

    assert some_slot.pop('missing', sentinel) is sentinel
    assert some_slot.pop('missing', None) is None


def test_pop_and_delitem_raise_key_error_for_empty_slot(folder_slot):
    """An empty slot still raises KeyError for removal of a valid but absent plugin key by no-default pop or del."""
    @folder_slot(slot)
    def some_slot():
        ...

    with pytest.raises(KeyError, match=match("'missing'")):
        some_slot.pop('missing')

    with pytest.raises(KeyError, match=match("'missing'")):
        del some_slot['missing']


def test_pop_and_delitem_raise_key_error_for_non_string_keys(folder_slot):
    """Public slot removal via pop or del raises KeyError with the invalid-key message for non-string keys passed at runtime."""
    @folder_slot(slot)
    def some_slot():
        ...

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        some_slot.pop(None)  # type: ignore[arg-type]

    with pytest.raises(KeyError, match=match('\'You have used an invalid key. Strings that are suitable as keys are valid Python identifiers, or the same strings with a number separated by a hyphen (e.g., "a", "a-5").\'')):
        del some_slot[None]  # type: ignore[index]


def test_deleting_plugin_prevents_it_from_running(folder_slot):
    """Deleting a duplicate plugin by its numbered key removes only that plugin from later slot dispatch, so subsequent calls run the remaining duplicates in order and skip the deleted one."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot(a, b=3):
        bread_crumbs.append(f'some_slot_{a}_{b}')

    @some_slot.plugin('plugin')
    def plugin_1(a, b=4):
        bread_crumbs.append(f'plugin_1_{a}_{b}')

    @some_slot.plugin('plugin')
    def plugin_2(a, b=5):
        bread_crumbs.append(f'plugin_2_{a}_{b}')

    @some_slot.plugin('plugin')
    def plugin_3(a, b=6):
        bread_crumbs.append(f'plugin_3_{a}_{b}')

    del some_slot['plugin-2']
    some_slot(1)

    assert bread_crumbs == ['plugin_1_1_4', 'plugin_3_1_6']


def test_delitem_and_pop_support_exact_duplicate_keys(folder_slot):
    """Exact numbered duplicate keys work across deletion, renumbering, and pop. Deleting `plugin-1` removes the unsuffixed first duplicate, renumbers survivors, and a later `pop('plugin-2')` detaches only the current `plugin-2` while leaving the parent with the other survivor."""
    bread_crumbs = []

    @folder_slot(slot)
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin_1():
        bread_crumbs.append('plugin_1')

    @some_slot.plugin('plugin')
    def plugin_2():
        bread_crumbs.append('plugin_2')

    @some_slot.plugin('plugin')
    def plugin_3():
        bread_crumbs.append('plugin_3')

    del some_slot['plugin-1']

    assert [x.name for x in some_slot.plugins.plugins] == ['plugin', 'plugin-2']

    some_slot()

    assert bread_crumbs == ['plugin_2', 'plugin_3']

    bread_crumbs.clear()

    removed_plugins = some_slot.pop('plugin-2')

    assert [x.name for x in removed_plugins] == ['plugin-2']
    assert [x.name for x in some_slot.plugins.plugins] == ['plugin']

    removed_plugins()

    assert bread_crumbs == ['plugin_3']

    bread_crumbs.clear()

    some_slot()

    assert bread_crumbs == ['plugin_2']


def test_delitem_is_loading_entry_points(folder_slot):
    """Deleting a missing valid key from an unloaded public slot loads entry points before raising KeyError, so the slot is marked loaded."""
    @folder_slot(slot)
    def some_slot():
        ...

    assert not some_slot.loaded

    with pytest.raises(KeyError, match=match("'kek'")):
        del some_slot['kek']

    assert some_slot.loaded


def test_pop_is_loading_entry_points(folder_slot):
    """pop() loads entry points before raising KeyError for a missing plugin key, leaving the slot marked loaded."""
    @folder_slot(slot)
    def some_slot():
        ...

    assert not some_slot.loaded

    with pytest.raises(KeyError, match=match("'kek'")):
        some_slot.pop('kek')

    assert some_slot.loaded


def test_deleting_plugins_is_protected_by_slot_lock(folder_slot):
    """Exact-key deletion of a duplicate plugin keeps both removal and survivor renumbering inside the slot lock."""
    @folder_slot(slot)
    def some_slot():
        ...

    @some_slot.plugin('plugin')
    def plugin_1():
        ...

    @some_slot.plugin('plugin')
    def plugin_2():
        ...

    @some_slot.plugin('plugin')
    def plugin_3():
        ...

    some_slot.lock = LockTraceWrapper(RLock())
    original_pop = some_slot.plugins.pop
    original_rename = some_slot.plugins._rename_duplicates

    def traced_pop(key):
        some_slot.lock.notify('delete')
        return original_pop(key)

    def traced_rename(name):
        some_slot.lock.notify('renumber')
        return original_rename(name)

    some_slot.plugins.pop = traced_pop
    some_slot.plugins._rename_duplicates = traced_rename

    del some_slot['plugin-2']

    assert some_slot.lock.was_event_locked('delete')
    assert some_slot.lock.was_event_locked('renumber')


def test_pass_to_plugin_decorator_something_wrong(folder_slot):
    """Slot.plugin raises the generic TypeError for both @slot and @slot() slots when the first decorator argument is neither a callable plugin nor a plugin-name string."""
    @folder_slot(slot)
    def some_slot():
        ...

    with pytest.raises(TypeError, match=match('Only a function or plugin name followed by a function can be passed to the decorator.')):
        some_slot.plugin(123)


def test_pass_two_slot_names_different_ways():
    """The slot decorator rejects conflicting positional and keyword slot names instead of silently preferring either value."""
    with pytest.raises(ValueError, match=match('You have specified two different names for the slot.')):
        @slot('lol', name='kek')
        def some_slot():
            ...


def test_positional_name_is_same_as_keyword():
    """A positional string passed to @slot is treated as the explicit slot name, so @slot('lol') sets slot_name to 'lol'."""
    @slot('lol')
    def some_slot():
        ...

    assert some_slot.slot_name == 'lol'


def test_contains_plugins(folder_slot, folder_plugin):
    """String membership on a public slot recognizes registered plugin names and aliases.\n\nAfter normal decorator registration, requested base names are present, the first plugin is also present through its `-1` alias, later duplicates are present through real suffixes such as `-2`, and missing suffixes or unrelated names are absent."""
    @folder_slot(slot)
    def some_slot():
        ...

    @folder_plugin(some_slot)
    def plugin():
        ...

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        ...

    @folder_plugin(some_slot)
    def plugin2():
        ...

    assert 'plugin' in some_slot
    assert 'plugin-1' in some_slot
    assert 'plugin-2' in some_slot
    assert 'plugin2' in some_slot
    assert 'plugin2-1' in some_slot

    assert 'plugin-3' not in some_slot
    assert 'plugin3' not in some_slot
    assert 'plugin3-1' not in some_slot
    assert 'plugin3-2' not in some_slot
    assert 'kek' not in some_slot


def test_len(folder_slot, folder_plugin):
    """len() reports plugin counts for slots and named selections, including duplicate base-name buckets, numbered aliases like -1, and zero for empty or missing selections."""
    @folder_slot(slot)
    def empty_slot():
        ...

    @folder_slot(slot)
    def some_slot():
        ...

    @folder_plugin(some_slot)
    def plugin():
        ...

    @folder_plugin(some_slot)
    def plugin():  # noqa: F811
        ...

    @folder_plugin(some_slot)
    def plugin2():
        ...

    assert len(empty_slot) == 0
    assert len(empty_slot['kek']) == 0

    assert len(some_slot) == 3
    assert len(some_slot['plugin']) == 2
    assert len(some_slot['plugin2']) == 1

    assert len(some_slot['plugin-1']) == 1
    assert len(some_slot['plugin-2']) == 1

    assert len(some_slot['plugin2-1']) == 1

    assert len(some_slot['plugin-3']) == 0
    assert len(some_slot['plugin2-2']) == 0
    assert len(some_slot['kek']) == 0


@pytest.mark.parametrize(
    'tag',
    [
        '>0.0.0',
        '<1000.0.0',
    ],
)
def test_check_engine_is_newer_than_zero(tag, folder_slot):
    """Satisfied engine constraints register plugins for the slot; with package version 0.0.1, both >0.0.0 and <1000.0.0 make the plugin visible by containment."""
    @folder_slot(slot)
    def some_slot():
        ...

    some_slot.code_representation.package_version = Version('0.0.1')

    @some_slot.plugin(engine=tag)
    def plugin():
        ...

    assert 'plugin' in some_slot


def test_check_engine_is_older_than_1000(folder_slot):
    """Plugins requiring a newer engine than the slot package version are skipped without error."""
    @folder_slot(slot)
    def some_slot():
        ...

    some_slot.code_representation.package_version = Version('0.0.1')

    @some_slot.plugin(engine='>1000.0.0')
    def plugin():
        ...

    assert 'plugin' not in some_slot


def test_by_default_get_version_of_tests_package_is_impossible(folder_slot):
    """
    Engine-constrained plugin registration requires a discoverable version for the package that declares the slot.

    A slot declared in the local tests package has no package version by default, so applying @slot.plugin(engine=...) raises CannotGetVersionsError instead of installing or silently skipping the plugin.
    """
    @folder_slot(slot)
    def some_slot():
        ...

    with pytest.raises(CannotGetVersionsError, match=match('It is not possible to obtain the name of the package in which the slot is declared.')):
        @some_slot.plugin(engine='>1000.0.0')
        def plugin():
            ...


def test_check_engine_is_in_some_range(folder_slot):
    """A plugin with engine version constraints supplied as a list is installed when the slot package version satisfies every constraint, as Version('0.0.2') does for >0.0.1 and <0.0.3."""
    @folder_slot(slot)
    def some_slot():
        ...

    some_slot.code_representation.package_version = Version('0.0.2')

    @some_slot.plugin(engine=['>0.0.1', '<0.0.3'])
    def plugin():
        ...

    assert 'plugin' in some_slot


def test_check_engine_is_not_in_some_range(folder_slot):
    """Plugins constrained by a list of engine expressions are not registered when the slot package version fails the upper bound despite satisfying the lower bound."""
    @folder_slot(slot)
    def some_slot():
        ...

    some_slot.code_representation.package_version = Version('0.0.4')

    @some_slot.plugin(engine=['>0.0.1', '<0.0.3'])
    def plugin():
        ...

    assert 'plugin' not in some_slot


def test_run_once_off(folder_slot, folder_plugin, subscribable_list_type, slot_unique_options):
    """Plugins registered with the default run_once=False remain reusable across repeated slot calls, dispatching with fresh arguments and staying visible in the slot collection."""
    @folder_slot(slot(**slot_unique_options))
    def some_slot(x, y) -> subscribable_list_type[int]:  # noqa: ARG001
        return []

    @folder_plugin(some_slot)
    def plugin(x, y):
        return x + y

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert some_slot(1, 2) == [3]
    assert some_slot(1, 3) == [4]


def test_run_once_on(folder_slot, subscribable_list_type, slot_unique_options):
    """A run-once plugin is enforced across repeated slot calls for the parametrized slot forms and unique settings: the first call aggregates its result, and the second raises NumberOfCallsError."""
    @folder_slot(slot(**slot_unique_options))
    def some_slot(x, y) -> subscribable_list_type[int]:  # noqa: ARG001
        return []

    @some_slot.plugin(run_once=True)
    def plugin(x, y):
        return x + y

    assert some_slot.keys() == ('plugin',)
    assert len(some_slot) == 1
    assert [x.name for x in some_slot] == ['plugin']
    assert [x.name for x in some_slot['plugin']] == ['plugin']
    assert some_slot(1, 2) == [3]

    with pytest.raises(NumberOfCallsError, match=match('A limit of 1 has been set on the number of calls for plugin "plugin". And this plugin has already been called previously.')):
        some_slot(3, 4)
