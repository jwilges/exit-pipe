# exit-pipe
*exit-pipe: a command-line utility to pipe the exit code from a subprocess
through one or more modifiers.*

[![build](https://github.com/jwilges/exit-pipe/workflows/CI/badge.svg)](https://github.com/jwilges/exit-pipe/actions?query=workflow:CI) [![codecov](https://codecov.io/gh/jwilges/exit-pipe/branch/master/graph/badge.svg)](https://codecov.io/gh/jwilges/exit-pipe)


## Background
This utility executes a specified subprocess, captures its exit code, and exits
with the result of piping the exit code through a conditional exit code
modifier.

The motivation for this slightly obtuse solution was to work around limitations
imposed by build utilities which execute configurable subprocesses without
exposing full shell access (e.g. `tox`) while also maintaining reasonable
portability across multiple operating system environments (thus eliminating the
option of executing an explicit shell within `tox`).

As of this release, one style of exit code modifier pipeline exists: `bitfield`.

The `bitfield` exit code pipeline (activated via the `--bitfield` argument)
evaluates the exit code against one or more bitfield masks and either replaces
the exit code with the mapping specified by the first matching bitfield mask or
passes through the unmodified exit code if no bitfield masks match.

## Supported Platforms
This utility has been tested on macOS Catalina 10.15.

## Usage
### Development Environment
Initialize a development environment by executing `tox`; the `exit-pipe` utility
will be installed in the `.tox/py38` Python virtual environment binary path.

### Examples
#### Remap non-fatal, non-error pylint exit codes to 0
As of `pylint` 2.4.3, the utility's exit code is a bitfield that may
be decoded as:

| Bit  | Meaning                   |
|-----:|---------------------------|
|  `0` | No error                  |
|  `1` | Fatal message issued      |
|  `2` | Error message issued      |
|  `4` | Warning message issued    |
|  `8` | Refactor message issued   |
| `16` | Convention message issued |
| `32` | Usage error               |

To remap the exit code for `pylint src` such that it exits with:
- `1` for fatal (`1`) and error (`2`) exit codes, and
- `0` for warning (`4`), refactor (`8`), convention (`16`), and usage (`32`) exit codes,

you may pass `pylint` through `exit-pipe` as follows:

    exit-pipe --bitfield "3:1;60:0" -- pylint src

The equivalent bitfield masks may be specified individually as follows:

    exit-pipe --bitfield "1,2:1;4,8,16,32:0" -- pylint src

As niche as this example may be, it serves as a generic workaround to cases
where you may wish to log all `pylint` messages while only interpreting a few
classes of messages as build errors. Disabling or ignoring classes of messages
would result in them not being logged.
