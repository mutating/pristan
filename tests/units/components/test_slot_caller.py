from typing import Dict, List

import pytest
from full_match import match

from pristan.components.plugin import Plugin
from pristan.components.slot_caller import CallerWithPlugins, SlotCaller
from pristan.components.slot_code_representer import SlotCodeRepresenter


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
        assert SlotCaller(SlotCodeRepresenter(function), function.__name__, function, True).has_non_empty_default_body is expected


def test_has_non_empty_default_body_propagates_inspection_errors():
    """Source inspection failures are not hidden by the convenience property."""
    class BrokenCodeRepresentation:
        @property
        def is_empty(self):
            raise RuntimeError('inspection failed')

    def empty_body():
        pass

    caller = SlotCaller(BrokenCodeRepresentation(), empty_body.__name__, empty_body, True)

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        caller.has_non_empty_default_body  # noqa: B018


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

    empty_caller = SlotCaller(SlotCodeRepresenter(empty_body), empty_body.__name__, empty_body, True)
    non_empty_caller = SlotCaller(SlotCodeRepresenter(non_empty_body), non_empty_body.__name__, non_empty_body, True)
    plugin_caller = SlotCaller(BrokenCodeRepresentation(), empty_body.__name__, empty_body, True)

    assert not CallerWithPlugins(empty_caller, [])
    assert CallerWithPlugins(non_empty_caller, [])
    assert CallerWithPlugins(plugin_caller, [Plugin('plugin', empty_body, int, True, False)])


def test_bool_does_not_execute_plugins_or_default():
    """Truthiness does not call selected plugins or the default slot body."""
    def default_body():
        raise AssertionError('default body was executed')

    def plugin_function():
        raise AssertionError('plugin was executed')

    caller = SlotCaller(SlotCodeRepresenter(default_body), default_body.__name__, default_body, True)

    assert CallerWithPlugins(caller, [])
    assert CallerWithPlugins(caller, [Plugin('plugin', plugin_function, int, True, False)])


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
        assert SlotCaller(SlotCodeRepresenter(function), function.__name__, function, True)([]) == expected_result


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

    caller = SlotCaller(BrokenCodeRepresentation(), empty_body.__name__, empty_body, True)

    def plugin_function():
        raise AssertionError('plugin was executed')

    with pytest.raises(RuntimeError, match=match('inspection failed')):
        caller([Plugin('plugin', plugin_function, int, True, False)])
