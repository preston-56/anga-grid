"""Gridded climate indicators for East African agriculture.

Top-level package. The bulk of the public API lives in themed
sub-packages:

  providers.{chirps,agera5,tamsat,nex_gddp}  - dataset readers
  indicators.{spi,onset,dry_spell,gdd,
              evapotranspiration,wrsi,trend,
              temperature_extremes}          - per-indicator modules
  severity.{bands,phases,quintile,summary}   - classification schemes
  rollup.{bbox,polygon}                      - spatial aggregation
  cropping.{calendar,windows}                - phenological windows
  correction.{linear,delta,monthly}          - bias correction
  storage.{io,manifest_io,format}            - read/write helpers
  provenance.{manifest,steps,ops}            - audit-trail manifest
  season.{types,catalog}                     - first-class Season
  types.{geometry,time,regions}              - foundational types

See the README and doc/cli.md for an operational walkthrough.
"""

from anga_grid._version import VERSION

__version__ = VERSION
__all__ = ["__version__"]
