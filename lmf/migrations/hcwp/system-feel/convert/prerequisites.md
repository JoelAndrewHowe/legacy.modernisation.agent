# Convert prerequisite inspection — Task 1

Task remains unchecked. No validator findings were supplied after the findings heading; none are invented. Existing unrelated working-tree changes were inspected with `git status --short` and preserved. Only new `system-feel/convert/` artifacts and the run-plan journal are changed.

## Commands (from `lmf/migrations/hcwp`)

```sh
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/check-prerequisites.py --evidence-prefix task-1
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/test-prerequisites.py
```

The first command passed (exit 0). Evidence: `evidence/task-1/prerequisites.json`, `packet-verification.log`, `input-identities.sha256`. Ten isolated approval checks passed with zero failures/skips in `approval-tests.json`. Reusing `task-1` returned exit 1 before any write. Choose a fresh evidence prefix for subsequent checks; existing evidence is never replaced.

The gate checks exact approval fields, SHA-256 of the manifest and review document, then invokes the approved `characterise/assemble-review.py` in **read-only** mode. That helper reconciles all nine required input groups, full input membership, 1499 input digests, the baseline approval and 120 baseline review entries, all 1690 slice review entries, and current-source passing reference evidence. The gate records 1692 identities (review entries plus manifest and slice approval). Absent/malformed/stale approval, missing/changed bytes, or membership drift returns nonzero. Tests mutate temporary synthetic files only, not approval or source bundles. No capture, rebaseline, evidence-writing baseline runner, build or reference rerun was invoked.

Approved revision: `6a44e9fcd19299d0886b6ccb7e48457d04b89b5913326ce445dba58cb246c655`.
Review document: `b5d76bd805491ca02bf48b4d0b52490884d3717c8a25f634fa72517db7b1fa4b`.
Human approval file: `49838b9d07bc8a6699221b65b540d770d416318ebabd2d21be8e7050b93dddc0`.
All individual input hashes are recorded, not replaced by a directory digest.

## Reading and interpretation

Inspected the vision, both iteration contracts, patient PersonService/name/address/age/status/school resolvers, complete original GetKdpResults, both approval files, both Characterise review packets, the slice behaviour/dependencies/gaps, fixture/scenario contract and representative definitions, reference README and review-assembly/input-gate implementations, current Kd03Recording application boundary, checks driver, browser flow, target limitations, NHSW context and pinned asset provenance. All reviewed packet/input bytes were opened and cryptographically checked; this is not an assertion of exhaustive semantic review of every binary or dependency file.

Historical packet paragraphs saying “awaiting approval” or “not executed” describe earlier tasks. The separately authored, current human approval and bound Task-6 reference evidence are authoritative: 53 executed/passed, zero failures/skips, plus 29 harness checks and 81 resolved citations. These retained results were verified, not rerun or newly claimed as Convert parity. The 40 iteration-001 scenarios and Q01–Q13 remain unchanged.

Approval resolves Health board wording and target URL/language policies, but **does not change approved fixtures**. They still use an invented Organisation and deliberately nonvalid SYN-NHS values. Future Refactor demonstration fixtures must document Welsh-health-board concepts separately; do not rewrite Characterise fixtures or smuggle that wording into Convert. Equal-date ordering is unspecified: recorded-date/ID tie-breaks, filters, pagination, routes and bilingual presentation remain Refactor-only.

## Boundary and limitations

This task implements only the mechanical prerequisite gate. No patient-summary/results port, parity comparison, application/UI change, human approval or stage completion is claimed. Evidence remains extracted legacy logic with symbolic resource/lookup and synthetic repository adaptations, not original Windows/Oracle/EF6 execution. Local demo, synthetic data, unavailable clinical prose, draft Welsh, EF InMemory, unverified PostgreSQL/production and deferred load testing remain limitations. Every subsequent Convert executable must call this prerequisite gate before doing conversion/parity work; this task does not yet create those executables.
