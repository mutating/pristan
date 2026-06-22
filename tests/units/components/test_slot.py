from typing import Dict, List

import pytest
from full_match import match

import pristan.components.slot as slot_module
from pristan.components.slot import Slot
from pristan.errors import (
    EntrypointLoadingError,
    PrimadonnaPluginError,
    PristanException,
)


def test_set_max_less_than_zero():
    with pytest.raises(ValueError, match=match('The maximum number of plugins cannot be less than zero.')):
        Slot(lambda x: x, '.', 'slot_name', -1, False, 'pristan', False)


def test_bool_loads_entrypoints_before_checking_local_plugins(monkeypatch):
    """Local plugins do not short-circuit entry point loading.

    The slot already has a local plugin, so an implementation that checked
    local plugin presence first would return True. The failing provider proves
    that bool resolves entry points before looking at the local collection.
    """
    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    @slot.plugin
    def plugin():
        raise AssertionError('plugin was executed')

    provider_error = KeyError('provider')

    def get_entries(group=None):
        assert group == 'pristan'
        raise provider_error

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert len(slot) == 1

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        bool(slot)

    assert exception_info.value.__cause__ is provider_error
    assert not slot.loaded


def test_bool_passes_custom_entrypoint_group(monkeypatch):
    """Bool uses the configured entry point group when it resolves plugins."""
    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'custom-group', False)

    def get_entries(group=None):
        assert group == 'custom-group'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert not bool(slot)

    assert slot.loaded


def test_bool_is_idempotent_after_successful_loading(monkeypatch):
    """A successfully loaded slot is not resolved again by repeated bool calls."""
    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    provider_calls = []

    class FakeEntryPoint:
        def load(self):
            @slot.plugin('plugin')
            def plugin():
                return None

    def get_entries(group=None):
        provider_calls.append(group)
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)
    assert bool(slot)

    assert provider_calls == ['pristan']
    assert [plugin.name for plugin in slot.plugins.plugins] == ['plugin']


def test_bool_does_not_execute_default_or_plugins(monkeypatch):
    """Truthiness does not call the slot body or registered plugin functions."""
    def default():
        raise AssertionError('default body was executed')

    slot = Slot(default, None, None, None, True, 'pristan', False)

    @slot.plugin
    def plugin():
        raise AssertionError('plugin was executed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)


def test_bool_short_circuits_default_body_when_plugins_exist(monkeypatch):
    """A present plugin makes bool true without reading fallback body state."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    @slot.plugin
    def plugin():
        raise AssertionError('plugin was executed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot.caller.code_representation = BrokenCodeRepresentation()
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)


def test_bool_with_empty_loaded_entrypoints_depends_on_default_body(monkeypatch):
    """Empty loaded entry points leave truthiness to current body detection.

    All representative body shapes are declared inside this test and then
    checked as one table, so the body-source examples stay close to the
    expectation they document without module-level support functions.
    """
    def empty_body():
        pass

    def ellipsis_body():
        ...

    def docstring_body():
        """Only a docstring."""

    def docstring_with_pass_body():
        """Docstring plus pass."""
        pass  # noqa: PIE790

    def empty_list_body() -> List[int]:
        return []

    def empty_dict_body() -> Dict[str, int]:
        return {}

    def bare_return_body():
        return

    def none_return_body():
        return None

    def unannotated_list_body():
        return []

    def docstring_with_annotated_list_body() -> List[int]:
        """Docstring plus annotated empty list return."""
        return []

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for function, expected in (
        (empty_body, False),
        (ellipsis_body, False),
        (docstring_body, False),
        (docstring_with_pass_body, False),
        (empty_list_body, False),
        (empty_dict_body, False),
        (bare_return_body, True),
        (none_return_body, True),
        (unannotated_list_body, True),
        (docstring_with_annotated_list_body, True),
    ):
        slot = Slot(function, None, None, None, True, 'pristan', False)

        assert bool(slot) is expected


def test_bool_with_fixture_container_annotations_is_false_for_empty_returns(monkeypatch, list_type, dict_type):
    """Fixture-provided list and dict annotations use the existing empty-return rule."""
    def list_slot() -> list_type:
        return []

    def dict_slot() -> dict_type:
        return {}

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for function in (list_slot, dict_slot):
        assert not bool(Slot(function, None, None, None, True, 'pristan', False))


def test_bool_keeps_loaded_after_successful_load_and_inspection_error(monkeypatch):
    """A fallback inspection failure after successful loading does not reset loaded."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    calls = []
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        calls.append(group)
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)
    slot.caller.code_representation = BrokenCodeRepresentation()

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        bool(slot)

    assert slot.loaded

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        bool(slot)

    assert calls == ['pristan']


