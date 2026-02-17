"""Exception hierarchy for anga-grid.

Every error the library raises descends from AngaGridError, so a
single except clause covers the whole library. Inheritance maps to
the operational concern:

  AngaGridError
    DatasetError       - anything wrong with input data
      ProviderError    - dataset reader couldn't satisfy the request
    SeasonError        - Season construction or window-mismatch issue
    ProvenanceError    - manifest serialisation/deserialisation
    IndicatorError     - indicator preconditions not met
"""


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


__all__ = [
    "AngaGridError",
    "DatasetError",
    "IndicatorError",
    "ProvenanceError",
    "ProviderError",
    "SeasonError",
]
