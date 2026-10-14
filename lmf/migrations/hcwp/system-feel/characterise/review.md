# HCWP system-feel — Characterise review packet

## Review state and boundary

Task 6 doer packet, 2026-10-14. **Awaiting independent review and revision-bound human approval; not approved for Convert.** No task checkbox is changed. No new validator findings were supplied with this execution. Earlier findings SF-G17–SF-G23 remain disclosed in `gaps.md` and their original/follow-up evidence is retained, not replaced. This packet does not author an approval, launch Convert/Refactor, implement product changes or complete iteration 002.

All short artifact names here are relative to `lmf/migrations/hcwp/system-feel/characterise/`; all commands below run from `/workspaces/legacy.modernisation.agent` unless stated otherwise. The packet comprises this document, every stable slice file, and reviewed original inputs selected in `review-files.sha256`. The manifest uses **repository-root-relative** paths. It does not hash itself: its SHA-256 is the approval revision and is reported separately in the run plan. The review document's own SHA-256 is also reported there. The factory run plan is an execution journal, not a bound product input.

Earlier documents' Task-1/2/3/4/5 status paragraphs describe their historical executions, not current aggregate status. In particular, pending-task/zero-scenario statements in the Task-2 documents do not supersede the fresh Task-6 observations below. Historical failed attempts and self-test collision sentinels are retained as diagnostic evidence, not counted as required scenario passes.

## Exact inputs and immutable approval

`input-inventory.md`, `input-membership.json`, `input-files.sha256`, `inventory-inputs.py`, original `input-gate-results.json` and its three logs bind the complete original inspection. Nine seed groups and supplemental assembly-line, Convert and Refactor trees are reconciled: **1499 files, 184 directories, 2 symlinks**. Directory membership includes hidden/untracked inputs and records link targets/resolution. A working-tree input is not assumed to equal HEAD. Existing unrelated user changes were inspected and preserved.

| Authority | Repository-root-relative path | SHA-256 |
| --- | --- | --- |
| Input manifest | `lmf/migrations/hcwp/system-feel/characterise/input-files.sha256` | `3ff28bcc423ef54f0915de0ce8f6a79f2b70cf92299c2a18805e6396156f874a` |
| Original patient source | `example-code/patient-banner (pseudononymised).txt` | `d0365ffb8b625eeb8085bf7cb23284837525caf61126a90756b9d8e330b51713` |
| Original KD03 source | `example-code/HCWP Core (pseudonymised) - single file.txt` | `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2` |
| Immutable baseline review manifest | `lmf/migrations/hcwp/characterise/review-files.sha256` | `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699` |

Individual hashes for vision, both seeds, original baseline artifacts/approval, current target/checks/browser, NHSW guidance/provenance, configuration and linked parity/Refactor reports are in the bound input manifest, not substituted by directory hashes. The original approval `lmf/migrations/hcwp/approvals/characterise-approved.md` independently binds the baseline revision above. Task 6 compared that revision and checked all **120 baseline review entries** read-only. No baseline verifier that rewrites evidence was invoked; iteration-001 artifacts and `lmf/docs/vision.md` were not modified. Its **KD03-001–040 and Q01–Q13** contract remains authoritative, including validation/notification identity, clearing, repeat and read-mapping quirks.

All Task-6 membership, per-file digest, exact manifest reconciliation, second-enumeration and immutable approval checks passed. Hash/membership/approval drift is a blocker, never permission to regenerate or rebaseline original inputs.

## Inspectable artifact map

- `behaviour.md`, `dependencies.md`, `gaps.md`: source-backed patient fields, mapping/retrieval, controlled age/death/status, alert/no-alert, school/Organisation, selected-patient/KDP retrieval/date ordering, physical values and separated seed-authored facets. Excluded display dependencies remain inventoried. Inline tokens resolve via `source-citations.json`; approved baseline paths/rule/scenario IDs remain explicit.
- `resource-reconciliation.json`: all 88 baseline resource identities plus additional patient/core identities, without invented prose. The complete unresolved inventory in `gaps.md` must feed later bilingual review.
- `fixtures.json`, `scenarios.json`, `fixture-scenario-contract.md`, `define-fixtures.py`, `validate-fixture-contract.py`, `task-3-contract-results.json`: 53 stable required SF definitions, all ten groups, explicit synthetic provenance, controlled clocks and 23 selected-patient history rows plus isolation/unsupported-contact sentinels. Structural validation was not itself reference execution.
- `reference/`: current C# runtime, compatibility/observation adapters, extraction script/manifest and 20 original-source spans. `reference/README.md` documents each retained rule and infrastructure adaptation. `verify` is executable and requires a fresh explicit `--evidence-prefix`.
- `migration-plan.md`: three future literal Convert slices and six accumulating Refactor slices; parity, all 40 baseline regressions, approval/staleness, application/persistence, browser/bilingual/asset gates. It proposes decisions without approving or implementing them.
- All original Task-2 evidence/logs, retention/cache follow-ups, Task-3/4/5 evidence, historical patch/snapshot/review notes and fresh Task-6 evidence are bound individually. `task-4-review-harness.patch` is explicitly historical, **not current code**; inspect current reference sources and fresh source hashes instead.
- `assemble-review.py`: exclusive-create manifest assembly and read-only verification of original inputs, passing fresh evidence, current source hashes, packet membership/digests and executable entry point.