def test_len_and_contains_do_not_load_entrypoints(monkeypatch):
    """Length and valid membership checks remain plugin-only no-load operations."""
    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        assert group == 'pristan'
        raise RuntimeError('provider')

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert len(slot) == 0
    assert 'plugin' not in slot


def test_invalid_contains_does_not_load_entrypoints(monkeypatch):
    """Invalid membership checks raise local collection errors without loading."""
    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        assert group == 'pristan'
        raise RuntimeError('provider')

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(ValueError, match=match("The plugin name string must look like either a valid Python identifier or an identifier plus one or more digits separated by a hyphen, for example, 'name-22'. 'bad--' is not a valid name for a plugin.")):
        'bad--' in slot  # noqa: B015

    with pytest.raises(TypeError, match=match('Checking for inclusion is only possible for strings of a valid format or for plugin objects.')):
        1 in slot  # noqa: B015


def test_iter_creation_does_not_load_until_consumed(monkeypatch):
    """Slot iteration is lazy until the generator is consumed."""
    def empty_body():
        pass

    provider_error = RuntimeError('provider')
    calls = []
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        calls.append(group)
        raise provider_error

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    iterator = iter(slot)

    assert calls == []

    with pytest.raises(EntrypointLoadingError) as exception_info:
        next(iterator)

    assert exception_info.value.__cause__ is provider_error
    assert calls == ['pristan']


def test_truthy_slot_with_non_empty_default_can_have_zero_plugins(monkeypatch):
    """Truthiness is not equivalent to plugin collection size."""
    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = Slot(none_return_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot)
    assert len(slot) == 0


def test_getitem_loads_before_returning_selection(monkeypatch):
    """Selection lookup resolves entry points before returning CallerWithPlugins."""
    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert len(slot['missing']) == 0
    assert slot.loaded


def test_getitem_and_delitem_load_errors_dominate_key_validation(monkeypatch):
    """Lazy load failures happen before invalid-key validation."""
    def empty_body():
        pass

    def getitem_invalid(slot):
        slot['bad--']

    def delitem_invalid(slot):
        del slot['bad--']

    def make_failing_provider(provider_error):
        def get_entries(group=None):
            assert group == 'pristan'
            raise provider_error

        return get_entries

    for operation in (getitem_invalid, delitem_invalid):
        provider_error = RuntimeError('provider')
        slot = Slot(empty_body, None, None, None, True, 'pristan', False)
        monkeypatch.setattr(slot_module, 'entry_points', make_failing_provider(provider_error))

        with pytest.raises(EntrypointLoadingError) as exception_info:
            operation(slot)

        assert exception_info.value.__cause__ is provider_error


def test_saved_selection_is_snapshot_and_does_not_load_again(monkeypatch):
    """Selections keep their plugin list and do not observe later parent additions."""
    def empty_body():
        pass

    calls = []
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        calls.append(group)
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    selected = slot['plugin']
    empty_selection = slot['missing']

    del slot['plugin']

    @slot.plugin('missing')
    def later_plugin():
        return None

    assert bool(selected)
    assert len(selected) == 1
    assert not bool(empty_selection)
    assert len(empty_selection) == 0
    assert bool(slot)
    assert calls == ['pristan']


