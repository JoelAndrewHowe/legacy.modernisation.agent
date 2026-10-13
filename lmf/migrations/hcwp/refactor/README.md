# HCWP KD03 architecture preview

Prerequisites: .NET SDK 10, Python 3 and bash. EF Core InMemory is pinned to
10.0.0; restore may require access to NuGet when it is not already cached.

From `lmf/migrations/hcwp`:

```sh
refactor/verify-architecture
dotnet run --project refactor/src/Hcwp.csproj --urls http://127.0.0.1:5187
```

Open `http://127.0.0.1:5187/`. Patient 101 is synthetic and already selected.
Choose a heart assessment and save. Reload reads EF-backed saved data; a browser
reload retains it within the running process. Restart resets the temporary data.
The fixture clock is fixed at 15 March 2025, not the current clinical date.

This is an **architecture preview**, not the complete browser demonstration.
NHSW integration and complete field/warning/confirmation UX are later plan tasks.
`architecture.md` describes the boundaries, executed evidence and limitations.
Executed preview-only browser verification is retained; no completed Refactor
gate or comprehensive browser verification is claimed.

## Reproduce the preview browser evidence

Requires Node.js/npm and Playwright's Chromium (pinned by `browser/package-lock.json`):

```sh
npm ci --prefix refactor/browser
(cd refactor/browser && npx playwright install chromium)
refactor/verify-preview > refactor/evidence/browser-preview-run.log 2>&1
```

On a host missing browser system libraries, install them with Playwright's
`install-deps chromium` command using appropriate privileges. Missing browser
prerequisites fail, not skip, the check. Port 5187 must be free: the test starts
and stops its own freshly seeded app. It executes Save, changes draft values
without saving and clicks Reload, then opens a separate browser context/circuit
and clicks Reload again. All three checks require live Blazor WebSocket traffic.
`evidence/browser-preview/results.json` contains outcomes and source/artifact
hashes; adjacent PNGs, rendered HTML and Playwright traces show the interactions.
Open a trace locally with `npx playwright show-trace <trace.zip>` from `browser/`.
See `validator-findings.md` for the supplied finding and bounded repair.
