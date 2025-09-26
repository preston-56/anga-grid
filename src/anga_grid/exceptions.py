class AngaGridError(Exception):
    pass


class DatasetError(AngaGridError):
    pass


class ProviderError(DatasetError):
    pass


class SeasonError(AngaGridError):
    pass


class ProvenanceError(AngaGridError):
    pass


class IndicatorError(AngaGridError):
    pass
