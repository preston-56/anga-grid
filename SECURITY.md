# Security policy

anga-grid is a small library used in operational drought-monitoring
contexts. It does not handle credentials, accept network input from
untrusted sources, or run user-supplied code. The realistic security
surface is small.

## Reporting a vulnerability

If you find a security issue, please email
**prestonosoro56@gmail.com** rather than opening a public issue.
Include:

- The affected version (or a commit SHA from `main`)
- A reproducer if possible
- The impact you're concerned about

We aim to acknowledge within 7 days and ship a fix within 30 days
for anything that affects integrity of operational outputs.

## Out of scope

- Bugs in the dataset providers (CHIRPS, AgERA5, TAMSAT, NEX-GDDP) or
  upstream Python libraries (xarray, xclim) — please report those to
  their respective projects.
- Numerical disagreements with another implementation that don't
  introduce data-integrity or remote-code-execution issues; please
  open a regular GitHub issue for those.
