from tests.smokes.demo.simple_slots import simple_slot_1, simple_slot_2, simple_slot_3, simple_slot_4, simple_slot_5


def test_run_simple_slot():
    assert not simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}
    assert simple_slot_1.loaded
    assert simple_slot_1() == {'name': 1}


def test_run_simple_slot_with_another_name():
    assert not simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}
    assert simple_slot_2.loaded
    assert simple_slot_2() == {'name2': 2}


def test_plugins_are_loaded_when_called():
    assert not simple_slot_3.loaded

    assert simple_slot_3() == {'name': 1}

    assert simple_slot_3.loaded


def test_plugins_are_loaded_when_keys_readed():
    assert not simple_slot_4.loaded

    assert simple_slot_4.keys() == ('name',)

    assert simple_slot_4.loaded


def test_plugins_are_loaded_when_getitem():
    assert not simple_slot_5.loaded

    assert len(simple_slot_5['name']) == 1

    assert simple_slot_5.loaded
