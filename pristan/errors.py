class PristanException(Exception):  # noqa: N818
    ...


class TooManyPluginsError(PristanException):
    ...


class PrimadonnaPluginError(PristanException):
    ...


class EntrypointLoadingError(PristanException):
    ...


class StrangeTypeAnnotationError(PristanException):
    ...


class CannotGetVersionsError(PristanException):
    ...


class NumberOfCallsError(PristanException):
    ...
