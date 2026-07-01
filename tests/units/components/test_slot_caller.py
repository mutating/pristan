from typing import Dict, List

import pytest
from full_match import match

from pristan.components.plugin import Plugin
from pristan.components.slot import Slot
from pristan.components.slot_caller import CallerWithPlugins


def test_has_non_empty_default_body_reflects_code_representer_is_empty():
    """The property exposes the inverse of the existing empty-body detector."""
    def empty_body():
        pass

    def non_empty_body():
        return None

    def empty_list_body() -> List[int]:
        return []

    def empty_dict_body() -> Dict[str, int]:
        return {}

    def docstring_with_annotated_list_body() -> List[int]:
        """Docstring plus annotated empty list return."""
        return []

    for function, expected in (
        (empty_body, False),
        (empty_list_body, False),
        (empty_dict_body, False),
        (non_empty_body, True),
        (docstring_with_annotated_list_body, True),
    ):
        slot = Slot(function, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

        assert slot.caller.has_non_empty_default_body is expected


def test_has_non_empty_default_body_propagates_inspection_errors():
    """Source inspection failures are not hidden by the convenience property."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    slot.code_representation = BrokenCodeRepresentation()

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        slot.caller.has_non_empty_default_body  # noqa: B018


def test_bool_truth_table_for_plugins_and_default_body():
    """CallerWithPlugins bool is true for plugins or a non-empty fallback body."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    def non_empty_body():
        return None

    empty_slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    non_empty_slot = Slot(non_empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    assert not CallerWithPlugins(empty_slot.caller, [])
    assert CallerWithPlugins(non_empty_slot.caller, [])
    empty_slot.code_representation = BrokenCodeRepresentation()
    assert CallerWithPlugins(empty_slot.caller, [Plugin('plugin', empty_body, int, True, False)])


def test_bool_does_not_execute_plugins_or_default():
    """Truthiness does not call selected plugins or the default slot body."""
    def default_body():
        raise AssertionError('default body was executed')

    def plugin_function():
        raise AssertionError('plugin was executed')

    slot = Slot(default_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    assert CallerWithPlugins(slot.caller, [])
    assert CallerWithPlugins(slot.caller, [Plugin('plugin', plugin_function, int, True, False)])


def test_empty_list_and_dict_defaults_still_call_to_empty_containers():
    """SlotCaller.__call__ still returns empty list and dict defaults without plugins."""
    def empty_list_body() -> List[int]:
        return []

    def empty_dict_body() -> Dict[str, int]:
        return {}

    for function, expected_result in (
        (empty_list_body, []),
        (empty_dict_body, {}),
    ):
        slot = Slot(function, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

        assert slot.caller([]) == expected_result


def test_repr():
    """SlotCaller repr exposes the referenced Slot with its explicit non-default options."""
    slot = Slot(lambda x: x, signature=None, slot_name='kek', max=None, type_check=False, entrypoint_group='pristan', unique=False)

    assert repr(slot.caller) == 'SlotCaller(slot=Slot(lambda x: x, slot_name=\'kek\', type_check=False))'


def test_call_snapshots_current_slot_state_once_per_call():
    """SlotCaller snapshots slot state before each call's inspection.

    The test mutates `slot.code_representation` and `slot.slot_function` while
    reading `is_empty` to prove dispatch uses the snapshot. A fallback branch
    also mutates `slot.slot_name` and `slot.type_check` before dispatch.
    """
    def wrong_default_body():
        return ['wrong']

    def broken_default_body() -> List[int]:
        raise AssertionError('slot function was read again')

    def plugin_function():
        return 1

    class BrokenCodeRepresentation:
        def __getattr__(self, _name):
            raise RuntimeError('slot metadata was read again')

    class MutatingCodeRepresentation:
        returns_list = True
        returns_dict = False
        returning_type = int

        def __init__(self, slot):
            self.slot = slot

        @property
        def is_empty(self):
            self.slot.code_representation = BrokenCodeRepresentation()
            self.slot.slot_function = broken_default_body
            self.slot.slot_name = 'mutated_slot'
            self.slot.type_check = False
            return False

    slot = Slot(broken_default_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)

    slot.code_representation = MutatingCodeRepresentation(slot)

    assert slot.caller([Plugin('plugin', plugin_function, int, True, False)]) == [1]
    assert isinstance(slot.code_representation, BrokenCodeRepresentation)

    slot = Slot(broken_default_body, signature=None, slot_name='stale_slot', max=None, type_check=False, entrypoint_group='pristan', unique=False)
    slot.slot_function = wrong_default_body
    slot.slot_name = 'original_slot'
    slot.type_check = True
    slot.code_representation = MutatingCodeRepresentation(slot)
    expected_type = List[slot.code_representation.returning_type]
    expected_type_name = getattr(expected_type, '__name__', str(expected_type))

    with pytest.raises(TypeError, match=match(f'The type list of the plugin\'s "original_slot" return value [\'wrong\'] does not match the expected type {expected_type_name}.')):
        slot.caller([])


def test_call_with_plugins_keeps_current_inspection_before_dispatch_behavior():
    """SlotCaller.__call__ keeps its existing source-inspection order.

    With plugins present, call dispatch still reads `is_empty` before running
    plugin functions. Inspection errors therefore dominate plugin calls, unlike
    bool, which short-circuits source inspection when plugins are present.
    """
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    slot = Slot(empty_body, signature=None, slot_name=None, max=None, type_check=True, entrypoint_group='pristan', unique=False)
    slot.code_representation = BrokenCodeRepresentation()

    def plugin_function():
        raise AssertionError('plugin was executed')

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        slot.caller([Plugin('plugin', plugin_function, int, True, False)])
