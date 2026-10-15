# Task 7 — final gate execution and assessment

No validator findings were supplied after the request heading (`suppliedValidatorFindings: []`). No new execution failure was encountered. This assessment does not create human approval, change stage state or mark the external plan done. Existing unrelated working-tree changes were inspected and preserved. No application, approved input, fixture, scenario or approval was changed in this task.

## Fresh execution

From `lmf/migrations/hcwp`:

```sh
system-feel/refactor/verify --evidence-dir system-feel/refactor/evidence/task-7-final
```

Exit 0, UTC **2026-10-15T16:34:15.715713+00:00–16:37:48.123849+00:00**. The packet's `results.json` retains exact nested commands, working directories, exit codes and logs. It executes both required existing commands, `refactor/run-approved-scenarios` (through the regression chain and again through the legacy gate) and `refactor/verify-gate`. All 16 count-bearing slice suites passed; zero failures/skips/errors. The legacy gate also passed every individual command and all four counted suites. Before/after immutable-input and current revision-bound human-approval checks passed; no approval was authored or regenerated.

| Evidence | Passing observations |
| --- | --- |
| `reference-convert/results.json` | 53 exact approved extracted-reference/Convert comparisons |
| `regression/regression/regression/prerequisites-and-regression/parity/` | All 40 iteration-001 scenarios on each of reference, Convert and Refactor |
| Same directory, `shared-sf/results.json` | 34 applicable shared application-boundary comparisons |
| Same directory, `queries.json`, `persistence.json` | 43 query/detail/isolation/order/paging checks; 4 fresh-context persistence checks |
| `regression/regression/history.json` | 16 history/detail checks |
| `regression/regression/browser/results.json` | 8 Chromium history/detail/URL-state checks |
| `regression/regression/regression/browser/results.json` | 7 Chromium shell/route/recording checks |
| `regression/language-unit.json`, `regression/browser/results.json` | 7 language/inventory checks; 9 bilingual Chromium groups |
| `legacy-evidence/gate-results.json` | Configured style, build (zero warnings/errors), 4 model, 4 persistence, 40 regressions and 6 full recording-flow Chromium groups |
| `verifier-tests.json` | 19 fail-closed gate-contract tests |

Banner/alert renderer and recording-flow unit checks also pass; exact counts are in `results.json`. Browser evidence covers English and draft Welsh, narrow/wide routes, real saved detail and safe not-found, keyboard reachability/visible focus, skip link, landmarks/headings/active navigation, labels, error associations/summary links, alerts, filtering/pagination, URL/language/draft retention, rendered contrast and absence of unexpected external requests. Local pinned-asset checks run in the carried-forward chain. The alert-bearing presentation uses the documented test-only rendered fixture, not a product patient-switch feature.

Retained: **145 PNG screenshots**, per-scenario observations, browser accessibility/HTML snapshots, commands, timestamps, build/style output, asset/source/evidence hashes, and tool versions. The bilingual browser report includes 10,644 measured colour samples (including diagnostics, not 10,644 independent accessibility tests). Chromium **156.0.8078.4**, Python **3.13.5**; exact .NET/Node/Playwright versions are in `dotnet-info.log`, `node-version.log` and `browser-tool-versions.log`. The narrow Welsh results screenshot was also opened for visual inspection; automated layout assertions, rather than that downscaled image alone, establish the bounded overflow checks.

## Independent post-run inspection

After the gate exited, recomputed SHA-256 for every entry in the top-level `source-identities.sha256` (**136**) and `evidence-identities.sha256` (**312**): all matched. Independently checked every counted suite for positive complete passes and zero failures/skips. `git diff --check -- refactor system-feel/refactor` exited 0. This new report was written afterward and is not claimed to be part of that execution's source manifest. Fixed-path legacy evidence was retained in the fresh packet; older failing development packets remain historical failures, not passing evidence.

## Parity and enhancements — separate claims

**Source parity:** approved patient-summary mapping/formatting/status/alert and KD03 retrieval behaviour match the extracted legacy reference. The 53-case full reference/Convert runner and 34 applicable shared application-boundary comparisons retain their documented adaptations (`task-6.md`, `shared-scenarios.md`). The source leaves equal-contact-date ordering unspecified.

**Carried-forward iteration 001:** all 40 approved observations continue to match across all three implementations, including validation, warning/confirmation identities, calculations, declined/invalid no-save outcomes, repeat recalculation, fresh-context read-back and patient isolation. No approved baseline was weakened or reapproved.

**Approved intentional presentation enhancements:** filters with AND/OR semantics, query-boundary pagination, stable contact-date/recorded-date/internal-ID descending ordering, readable complete details, safe not-found/invalid-state handling and URL-state restoration. Internal IDs remain technical routing/ordering keys, not clinical display content. Health-board wording uses documented synthetic Welsh-health-board fixtures, not a reinterpretation of every legacy organisation.

**Product-authored UX, no legacy parity claim:** pinned local NHSW shell and identity, synthetic-data notice, routed results/details/recording workflow, selected-patient banner, English/draft-Welsh inventory and language switch, accessible interactions, responsive presentation and synthetic long-history demonstration. These are new target behaviour, not recovered Windows UI evidence.

## Limitations

Evidence is parity with extracted legacy logic and documented dependency doubles, not execution of the original Windows/Oracle/EF6 system. Demographics, alert fixtures and 23+ result volume are synthetic test inputs, not clinically typical history. Welsh is draft awaiting professional language review. Original warning/error prose remains unavailable; resource identities and honest fallbacks are retained in the unresolved-resource inventory, not invented clinical translations.

Persistence is process-local EF Core InMemory, reset on application restart; no relational, Oracle, PostgreSQL, Azure, concurrency, production deployment or clinical assurance is established. Browser evidence is bounded Chromium/component inspection, not full WCAG or assistive-technology certification, all-browser support or native-popup certification. Performance/load testing beyond deterministic query/paging semantics remains deferred. Patient search/switching, access control, editing/deletion and other contacts remain excluded.

The required final gate evidence passes for validator/operator review. Human acceptance and external plan updates remain outside this doer action.
