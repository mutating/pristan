from typing import Dict

from pristan import slot


@slot
def simple_slot_1() -> Dict[str, int]:
    """For test_run_simple_slot only; do not reuse."""
    return {}


@slot(entrypoint_group='another_name')
def simple_slot_2() -> Dict[str, int]:
    """For test_run_simple_slot_with_another_name only; do not reuse."""
    return {}


@slot
def simple_slot_3() -> Dict[str, int]:
    """For test_plugins_are_loaded_when_called only; do not reuse."""
    return {}


@slot
def simple_slot_4() -> Dict[str, int]:
    """For test_plugins_are_loaded_when_keys_are_read only; do not reuse."""
    return {}


@slot
def simple_slot_5() -> Dict[str, int]:
    """For test_getitem_loads_plugins_from_real_entrypoint only; do not reuse."""
    return {}


@slot(unique=True)
def simple_slot_6() -> Dict[str, int]:
    """For test_unique_slot_rejects_duplicate_plugins_loaded_from_entrypoints only; do not reuse."""
    return {}


@slot
def simple_bool_slot() -> Dict[str, int]:
    """For test_bool_loads_plugins_from_real_entrypoint_once only; do not reuse."""
    return {}


@slot
def simple_one_slot() -> Dict[str, int]:
    """For test_slot_one_loads_plugin_from_real_entrypoint_and_calls_result only; do not reuse."""
    return {}


@slot(entrypoint_group='another_name')
def simple_custom_one_slot() -> Dict[str, int]:
    """For test_slot_one_loads_plugin_from_custom_entrypoint_group only; do not reuse."""
    return {}


@slot(explicit_plugin_names=True)
def simple_explicit_plugin_names_slot() -> Dict[str, int]:
    """For test_explicit_plugin_names_rejects_inferred_name_loaded_from_entrypoint only; do not reuse."""
    return {}
