class GspreadPandasException(Exception):
    pass


class ConfigException(GspreadPandasException):
    pass


class NoWorksheetException(GspreadPandasException):
    pass


class MissMatchException(GspreadPandasException):
    pass
