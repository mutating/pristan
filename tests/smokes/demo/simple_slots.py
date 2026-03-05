from typing import Dict

from pristan import slot


@slot
def simple_slot_1() -> Dict[str, int]:
    return {}


@slot(entrypoint_group='another_name')
def simple_slot_2() -> Dict[str, int]:
    return {}
