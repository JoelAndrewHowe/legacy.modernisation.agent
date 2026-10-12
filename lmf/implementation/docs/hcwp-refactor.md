# HCWP Refactor evidence

## Gate and retained workspace

`workspaces/hcwp/migration/state.json` records `completed`, with Characterise,
Convert and Refactor accepted. Current and human-approved revision are both
`6515ffc7f2a4f89ff8efc5bbb0887b5031ebf9cc02f6191de3c225cc49984ad2`.
Characterise and Convert each retain one attempt; Refactor retains two. This is
an adapter-generated migration, **not a verified real-agent migration**.

The runner-executed Refactor verifier builds the final assembly, checks whitespace
formatting for the introduced C# service/entry-point/persistence checks, runs the
approved scenarios against the independent reference and final assembly, then
runs fresh-context EF persistence checks and actual Playwright Chromium checks.
The shared suite establishes **parity with extracted legacy logic**, not parity
with the original Windows/Oracle application.

Retained evidence under `workspaces/hcwp/migration/refactor/`:

- `parity-report.json`: 371 approved scenarios and their expected, reference and
  final observations; commands, approved revision and limitations.
- `persistence-report.json`: four passing checks, zero failures/skips: detached
  fresh-context field read-back, invalid submissions without writes,
  confirmation/repeat/patient isolation, and decline/BMI warnings.
- `browser-report.json`: six passing Chromium checks, zero failures/skips:
  KD03 fields/add/read-back, reload retention, unsupported contact absent from
  UI, invalid field without save, cancelled warning without save, and confirmed
  second result with repeat read-back. `browser.png` retains a screenshot.
- `build.log`, `style.log`, `reference.log`, `refactored.log`, `persistence.log`,
  `browser.log`, `server.log` and `attempts/`: execution and runner diagnostics.
- `refactor-manifest.json` and `REFACTOR.md`: source/approval binding and adaptations.

## Reproducible validation

From `lmf/implementation/`:

```sh
python3 -m unittest discover -s tests -p 'test_hcwp_refactor.py'
python3 -m unittest discover -s tests
python3 workspaces/hcwp/migration/refactor/verify.py
```

The first two commands were executed for this documentation follow-up: the
Refactor regression passed (1 test), and the complete suite passed (12 tests).
The Refactor regression generates a fresh isolated migration and runs real
build/style/parity/persistence/browser gates. It also detects a calculation
mismatch, an omitted head-circumference field validator, an unavailable browser,
and changed approved inputs, then verifies recovery. Invalid-field probes use a
distinct date so duplicate-date rejection cannot mask omitted field validation.
Physical dropdown labels and saved selections are checked in Chromium using
source-extracted lookup dictionaries, not arbitrary byte input.

## Launch and limitations

Requires .NET 10, EF Core InMemory 10.0.0 restore access, Python Playwright and
Chromium. Launch from this directory:

```sh
dotnet run --project workspaces/hcwp/migration/refactor/app/Hcwp.csproj -- --urls http://127.0.0.1:5080
```

Patient 1001 is preselected; patient 2002 supplies a repeat-isolation fixture.
The clock, patient data, schedule/ranges and SYNTH location/examiner values are
invented demonstration fixtures documented in the generated `REFACTOR.md`.
Warnings use symbolic resource identifiers. Only KD03 is offered and supported;
unsupported submissions are also rejected by the persistence checks.

Data survives page reload only within the running application's lifetime.
Restarting resets the in-memory store. No PostgreSQL compatibility, original
Windows event/binding behaviour, real services/clinical lookups, Oracle
transactions, appointments, recalls, editing/deletion, production security or
real-agent execution is established. Real-agent evidence belongs to the later
plan task and must not be inferred from these deterministic adapter checks.
