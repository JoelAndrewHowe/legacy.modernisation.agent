# Task 6 — expanded executable verification

No validator findings were supplied with this task (`suppliedValidatorFindings: []`). The external plan remains unchanged/unchecked. This is verification implementation, not the final iteration completion report.

## Entry point

From `lmf/migrations/hcwp`:

```sh
system-feel/refactor/verify
# Or retain a named, fresh packet:
system-feel/refactor/verify --evidence-dir system-feel/refactor/evidence/my-fresh-run
python3 system-feel/refactor/test-verifier.py
```

Requires .NET 10, Python 3, Node, installed Playwright dependencies and actual Chromium. Missing prerequisites/runtime failures are failures, never skips. Evidence directories must be new and Refactor-owned. No approval is created or changed.

The entry point executes current immutable-input/approval checks, all 53 reference/Convert comparisons, the existing task-2 through task-5 chain (40 approved regressions, query/isolation/pagination/detail tests, fresh-context persistence, shared application-boundary comparisons, Chromium shell/history/language suites), then the existing `refactor/verify-gate` (including configured style and full recording flow). It rejects empty, failed, skipped, noninteger, incomplete and runtime-error aggregates. Nineteen positive/negative gate-contract tests exercise that rejection policy, including individual legacy command statuses, nested suite counts and runtime errors even when the outer summary reports zero failures. Every nested count-bearing suite is inspected, with at least nine required bilingual browser checks. Reports retain commands, exit codes, clocks, versions, source/evidence SHA-256 identities, accessibility snapshots and screenshots; fixed-path legacy gate outputs are copied into the fresh packet.

## Extensions to the existing test stack

- `refactor/browser/language.mjs`: English/draft Welsh, 320/1280px, results with paging, a real saved detail, safe missing detail, recording and summary. Checks landmarks, active navigation, one H1, associated nonempty labels, no overflow, normal no-alert state, every enabled form control and every link/button reachable through native Tab, keyboard skip-link activation, computed rendered text/control/focus contrast using the existing `contrast.mjs` approach, accessibility snapshots and screenshots. Existing language/filter/detail-return/reload/draft-retention checks remain.
- Bilingual invalid recording: repeat confirmation proceeds to validation, named alert summary, summary links, invalid-state/description associations, focus transfer, narrow/wide rendered error contrast and screenshots.
- Real PatientBanner HtmlRenderer harness emits English and Welsh alert-bearing documents. Chromium checks named alert semantics, both synthetic alert texts, isolation, narrow/wide layout and rendered contrast. This is a test-only intercepted document, not a product patient switch or route.
- Existing `flow.mjs` now scopes saved-result assertions to `#saved-results`, counts one contact-details group per persisted record, and asserts human-readable saved fields rather than obsolete raw codes/internal patient IDs. Declined confirmation, rejected input, successful save, read-back, repeat recalculation and fresh-circuit assertions remain. Warning assertions distinguish clinical resource warnings from the synthetic demonstration banner.
- Shared-shell and recording `data-ready` attributes expose completion of interactive initialization; browser checks no longer mistake prerendered HTML for attached event handlers. They do not alter recording/domain rules.

## Full reference/Convert reexecution adaptation

`verify-parity.py` links unchanged Convert source into a fresh evidence-owned runner. Reflection calls the existing private observation adapter without changing its implementation. The immutable Convert CLI enforces its *pre-Refactor* whole-target snapshot, which is intentionally stale after approved Refactor edits. This runner instead first enforces the Refactor immutable-input/approval gate, then executes all 53 approved requests against the unchanged port and reference, compares each approved expectation and complete reference/Convert observations (including structural ordering evidence), and retains every request/observation. The original Convert CLI/source/gate and historical evidence are untouched. This is extracted-reference parity, not Windows/Oracle execution.

## Development observations addressed

Retained failing packets are not passing evidence. `task-6-language-01` through `-11` exposed harness assumptions: results use accessible articles rather than a table; primary-navigation current state must exclude pagination; native date segments must not be remeasured as separate controls; the recording route must await its interactive render and accept the repeat prompt before expecting validation; link focus transfer is asynchronous; focused language buttons must be measured as focus rather than neutral boundary samples. These were corrected without weakening contrast thresholds or changing clinical rules. `task-6-language-12` passes all nine checks; `task-6-language-15` also passes after extending native keyboard/focus checks to all links/buttons and skip-link activation. The extra focus coverage exposed the contrast sampler's single-shadow assumption (`-13`/`-14`): NHSW pagination paints a yellow top and dark bottom shadow, and the current-page blue fill is retained. The sampler now retains all painted shadow candidates and measures qualifying portions against each adjacent background, preserving the same 3:1 threshold rather than requiring one colour to contrast against both neighbours. `task-6-gate-01` failed on pre-interactive language switching; `task-6-gate-02` correctly rejected the old full-flow selector that counted the newly added patient banner as a saved result. The full-flow selector/readback updates address that incompatibility. `task-6-gate-03` exposed retained pagination click focus affecting its neutral-style assertion; history checks now await interactivity, remove click focus before comparing neutral current-page colours and retain those colours. `task-6-gate-04` passed the complete gate before the additional all-link bilingual focus coverage; final current-source execution is retained separately.

## Follow-up doer verification

No validator findings were supplied in the follow-up request either. Inspection found that the slice verifier trusted the legacy gate's outer counters without validating its individual checks. `require_legacy_checks` now rejects hidden failed/skipped commands, empty/failed/skipped count-bearing suites, malformed checks, boolean counters and runtime errors. Eleven additional contract cases cover this boundary (19 total passing). This is a verification hardening observation, not a supplied validator finding.

Fresh execution: `system-feel/refactor/verify --evidence-dir system-feel/refactor/evidence/task-6-gate-06` passed all 16 counted suites with zero failures/skips, including 53 reference/Convert cases, all 40 approved regression cases per implementation, nine bilingual Chromium checks and the existing Refactor gate. Commands, versions, hashes, observations and screenshots are retained in that packet. Its source identities describe the executed code; this follow-up documentation/summary update occurred afterward. The plan remains unchecked.

Limitations: synthetic fixtures and volume, extracted-reference evidence, draft Welsh awaiting professional review, unresolved original resource prose, EF in-memory local demonstration, no PostgreSQL/production assurance, no full WCAG certification or load/performance claim. The final reporting/acceptance task remains separate.