## Exact fresh commands and results

All three commands used `PYTHONDONTWRITEBYTECODE=1`. Every retained evidence destination was fresh; existing destinations must reject writes.

```sh
python3 lmf/migrations/hcwp/system-feel/characterise/verify-source-citations.py --evidence-prefix task-6
python3 lmf/migrations/hcwp/system-feel/characterise/reference/test-harness.py --evidence-prefix task-6-selftests
lmf/migrations/hcwp/system-feel/characterise/verify --evidence-prefix task-6-final
```

| Gate | UTC start–finish (2026-10-14) | Result | Retained evidence |
| --- | --- | --- | --- |
| Required exact citation gate | 22:41:03.557696–22:41:05.032364 | exit 0; 3 documents, 102 tokens, 81 unique/resolved citations, zero failures | `task-6-source-citation-results.json`, `task-6-source-citation-verification.log` |
| Current-source harness self-tests | 22:41:05.086435–22:41:07.365024 | exit 0; 29 checks passed, zero failed; **not additional reference scenarios** | `task-6-selftests-harness-test-results.json`, isolated retained collision sentinel |
| Full reference re-execution | 22:41:07.491108–22:41:12.134224 | exit 0; **53 required/executed/passed; zero failed, skipped or errors** | `task-6-final-reference-results.json`, `task-6-final-reference-observations.json`, `task-6-final-reference-verification.log` |

Citation integrity evidence uses **`task-6-gate-results.json`**, never the Task-2 destination. Its input checks ran 22:41:03.599454–22:41:04.920584; all 1499 hashes/membership and approval passed. Exact nested commands, working directories, times and exits are retained there and in `task-6-input-hash-check.log`, `task-6-baseline-revision-check.log`, `task-6-baseline-hash-check.log`:

```sh
# root, default read-only enumeration inside citation gate:
python3 lmf/migrations/hcwp/system-feel/characterise/inventory-inputs.py --results task-6-gate-results.json
sha256sum --check lmf/migrations/hcwp/system-feel/characterise/input-files.sha256
# lmf/migrations/hcwp, independent baseline approval checks:
sha256sum characterise/review-files.sha256
sha256sum --check characterise/review-files.sha256
```

The final reference command repeated the same full gate at 22:41:07.596827–22:41:09.588439 using separate `task-6-final-reference-*` logs/results, then resolved all 81 citations again, checked reproducible extraction and bound Task-3 artifacts, built and executed the runtime. Python **3.13.5**, .NET SDK **10.0.401**; tool details/build output are in the verification log. Both current-source builds succeeded with zero warnings/errors. Actual/expected observations and classifications for each SF-001–SF-053 are retained, not merely aggregate assertions.

| Required group | Executed/passed memberships |
| --- | ---: |
| G01 full included summary | 2/2 |
| G02 missing optional values | 7/7 |
| G03 controlled age/death/status | 12/12 |
| G04 alerts and no-alert triggers | 7/7 |
| G05 school and Organisation lookup | 7/7 |
| G06 selected-patient isolation | 7/7 |
| G07 zero/one/multiple KD03 retrieval | 4/4 |
| G08 descending contact dates | 2/2 |
| G09 explicitly undefined equal-date ordering | 3/3 |
| G10 physical/reason/repeat facets | 13/13 |

Groups overlap; **53 unique executions**, not the sum of membership counts. Equal-date assertions check full unordered tie membership and original-method ordering keys, never infer a tie rule from observed sequence. No final-application baseline regression, original-system execution, browser flow, translated UI or Convert parity is claimed here. Those future gates remain in `migration-plan.md`.

## Actual adaptations requiring reviewer acknowledgement

These are disclosed reference boundaries, not operational legacy infrastructure proof. Inspect current `reference/README.md`, generated `Legacy.cs`, `Compatibility.cs`, `Program.cs`, original spans and extraction manifest.

1. Exact source name/address, age, Organisation/school, ShowAlert, physical lookup, service query and complete GetKdpResults expressions compile with minimal compatibility types. Clock replaces DateTime.Now explicitly. No target application source supplies reference rules.
2. LINQ-to-Objects synthetic entity graphs and repository/unit-of-work doubles replace EF6/Oracle. AsNoTracking is identity; saved-row mapping is a disclosed identity read adaptation, not proof of SQL, database transactions, AutoMapper or complete EF mapping.
3. Selected summary graph/AutoMapper and web-view adapters observe known conditions/arguments; unavailable enum/status/constants/formatting prose remain symbolic. Resource.Format returns identities/arguments, not recovered clinical messages. Birth-date presentation is controlled en-GB, not universal legacy-culture parity.
4. Original all-KDP retrieval executes before a labelled KD03-only scope adapter. Original date-only delegate ordering stays separate from future recorded-date/ID pagination keys.
5. Recorded/not-examined, initial/repeat and physical-only Has concern are explicitly seed-authored read facets. Applicable Heart/Hips/Eyes/Testes/PhysicalGeneral value 2 drives concern; social/family/domestic fields and severity are excluded. Null remains distinct from Not assessed; no persisted aggregate status exists.
6. UI condition/resource-call observations do not reproduce Windows/MVC events, HTML/encoding/focus/dialog acknowledgement. Access-control/session/remote/default-access are excluded no-op/inventoried dependencies. Excluded display does not remove shared retrieval from dependencies.md.

