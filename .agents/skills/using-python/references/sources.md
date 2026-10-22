# Python source basis

Primary Python documentation and established maintainer style guides behind the references. Read
this to audit or update a claim. Where sources permit several conventions, the skill follows the
repository rather than presenting one organization's choice as Python law.

## Language-wide style and contracts

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/): imports, module-level
  order, comments, naming, inheritance APIs, public/internal interfaces, annotations, and the rule
  that project consistency can outweigh a general recommendation.
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/): docstring placement,
  one-line and multiline form, imperative summaries, and caller-visible function, class, module,
  package, and script documentation.
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/): annotations as optional type metadata
  and their relationship to runtime behavior.
- [PEP 604 — Union Types](https://peps.python.org/pep-0604/): the Python 3.10 version floor for
  `X | Y` union syntax.
- [PEP 20 — The Zen of Python](https://peps.python.org/pep-0020/): readability, explicit behavior,
  simplicity, flat structure, and namespaces as guiding—not mechanically enforceable—principles.

## Modules, packages, and entry points

- [Python tutorial — Modules and Packages](https://docs.python.org/3/tutorial/modules.html): import
  execution, module namespaces, package structure, `__init__.py`, `__all__`, wildcard imports,
  absolute and relative imports, and directly executed modules.
- [Python `__main__` documentation](https://docs.python.org/3/library/__main__.html): minimal entry
  blocks, importable `main()` behavior, exit values, and package `__main__.py`.
- [Python Packaging User Guide — `src` layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/): the isolation, installation, and import-path tradeoffs of each project layout.

## Established project conventions

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html): explicit dos and
  don'ts for imports, mutable global state, nesting, defaults, properties, docstrings, comments,
  TODOs, naming, import-safe entry points, focused functions, concurrency, and annotations. This is
  a published Google convention, not a universal Python mandate.
- [Python Developer's Guide — Documentation style](https://devguide.python.org/documentation/style-guide/): precise reference prose, simple language, affirmative guidance, and choosing tutorial,
  how-to, reference, or explanation according to the reader's need.

## Documented traps and the tools that encode them

A lint rule exists because enough people hit the trap. These catalogs are evidence of which mistakes
are common, not merely style opinions.

- [Python Programming FAQ](https://docs.python.org/3/faq/programming.html): mutable default
  arguments, late-binding closures, assignment never copying, `is` versus `==`, local-versus-global
  scope, augmented assignment on tuple members, quadratic string concatenation, and circular imports.
- [flake8-bugbear](https://github.com/PyCQA/flake8-bugbear): the `B0xx` catalog of real Python traps —
  mutable and computed defaults, `finally` swallowing exceptions, `lru_cache` on methods, late
  binding in loops, ABCs missing `@abstractmethod`, `assertRaises(Exception)`, multi-character
  `.strip()`, and `groupby` reuse.
- [Ruff rules](https://docs.astral.sh/ruff/rules/): the family index. `B` (bugbear), `S` (bandit),
  `DTZ` (naive datetimes), `LOG` and `G` (logging), `ASYNC` (blocking calls in coroutines), `PTH`
  (pathlib), `TRY` (exception handling), `SIM`, `PERF`, `TC`, `ANN`.
- [`dataclasses`](https://docs.python.org/3/library/dataclasses.html): mutable defaults raising,
  field ordering under inheritance, the `eq`/`frozen`/`__hash__` interaction, `slots` constraints,
  `replace()` with `init=False`, and `__post_init__` versus base-class `__init__`.
- [Deprecations index](https://docs.python.org/3/deprecations/index.html) and
  [What's new in Python 3.13](https://docs.python.org/3/whatsnew/3.13.html): the removal schedule —
  `datetime.utcnow()` deprecated with no removal version, the asyncio policy API in 3.16, and the
  PEP 594 modules removed in 3.13.

## Security

- [Ruff `flake8-bandit` (S) rules](https://docs.astral.sh/ruff/rules/#flake8-bandit-s) and
  [Bandit](https://bandit.readthedocs.io/): the vulnerability catalog — shell injection, `eval`,
  pickle, unsafe YAML, weak hashes, non-cryptographic randomness, hardcoded credentials, insecure
  temporary files, disabled certificate verification, XML attacks, and `assert` used for enforcement.
- [`subprocess` security considerations](https://docs.python.org/3/library/subprocess.html#security-considerations):
  the `shell=True` injection warning and the argument-list form that avoids it.
- [`pickle`](https://docs.python.org/3/library/pickle.html), [`secrets`](https://docs.python.org/3/library/secrets.html),
  [`hashlib`](https://docs.python.org/3/library/hashlib.html), [`tempfile`](https://docs.python.org/3/library/tempfile.html),
  and [`tarfile` extraction filters](https://docs.python.org/3/library/tarfile.html#extraction-filters).

## Typing

- [`typing`](https://docs.python.org/3/library/typing.html): deprecated aliases and their version
  floors, `Protocol` and the documented limits of `@runtime_checkable`, `TypedDict`, `Self`,
  `Literal`, `Final`, `NewType`, and the note that the runtime does not enforce annotations.
- [Typing best practices](https://typing.python.org/en/latest/reference/best_practices.html) and
  [mypy documentation](https://mypy.readthedocs.io/): `--strict` as a goal, incremental adoption,
  unannotated function bodies going unchecked, `Any` disabling checking, and duck-typed parameters.
- [PEP 544 — Protocols](https://peps.python.org/pep-0544/),
  [PEP 649 — Deferred annotation evaluation](https://peps.python.org/pep-0649/),
  [PEP 695 — Type parameter syntax](https://peps.python.org/pep-0695/).

## Design anti-patterns

- [Python anti-patterns catalog](https://docs.quantifiedcode.com/python-anti-patterns/): the
  community catalog of correctness, maintainability, readability, security, and performance
  anti-patterns behind the idiom tables.
- [Stop Writing Classes](https://www.youtube.com/watch?v=o9pEzgHorH0): **Jack Diederich**, PyCon 2012.
  The case that a class with an `__init__` and one method is a function. Frequently misattributed to
  Raymond Hettinger, whose *The Art of Subclassing* is the complementary talk.

## Practitioner sources

Maintainer writing, cited where the documentation states a mechanism but not a judgement.

- [Facts and myths about Python names and values](https://nedbatchelder.com/text/names.html) —
  **Ned Batchelder**. The canonical model of names, values, and the "mutable presto-chango."
- [hasattr() — a dangerous misnomer](https://hynek.me/articles/hasattr/),
  [Please fix your decorators](https://hynek.me/articles/decorators/), and
  [Subclassing in Python redux](https://hynek.me/articles/python-subclassing-redux/) —
  **Hynek Schlawack**: how `hasattr` masks errors, what a wrapper's signature hides, and the
  composition-over-subclassing argument.

## Concurrency and performance

- [Python concurrency overview](https://docs.python.org/3/library/concurrency.html): selecting
  concurrent tools from CPU-bound versus I/O-bound work and execution style.
- [`asyncio` coroutines and tasks](https://docs.python.org/3/library/asyncio-task.html): task
  ownership, weak task references, cancellation cleanup, timeouts, and structured concurrency.
- [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html): executor
  ownership, shutdown, thread pools, process pools, futures, and deadlock cautions.
- [`multiprocessing` programming guidelines](https://docs.python.org/3/library/multiprocessing.html#programming-guidelines): safe imports, process start methods, resource passing, queues, joining, and avoiding shared state.
- [Python profiling tools](https://docs.python.org/3/library/profile.html): measuring execution before
  optimizing and choosing deterministic or statistical profiling tools.
- [Python data model — `__slots__`](https://docs.python.org/3/reference/datamodel.html#slots): memory,
  attribute, inheritance, weak-reference, and default-value consequences.

## CLI, subprocess, and async failure evidence

- [Linux `pipe(7)`](https://man7.org/linux/man-pages/man7/pipe.7.html) establishes that an empty pipe
  blocks while a writer remains open. [Codex CLI issue #20919](https://github.com/openai/codex/issues/20919)
  records a non-TTY stdin pipe hanging an unattended CLI. Together they support explicit stdin opt-in.
- [Python asyncio subprocesses](https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.subprocess.Process.wait)
  warns that waiting with unread `stdout=PIPE` or `stderr=PIPE` can deadlock and directs bounded-output
  callers to `communicate()`; concurrent drains extend that to output too large to buffer.
- [Python asyncio streams](https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamWriter.write)
  states that `write()` may buffer data and should be paired with `drain()`.
  [CPython issue 25441](https://bugs.python.org/issue25441) reproduces a broken peer becoming observable
  through `drain()`.
- [`asyncio.wait()`](https://docs.python.org/3/library/asyncio-task.html#asyncio.wait) defines its
  `(done, pending)` result and `FIRST_COMPLETED` behavior, from which carrying only `pending` follows.

## Test-harness failure evidence

- [Python task cancellation](https://docs.python.org/3/library/asyncio-task.html#task-cancellation)
  says cancellation is delivered at the next opportunity.
  [CPython issue #116048](https://github.com/python/cpython/issues/116048) reproduces cancellation
  before a task starts, when the coroutine body and its `finally` block never run.
- [`unittest` skipping](https://docs.python.org/3/library/unittest.html#skipping-tests-and-expected-failures)
  requires an explicit reason and offers conditional skip boundaries.
  [`ModuleNotFoundError`](https://docs.python.org/3/library/exceptions.html#ModuleNotFoundError)
  exposes the missing module through `name`.
  [pytest's `importorskip` deprecation](https://docs.pytest.org/en/latest/deprecations.html#pytest-importorskip-default-behavior-regarding-importerror)
  explains that catching broad `ImportError` can hide a broken installation, while
  [Ruff BLE001](https://docs.astral.sh/ruff/rules/blind-except/) encodes the broader rule to catch the
  expected exception narrowly.
- [Linux `killpg(3)`](https://man7.org/linux/man-pages/man3/killpg.3.html) states that group zero means
  the caller's process group and that POSIX leaves values at or below one undefined.
  [`subprocess.Popen`](https://docs.python.org/3/library/subprocess.html#popen-constructor) documents
  `start_new_session=True` as the safe Python interface to `setsid()`.

## License

Portions are adapted from material under this notice:

```text
MIT License

Copyright (c) 2025 TestMu AI / LambdaTest

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