def test_selection_bool_branches(monkeypatch):
    """CallerWithPlugins bool covers plugin, fallback-true, and fallback-false branches."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)
    slot_with_plugin = Slot(empty_body, None, None, None, True, 'pristan', False)

    @slot_with_plugin.plugin
    def plugin():
        return None

    slot_with_plugin.caller.code_representation = BrokenCodeRepresentation()

    assert bool(slot_with_plugin['plugin'])

    assert bool(Slot(none_return_body, None, None, None, True, 'pristan', False)['missing'])
    assert not bool(Slot(empty_body, None, None, None, True, 'pristan', False)['missing'])


def test_selection_bool_does_not_execute_default_or_plugins(monkeypatch):
    """Selection truthiness does not call the slot body or selected plugins."""
    def default():
        raise AssertionError('default body was executed')

    slot = Slot(default, None, None, None, True, 'pristan', False)

    @slot.plugin('plugin')
    def plugin():
        raise AssertionError('plugin was executed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert bool(slot['missing'])
    assert bool(slot['plugin'])


def test_selection_bool_for_absent_duplicate_depends_on_default_body(monkeypatch):
    """An absent numbered duplicate is empty but still uses fallback truthiness."""
    def empty_body():
        pass

    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for body, expected_bool in (
        (empty_body, False),
        (none_return_body, True),
    ):
        current_slot = Slot(body, None, None, None, True, 'pristan', False)

        @current_slot.plugin('name')
        def plugin():
            return None

        selection = current_slot['name-3']
        assert bool(selection) is expected_bool
        assert len(selection) == 0


def test_del_last_plugin_updates_parent_bool(monkeypatch):
    """After deleting the last plugin, parent bool falls back to default body state."""
    def empty_body():
        pass

    def none_return_body():
        return None

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for body, expected_bool in (
        (empty_body, False),
        (none_return_body, True),
    ):
        current_slot = Slot(body, None, None, None, True, 'pristan', False)

        @current_slot.plugin('plugin')
        def plugin():
            return None

        del current_slot['plugin']

        assert bool(current_slot) is expected_bool


def test_pop_existing_returns_detached_truthy_selection(monkeypatch):
    """Popping an existing plugin returns a detached truthy selection."""
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    removed = slot.pop('plugin')

    assert bool(removed)
    assert len(removed) == 1
    assert not bool(slot)


def test_pop_existing_with_default_returns_selection_not_default(monkeypatch):
    """A found key makes pop return a selection even when a default is supplied."""
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    default = object()
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('plugin')
    def plugin():
        return None

    removed = slot.pop('plugin', default)

    assert removed is not default
    assert bool(removed)


@pytest.mark.parametrize('key', ['missing', 'bad--'])
def test_pop_default_returns_default_after_successful_load(monkeypatch, key):
    """A missing or invalid plugin key returns the default after loading succeeds."""
    def empty_body():
        pass

    default = object()
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    assert slot.pop(key, default) is default
    assert slot.loaded


def test_duplicate_plugin_selection_keys(monkeypatch):
    """Base-name lookup returns duplicate bucket; numbered keys select exact matches."""
    def empty_body():
        pass

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    @slot.plugin('name')
    def plugin_1():
        return None

    @slot.plugin('name')
    def plugin_2():
        return None

    for key, expected_names in (
        ('name', ['name', 'name-2']),
        ('name-1', ['name']),
        ('name-2', ['name-2']),
        ('name-3', []),
    ):
        assert [plugin.name for plugin in slot[key]] == expected_names


@pytest.mark.parametrize('operation_name', ['bool', 'call', 'iter', 'keys', 'getitem', 'delitem', 'pop', 'pop-default'])
@pytest.mark.parametrize('provider_name', ['provider-call', 'provider-iteration', 'point-load-runtime', 'point-load-key-error'])
def test_entrypoint_loading_errors_are_wrapped_for_lazy_operation_matrix(monkeypatch, operation_name, provider_name):
    """Every lazy public operation wraps ordinary external loading failures.

    Entry point resolution is shared by bool, calls, consumed iteration, key
    reads, item access, deletion, and pop. Each operation must expose the same
    wrapper while preserving provider, iteration, point.load, and import-style
    KeyError failures as the original cause.
    """
    class FakeEntryPoint:
        def __init__(self, exception):
            self.exception = exception

        def load(self):
            raise self.exception

    class BrokenIterable:
        def __init__(self, exception):
            self.exception = exception

        def __iter__(self):
            raise self.exception

    def empty_body():
        pass

    def delitem_operation(slot):
        del slot['missing']

    def provider_call_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            raise cause

        return get_entries

    def provider_iteration_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return BrokenIterable(cause)

        return get_entries

    def point_load_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return [FakeEntryPoint(cause)]

        return get_entries

    operations = {
        'bool': bool,
        'call': lambda slot: slot(),
        'iter': list,
        'keys': lambda slot: slot.keys(),
        'getitem': lambda slot: slot['missing'],
        'delitem': delitem_operation,
        'pop': lambda slot: slot.pop('missing'),
        'pop-default': lambda slot: slot.pop('missing', None),
    }
    provider_cases = {
        'provider-call': (provider_call_failure, KeyError('provider')),
        'provider-iteration': (provider_iteration_failure, KeyError('iteration')),
        'point-load-runtime': (point_load_failure, RuntimeError('load')),
        'point-load-key-error': (point_load_failure, KeyError('broken import')),
    }
    provider_factory, cause = provider_cases[provider_name]
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', provider_factory(cause))

    with pytest.raises(EntrypointLoadingError, match=match('An error occurred while loading entry points.')) as exception_info:
        operations[operation_name](slot)

    assert exception_info.value.__cause__ is cause
    assert not slot.loaded


@pytest.mark.parametrize('provider_name', ['provider-call', 'provider-iteration', 'point-load'])
@pytest.mark.parametrize('cause_name', ['primadonna', 'inner-wrapper', 'custom'])
def test_pristan_errors_from_entrypoint_loading_are_not_wrapped_for_source_matrix(monkeypatch, provider_name, cause_name):
    """Pristan exceptions pass through every entry point loading stage.

    The lazy loader catches broad external failures to provide a stable wrapper,
    but Pristan's own exceptions already carry user-facing meaning. Provider,
    provider iteration, and point.load failures therefore re-raise the original
    Pristan exception object instead of converting it to EntrypointLoadingError.
    """
    class FakeEntryPoint:
        def __init__(self, exception):
            self.exception = exception

        def load(self):
            raise self.exception

    class BrokenIterable:
        def __init__(self, exception):
            self.exception = exception

        def __iter__(self):
            raise self.exception

    class CustomPristanError(PristanException):
        pass

    def empty_body():
        pass

    def provider_call_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            raise cause

        return get_entries

    def provider_iteration_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return BrokenIterable(cause)

        return get_entries

    def point_load_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return [FakeEntryPoint(cause)]

        return get_entries

    provider_factories = {
        'provider-call': provider_call_failure,
        'provider-iteration': provider_iteration_failure,
        'point-load': point_load_failure,
    }
    causes = {
        'primadonna': PrimadonnaPluginError('duplicate plugin'),
        'inner-wrapper': EntrypointLoadingError('inner wrapper'),
        'custom': CustomPristanError('future internal error'),
    }
    cause = causes[cause_name]
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', provider_factories[provider_name](cause))

    with pytest.raises(PristanException) as exception_info:
        bool(slot)

    assert exception_info.value is cause
    assert not slot.loaded


@pytest.mark.parametrize('operation_name', ['bool', 'call', 'iter', 'keys', 'getitem', 'delitem', 'pop', 'pop-default'])
def test_pristan_errors_from_entrypoint_loading_are_not_wrapped_for_lazy_operation_matrix(monkeypatch, operation_name):
    """Lazy public operations pass through Pristan exceptions consistently.

    A Pristan exception raised while discovering entry points is not an external
    import or plugin-module failure. This matrix keeps all lazy public access
    paths aligned, including pop with a user default.
    """
    def empty_body():
        pass

    def delitem_operation(slot):
        del slot['missing']

    operations = {
        'bool': bool,
        'call': lambda slot: slot(),
        'iter': list,
        'keys': lambda slot: slot.keys(),
        'getitem': lambda slot: slot['missing'],
        'delitem': delitem_operation,
        'pop': lambda slot: slot.pop('missing'),
        'pop-default': lambda slot: slot.pop('missing', None),
    }
    cause = PristanException('provider')
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def get_entries(group=None):
        assert group == 'pristan'
        raise cause

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(PristanException) as exception_info:
        operations[operation_name](slot)

    assert exception_info.value is cause
    assert not slot.loaded


def test_registration_error_during_entrypoint_loading_is_not_wrapped(monkeypatch):
    """Registration failures raised inside point.load remain direct Pristan errors."""
    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', True)
    captured = []

    def register_duplicates():
        @slot.plugin('name')
        def first_plugin():
            return None

        try:
            @slot.plugin('name')
            def second_plugin():
                return None
        except PrimadonnaPluginError as exception:
            captured.append(exception)
            raise

    class FakeEntryPoint:
        def load(self):
            register_duplicates()

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint()]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(PrimadonnaPluginError) as exception_info:
        bool(slot)

    assert exception_info.value is captured[0]
    assert not slot.loaded
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name']


def test_load_failure_then_retry_success_keeps_partial_plugins(monkeypatch):
    """A failed load keeps partial plugins and retries from the provider start.

    Entry point loading does not roll back plugins that registered before a
    later entry point failed. A retry starts discovery again, so the previously
    registered plugin remains and can be duplicated before the retry succeeds.
    """
    class FakeEntryPoint:
        def __init__(self, loader):
            self.loader = loader

        def load(self):
            self.loader()

    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    attempts = []

    def register_name():
        @slot.plugin('name')
        def plugin():
            return None

    def register_other():
        @slot.plugin('other')
        def plugin():
            return None

    def fail_first_load():
        raise RuntimeError('first failure')

    def get_entries(group=None):
        assert group == 'pristan'
        attempts.append('attempt')
        if len(attempts) == 1:
            return [FakeEntryPoint(register_name), FakeEntryPoint(fail_first_load)]
        return [FakeEntryPoint(register_name), FakeEntryPoint(register_other)]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(EntrypointLoadingError):
        bool(slot)

    assert [plugin.name for plugin in slot.plugins.plugins] == ['name']
    assert not slot.loaded

    assert bool(slot)
    assert [plugin.name for plugin in slot.plugins.plugins] == ['name', 'name-2', 'other']
    assert slot.loaded


def test_stable_load_failure_can_accumulate_partial_duplicates(monkeypatch):
    """Stable failures retry from the start and can duplicate partial plugins.

    The loader intentionally keeps partial state after failed discovery. When
    the same provider fails repeatedly after registering one plugin, each retry
    can add another duplicate before the same load error is raised.
    """
    class FakeEntryPoint:
        def __init__(self, loader):
            self.loader = loader

        def load(self):
            self.loader()

    def empty_body():
        pass

    slot = Slot(empty_body, None, None, None, True, 'pristan', False)

    def register_name():
        @slot.plugin('name')
        def plugin():
            return None

    def fail_stable_load():
        raise RuntimeError('stable failure')

    def get_entries(group=None):
        assert group == 'pristan'
        return [FakeEntryPoint(register_name), FakeEntryPoint(fail_stable_load)]

    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    for _ in range(2):
        with pytest.raises(EntrypointLoadingError):
            bool(slot)

    assert [plugin.name for plugin in slot.plugins.plugins] == ['name', 'name-2']
    assert not slot.loaded


@pytest.mark.parametrize('provider_name', ['provider-call', 'provider-iteration', 'point-load'])
def test_base_exception_from_entrypoint_loading_passes_through(monkeypatch, provider_name):
    """BaseException subclasses pass through every entry point loading stage."""
    class CustomBaseException(BaseException):
        pass

    class FakeEntryPoint:
        def __init__(self, exception):
            self.exception = exception

        def load(self):
            raise self.exception

    class BrokenIterable:
        def __init__(self, exception):
            self.exception = exception

        def __iter__(self):
            raise self.exception

    def empty_body():
        pass

    def provider_call_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            raise cause

        return get_entries

    def provider_iteration_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return BrokenIterable(cause)

        return get_entries

    def point_load_failure(cause):
        def get_entries(group=None):
            assert group == 'pristan'
            return [FakeEntryPoint(cause)]

        return get_entries

    provider_cases = {
        'provider-call': provider_call_failure,
        'provider-iteration': provider_iteration_failure,
        'point-load': point_load_failure,
    }
    cause = CustomBaseException(provider_name)
    slot = Slot(empty_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', provider_cases[provider_name](cause))

    with pytest.raises(CustomBaseException) as exception_info:
        bool(slot)

    assert exception_info.value is cause
    assert not slot.loaded


def test_direct_local_errors_are_not_wrapped(monkeypatch):
    """Errors outside entry point loading keep their original types."""
    def default_body():
        raise ValueError('default failed')

    def get_entries(group=None):
        assert group == 'pristan'
        return []

    default_slot = Slot(default_body, None, None, None, True, 'pristan', False)
    monkeypatch.setattr(slot_module, 'entry_points', get_entries)

    with pytest.raises(ValueError, match=match('default failed')):
        default_slot()

    plugin_slot = Slot(default_body, None, None, None, True, 'pristan', False)

    @plugin_slot.plugin
    def plugin():
        raise RuntimeError('plugin failed')

    with pytest.raises(RuntimeError, match=match('plugin failed')):
        plugin_slot()
