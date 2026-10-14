# Characterise approval — HCWP system feel

## Approval

- State: approved for progression to Convert
- Reviewer: JoelAndrewHowe
- Approval date: 2026-10-14
- Review revision: `6a44e9fcd19299d0886b6ccb7e48457d04b89b5913326ce445dba58cb246c655`
- Revision definition: SHA-256 of `system-feel/characterise/review-files.sha256`
- Review packet SHA-256: `b5d76bd805491ca02bf48b4d0b52490884d3717c8a25f634fa72517db7b1fa4b`
- Reviewed files: every path and content hash listed in
  `system-feel/characterise/review-files.sha256`

The product owner explicitly approved this exact Characterise revision after
reviewing its evidence, adaptations, limitations and pending product decisions.
This approval permits the bounded migration to progress to Convert. It does not
approve Convert, Refactor, production deployment, clinical use or professional
Welsh translation.

## Verification accepted

The approved packet reports:

- all 1,690 review-manifest entries passed their SHA-256 checks;
- 53 of 53 required reference scenarios passed, with zero failures or skips;
- 81 of 81 source citations resolved, with zero failures;
- 29 harness self-checks passed, with zero failures; and
- the input inventory reconciled 1,499 files, 184 directories and 2 symlinks.

## Approved decisions

1. For this synthetic demonstration system, `Organisation` represents a Welsh
   health board only. Refactor will deliberately display the label **Health
   board**. Fixtures must use Welsh health boards and must not imply that the
   legacy system used this wording or that arbitrary organisations are health
   boards.
2. Invalid or unavailable filter tokens and invalid page or page-size values
   must be surfaced in an error summary headed **Invalid filters**. Valid values
   continue to apply. Invalid filter tokens are ignored; invalid page values
   fall back to page 1; invalid page sizes fall back to 10; a positive page past
   the available range resolves to the last non-empty page, or page 1 when
   there are no results. These are intentional product rules, not legacy
   behaviour.
3. English and draft Welsh text will be maintained in resource files. The
   local demonstration stores the selected language as a browser-local
   preference, with English as the default. Switching language retains the
   selected patient, URL/list state and unsaved form state. Missing Welsh text
   falls back to English. Draft Welsh remains clearly identified and requires
   professional review before production or clinical use; unavailable legacy
   clinical prose must not be invented or translated.
4. The extracted-reference, synthetic-data, resource, UI, mapping, persistence
   and unavailable-infrastructure adaptations documented in `review.md` are
   accepted for this bounded migration stage. This is evidence of parity with
   extracted legacy rules, not proof of the complete Windows, EF6 or Oracle
   system.
5. Access control, remote-record handling, patient search/switching, editing,
   deletion, production database migration and deployment remain outside this
   iteration's scope.

## Invalidation rule

Any change to a path listed in
`system-feel/characterise/review-files.sha256`, or to the source, approved
behaviour, decisions or scenarios, invalidates this approval. The changed
packet must be reverified, re-inventoried and approved as a new revision before
Convert continues.

This records the product owner's explicit decision in the project conversation
on 2026-10-14. It is separate from, and does not invoke,
`lmf/implementation/lmf approve`.