## Gaps, intentional differences and human decisions

Full classified stable register: **SF-G01–SF-G23** in `gaps.md`. No clinical/product/translation decision is made by this packet.

- **SF-G04 — fixture author + product owner:** invented Organisation lacks health-board-concept confirmation. Health board wording separately requires an explicit owner decision. Retain **Organisation** pending both; Characterise may disclose this unresolved item, but no agent may silently approve the label.
- **SF-G01/G02/G03/G06/G14/G15 — legacy maintainer, clinical/product owner and reference reviewer:** accept the bounded symbolic resource/status/format, web age path, controlled-clock, graph/KD03/UI adaptations, or supply authoritative missing evidence and renew review. Missing messages must not be invented or clinically translated. Malformed/null/multiple-match graphs and unavailable Oracle age/UI behaviour are not guaranteed by well-formed extracted tests. No new source/baseline replacement rule was found.
- **SF-G07/G08:** fixtures now document invented names, addresses, deliberately nonvalid SYN-NHS strings, schools, organisations, alerts and histories. Their 23-result volume is artificial paging/filter test data, **not typical clinical history**; it does not resolve health-board meaning.
- **SF-G05/G09–G13 — product owner/application engineer/design/accessibility/translation reviewers:** seed authorises shell/banner, routes/detail/save navigation, filter/query/URL semantics, pagination and stable extra ordering keys, bilingual draft copy/fallback/state retention as intentional enhancements. They are not legacy UI rules. Invalid URL/page and local-demo language-persistence policies in migration-plan.md remain proposals requiring documented choices/tests before implementation. Professional Welsh review remains outstanding.
- **SF-G16:** extracted-reference, local-demo, synthetic-data, draft-Welsh, EF InMemory, unverified PostgreSQL/production and deferred load/performance limitations remain. Original EF6/Oracle/Windows/UI/resources are unavailable. Pagination itself is required later; no production-scale proof is claimed.
- **SF-G17–SF-G23:** evidence overwrites, caches, missing implementation diff, self-test prefixes/ambient DLL, bare entry point and stale historical patch findings have mechanical follow-ups and retained tests. Task 6 obeys their prefix/retention/exclusion rules and reran current-source self-tests. Independent validator review is still required; doer tests are not validator or human approval.

The original baseline warning/error inventory and unavailable prose remain unresolved in full, including newly inspected excluded scheduled identities. Honest identity/argument fallback is the only evidenced adaptation. No professional Welsh or clinical prose approval exists.

## Review binding, exclusions and reproduction

From repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 lmf/migrations/hcwp/system-feel/characterise/assemble-review.py --capture
PYTHONDONTWRITEBYTECODE=1 python3 lmf/migrations/hcwp/system-feel/characterise/assemble-review.py
sha256sum --check lmf/migrations/hcwp/system-feel/characterise/review-files.sha256
sha256sum lmf/migrations/hcwp/system-feel/characterise/review.md lmf/migrations/hcwp/system-feel/characterise/review-files.sha256
```

Capture is once-only, never an input rebaseline. Default assembly verification is read-only and repeats the complete original input/approval gate, compares current source hashes to fresh evidence, and rejects changed slice membership/digests. All stable slice artifacts (including hidden `.gitignore`, source scripts, original Task-2 evidence and every follow-up/fresh textual evidence) are directly bound. Slice compiler `reference/bin/` and `reference/obj/`, **every `__pycache__` directory and every `*.py[cod]` file** are excluded. No interpreter cache is an evidence artifact. Original input manifests themselves remain bound and unmodified: original input cache bytes, where inventoried, are enforced only by that immutable input gate, never listed as direct review evidence. Other baseline generated members are pre-existing reviewed inputs, not newly generated slice compiler output. Packet exclusions do not waive original input completeness.

Before a future progression, verify both manifest SHA-256 and all listed bytes from the documented root, original input membership/approval and current reviewed evidence. Fresh reruns use another prefix and must not delete/overwrite historical evidence; additional packet artifacts or changed decisions require renewed review, not silent approval reuse.

## Human approval pause

Present this exact packet and its manifest revision to the product owner. Only the human operator may create `lmf/migrations/hcwp/system-feel/approvals/characterise-approved.md`, naming the exact **SHA-256 of this `review-files.sha256`** and state **approved for progression to Convert**, with acknowledgement of adaptations, limitations and unresolved decisions. No approval file is authored here. Absent, malformed or stale approval blocks Convert; a successful agent review loop cannot substitute for it. Stop at this Characterise milestone, not iteration-002 completion.
