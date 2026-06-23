"""Single source of truth for the package version.

Bumped manually as the v0.x series develops. v1.0 will switch this
to importlib.metadata.version("anga-grid") once we commit to the
stability contract; until then the dev0 marker is intentional and
warns consumers the API may shift.
"""

VERSION = "0.5.0"
