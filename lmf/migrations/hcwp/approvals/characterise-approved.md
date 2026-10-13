# Characterise approval — HCWP KD03

## Approval

- State: approved for progression to Convert
- Reviewer: JoelAndrewHowe
- Approval date: 2026-10-13
- Review revision: `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`
- Revision definition: SHA-256 of `characterise/review-files.sha256`
- Reviewed files: every file and content hash listed in `characterise/review-files.sha256`

The reviewer explicitly approved this exact Characterise revision after reviewing
the generated handoff and answering its pending human decisions. This approval
permits the bounded migration to progress to Convert. It does not approve Convert
or Refactor, and it does not claim parity with the complete Windows/Oracle system.

## Verification accepted

The following command was rerun from the repository root:

```sh
lmf/migrations/hcwp/characterise/verify
```

Result:

```json
{"total":40,"passed":40,"failed":0,"skipped":0}
```

The review inventory was also checked from `lmf/migrations/hcwp`:

```sh
sha256sum --check characterise/review-files.sha256
```

Every listed file matched. The inventory itself produced the review revision
recorded above.

## Approved decisions

1. The scope is the bounded KD03 add-and-read-back workflow described in
   `characterise/migration-plan.md`. Search, editing/deletion, scheduled entry,
   appointment/recall processing, database migration, deployment and other
   contact types remain excluded.
2. Source-backed user-visible quirks are preserved through Characterise and the
   literal Convert baseline. In particular, head circumference `150` remains a
   demonstration of field-path rejection and direct-save acceptance.
3. The remaining source-backed technical quirks Q01–Q13 are preserved through
   Convert. Possible corrections require deliberate review during Refactor.
4. The labelled synthetic patients, operational lookups, schedule, BMI limits,
   centile bands, fixed clock/IDs and message substitutes are accepted as test
   fixtures, not clinical policy or proof of production values.
5. The KD03-only adapter boundary is accepted as migration scope enforcement,
   not behaviour attributed to the legacy validator.
6. The extracted-reference, UI, mapping, persistence and excluded-infrastructure
   limitations in `characterise/review.md` are accepted for this bounded stage.
   Evidence may be described only as parity with extracted legacy logic, not
   full-system, Windows, EF6 or Oracle parity.
7. The inconsistent declined-value behaviour is preserved for Convert and is to
   be reconsidered explicitly during Refactor's UX review.

## Invalidation rule

Any change to a file listed in `characterise/review-files.sha256`, or to the
source, target description, approved behaviour or scenarios, invalidates this
approval. A changed packet must be reverified, re-inventoried and approved as a
new revision before conversion continues.

This is the manual approval convention used by the tutorial assembly lines. It
is separate from, and does not invoke, `lmf/implementation/lmf approve`.
