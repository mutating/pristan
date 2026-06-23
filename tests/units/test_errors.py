import pristan.errors as errors_module


def test_all_pristan_errors_inherit_from_pristan_exception():
    """Every Pristan error is rooted in PristanException.

    Entry point loading intentionally catches broad third-party exceptions, so
    Pristan's own exceptions need a shared base class that protects them from
    being converted into integration wrappers. The test discovers exceptions
    from `pristan.errors` dynamically: if new Pristan exceptions are added
    later, they are covered by the same contract without updating this test.
    """
    assert issubclass(errors_module.PristanException, Exception)

    for error_name, error_class in vars(errors_module).items():
        if error_name.startswith('__'):
            continue

        assert issubclass(error_class, errors_module.PristanException)


def test_explicit_plugin_names_error_inherits_from_name_error():
    """Strict plugin-name failures can be caught as library or name errors."""
    assert issubclass(errors_module.ExplicitNameRequiredError, NameError)
