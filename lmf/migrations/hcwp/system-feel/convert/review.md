# Task 5 — Convert mechanical evidence review

No validator findings were supplied (`validatorFindings: []`). This is a doer review, not independent human approval. The plan checkbox remains unchanged; no Refactor work was performed.

## Command and outcome

From `lmf/migrations/hcwp`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/review-convert.py --evidence-prefix task-5-review
```

Passed, exit 0. Evidence: `evidence/task-5-review/review.json` and command logs. Use a fresh prefix for reruns; outputs are exclusive-create. Failures stop the review with nonzero status and recorded errors, not skips.

The reviewer invokes the existing producer with a fresh bundle, then independently checks its retained evidence rather than accepting the producer exit alone:

- Fresh nonincremental Release build; current source and binary identities verified.
- All five approval/input gates pass; 1692 input identities unchanged before/after, including iteration-001 inputs. No baseline or reference evidence regenerated.
- All 53 exact approved scenarios pass with zero failures/skips; scenario membership/order and expectations match the approved packet. A separate recursive, type-sensitive comparator checks every retained reference/converted observation without allowing extra keys, missing rows or changed ordering.
- Ten approval rejection tests and eleven comparator/ordering-contract tests pass with zero failures/skips.
- Three historical source-preservation checks pass and their current source/target identities match. Approved rule bodies remain separate from application integration; no routes, presentation, filtering, pagination, bilingual UI or deterministic equal-date tie-break added.
- Report-bound manifest verified against all 45 artifact identities.
- Bare DLL invocation rejects missing gate arguments with exit 2. Reusing the producer evidence prefix rejects with exit 2; all 30 retained bundle files remain byte-identical.
- Scoped `git diff --check` passes.

Fresh observations, build output, timestamps, versions and all prerequisite results are under `evidence/task-5-review-bundle*`. The artifact manifest binds the tools/source present during execution, including `review-convert.py`. This subsequently written review narrative and the plan journal are not part of that producer manifest.

## Disposition and boundary

The reviewed mechanical Convert gates pass. No supplied validator findings remain to address. This review does not mark the task or stage complete; that decision remains with the validator/runner. Refactor requires its own run.

`report.md`, `port.md` and `parity.md` retain provenance, adaptations and limitations: parity is with approved extracted reference logic and synthetic fixtures, not original Windows/Oracle execution or clinical assurance. Equal-date ordering remains unspecified. Missing clinical resource prose remains unresolved. The application's 40 iteration-001 regression scenarios and the seed's UI/browser/accessibility/persistence gates were not run here and must execute during Refactor. No production, PostgreSQL, Welsh-language professional approval or load-testing claim is made.
