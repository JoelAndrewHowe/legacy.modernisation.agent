# HCWP KD03 synthetic recording

Requires .NET SDK 10, Python 3 and bash. EF Core InMemory is pinned to 10.0.0;
restore may need NuGet. From `lmf/migrations/hcwp`:

```sh
dotnet run --project refactor/src/Hcwp.csproj --urls http://127.0.0.1:5187
```

Open the local URL. Patient 101 is synthetic, already selected. Enter KD03
fields, save, respond to applicable confirmation and inspect saved read-back.
Invalid input does not save. Start new result permits another contact; Reload
reads persistence independently of the draft. Browser reload retains data within
the process; restart resets it. The demonstration clock is 15 March 2025.

The interface uses vendored official NHSW assets; see `nhsw-provenance.md`.
`full-flow.md` documents the implementation, evidence and limitations.
Fresh three-way parity passes all 40 approved scenarios on each implementation,
with zero failures/skips and exact observations; see `parity-report.md`. Reproduce
with `refactor/run-approved-scenarios` (evidence in `evidence/parity/`).
Build/configured style/persistence/current-browser verification now has positive
executed evidence: see `verification.md` and reproduce with `refactor/verify-gate`.
**Refactor is not declared complete:** final limitations documentation and
completion assessment remain pending. No task checkbox was changed.

## Reproduce full-flow smoke/regression evidence

Requires Node.js/npm and pinned Playwright Chromium:

```sh
npm ci --prefix refactor/browser
(cd refactor/browser && npx playwright install chromium)
refactor/verify-flow
```

If browser system libraries are missing, use Playwright's `install-deps chromium`
with appropriate privileges. Missing prerequisites fail, never skip. Port 5189
must be free; the runner starts/stops a freshly seeded real app.

Evidence is under `evidence/full-flow-*`. Historical `verify-preview` and
`verify-nhsw` checks targeted the smaller preview interface; do not use their
old reports to certify this expanded interface. `architecture.md` and
`validator-findings.md` retain historical architecture and repair context.

Parity is with extracted legacy logic, not the original Windows/Oracle system.
Temporary EF InMemory storage does not verify PostgreSQL. Other contacts,
search, editing/deleting, appointments, recalls and production infrastructure
remain excluded.
