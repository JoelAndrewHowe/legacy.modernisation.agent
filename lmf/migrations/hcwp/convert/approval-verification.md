# Characterise approval verification

Performed only the next unfinished task in `factory/runs/hcwp-convert/plan.md`: verify the operator-owned Characterise approval. The plan is unchanged; no task was marked done. No implementation or fresh scenario execution was performed.

## Result

`approvals/characterise-approved.md` is present and approves progression to Convert for the current reviewed packet. Reviewer: JoelAndrewHowe; approval date: 2026-10-13. Its revision definition is SHA-256 of `characterise/review-files.sha256`, not repository HEAD. The actual inventory hash exactly matches the approved revision:

`5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`

The approval covers every inventoried file, all current KD03-001–040 scenarios and the bounded reference artifacts. All **120** inventory entries match. Disposable build/cache files are excluded as documented in the reviewed handoff. Historical “awaiting approval” text in the immutable handoff does not override the subsequent operator approval. No human-owned blocker was found, and no additional approval attestation is required.

The approved decisions preserve Q01–Q13, synthetic fixture limitations, KD03-only scope enforcement and declined-value behaviour. They accept only extracted-legacy-logic evidence, not full Windows/Oracle, EF6 or save-service parity. Conversion may proceed in a subsequent task under those constraints.

## Recheck for this invocation

Repeated the approval verification because it remains the next unchecked plan task. The inventory check again exited 0 with all 120 entries matching; the inventory revision, approval hash, source, vision and iteration hashes remain exactly those recorded below. Inspection HEAD is unchanged. Read-only JSON assertions again confirmed all 40 required ordered scenario IDs, passing nonempty observations with no differences, matching source/fixture/scenario hashes, and an unfiltered retained report of 40 passes, zero failures and zero skips. No fresh execution was substituted for retained evidence. Approval is current; no human-owned blocker was found. No validator findings were supplied in this invocation, so no new repair was required. Only this verification record was updated; the unchecked plan task, approval and Characterise packet remain unchanged.

## Read-only checks

From `lmf/migrations/hcwp`:

```sh
sha256sum --check characterise/review-files.sha256
sha256sum characterise/review-files.sha256 approvals/characterise-approved.md \
  ../../docs/vision.md ../../iterations/001-characterise-and-migrate-hcwp.md \
  '../../../example-code/HCWP Core (pseudonymised) - single file.txt'
git rev-parse HEAD
```

Inventory check exited 0. Approval file SHA-256: `1dc949df7d3663db3ea9f93fbf0c07be95c2908b3480dc575cfcaff989145731`. Source hash remains `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2`. Vision and iteration/target description hashes match `characterise/input-reading.md`: respectively `a5280da556de24f8d6d9254df5b1bdd22ace59c7fc0a5ac64b9485dd71483444` and `73c53da335f85625dd0ce180d69eec64a21431f9ab8247a58520e0dfbd3addcd`. Inspection HEAD: `5bf640d31e7ce3b620111ada7e3dbda237c1861a` (context only, not the approval revision).

A read-only Python JSON inspection confirmed all 40 ordered scenario definitions are required, retained results cover those exact IDs with nonempty observations and no differences, report source/fixture/scenario hashes match current inputs, and the retained unfiltered verify report has 40 passes, zero failures and zero skips. These are checks of approved retained evidence, **not a new execution or a Convert parity gate**. The reference was not rebuilt because doing so may mutate inventoried build diagnostics.

## Validator findings

No findings were supplied after the user's findings heading. There is therefore no new validator defect to repair. Existing V01 is recorded as addressed in the approved Characterise packet: distinct inner `ValidationErrorsPrompt` and parent `ExamResultsErrorSavingPrompt`, actual parent notification, ordered errors and unchanged committed storage remain part of the contract to preserve. No reference or scenario repair was necessary at this approval-verification step; no validator approval is claimed.

Only this file under `convert/` was written. Operator approval, Characterise artifacts and the external plan were not changed. Any subsequent change to reviewed inputs invalidates approval as specified by the operator's invalidation rule.
