class PristanException(Exception):  # noqa: N818
    ...


class TooManyPluginsError(PristanException):
    ...


class PrimadonnaPluginError(PristanException):
    ...


class ExplicitNameRequiredError(PristanException, NameError):
    ...


class EntrypointLoadingError(PristanException):
    ...


class StrangeTypeAnnotationError(PristanException):
    ...


class CannotGetVersionsError(PristanException):
    ...


class NumberOfCallsError(PristanException):
    ...


class OneResolutionError(PristanException):
    ...
