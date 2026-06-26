import pristan
import pristan.errors as errors_module


def test_all_pristan_errors_inherit_from_pristan_exception():
    """Every Pristan error is rooted in PristanException.

    The shared base keeps Pristan errors out of entry point wrappers. Dynamic
    discovery covers future errors, and `OneResolutionError` is pinned as a
    direct subclass.
    """
    assert issubclass(errors_module.PristanException, Exception)

    for error_class in vars(errors_module).values():
        if not isinstance(error_class, type):
            continue

        assert issubclass(error_class, errors_module.PristanException)

    assert errors_module.OneResolutionError.__bases__ == (errors_module.PristanException,)


def test_pristan_errors_are_not_exported_from_root_package():
    """Errors from pristan.errors are not part of the root package surface."""
    for error_name, error_class in vars(errors_module).items():
        if not isinstance(error_class, type):
            continue

        assert not hasattr(pristan, error_name)


def test_explicit_plugin_names_error_inherits_from_name_error():
    """Strict plugin-name failures can be caught as library or name errors."""
    assert issubclass(errors_module.ExplicitNameRequiredError, NameError)
