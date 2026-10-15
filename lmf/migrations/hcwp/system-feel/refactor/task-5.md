# Task 5 — English and draft Welsh

Task implemented without changing the plan checkbox. No validator findings were supplied in this request; `suppliedValidatorFindings` is an empty list in the task report. This is Refactor presentation work, not new legacy parity or professional translation approval.

## Reviewed prerequisites

Inspected the working tree before editing; unrelated factory/course changes were left alone. `check-prerequisites.py` passes current immutable input hashes and human approval binding. `evidence/task-5-preflight/results.json` verifies all 53 retained Convert observations and their current source identities, current immutable prerequisites, 40 approved baseline scenarios, 43 query checks, four fresh-context persistence checks and 34 applicable shared scenarios.

An initial attempt to run the Convert-stage verifier directly was rejected because that gate binds the pre-Refactor application snapshot. Its failed evidence was relocated out of Convert to `evidence/task-5-convert-preflight-rejected/`; no gate or approval was weakened or recreated. The existing Refactor prerequisite verifier is the correct gate for authorized mutable application boundaries. The rejected command is not passing parity evidence.

## Inventory and fallback contract

- `refactor/src/Presentation/interface-strings.cy.json` is the reviewable bilingual inventory: each key is the complete English fallback and its value is draft Welsh. All 192 entries require professional Welsh-language review, especially clinical field/lookup labels. No agent wording is approved for production.
- `RecordingFields`, `ResultDisplay` and `PatientBannerValues` continue to supply application-authored English labels/descriptions outside component markup. The inventory translates those labels at presentation time; persisted codes, rules and DTOs are unchanged.
- `InterfaceLanguage` centralizes English default, supported language selection, missing/blank-Welsh English fallback and parameterized ranges/accessibility labels. Razor has no translation dictionaries. Components subscribe to the scoped language service, then unsubscribe on disposal.
- `unresolved-resources.json` is an exact copy of the approved Characterise resource reconciliation: all 162 identities, including all 88 baseline identities, original-source references, hashes, unresolved status and owners. This intentionally includes excluded resources rather than silently dropping them. It is the unresolved-resource section of this translation review inventory. No original resource prose has been recovered, invented or translated. Resource identities and arguments remain the honest fallback in both languages.
- Independently authored UI labels such as School may share a name with an unresolved resource identity. Their Welsh wording translates the **new product label**, not the unavailable legacy resource. `CurrentStatusText` and `CodeDescriptionFormat` stay visible in explicit unavailable-description/format fallbacks.
- Patient names, addresses, organisations, alerts and history fixture descriptions are input data, not interface translations; they remain unchanged. Existing English-formatted dates and extracted age values are retained as source/display observations rather than reinterpreted clinical data.

## Retention and document language

The shared shell offers English/Cymraeg buttons with language tags and pressed state, plus a visible draft-review disclaimer. Switching calls the scoped service and a local JS helper, without navigation, URL replacement, recreating the recording model, saving or serializing the draft. Selected patient, list filter/page URL, pending form values and navigation remain intact.

`localStorage['hcwp.language']` stores **only** `en` or `cy`; it survives navigation, full-page GET filter submission and browser reload until cleared. No patient information or draft is written to browser storage. Unsupported stored values normalize to English. If browser storage is blocked, the preference remains circuit-only and reload falls back to English. Unsaved draft **reload** persistence is not claimed or required; ordinary local-demo circuit loss can lose the draft.

The local helper sets `document.documentElement.lang` before interactive startup and after each switch. Initial static HTML uses English fallback until the circuit reads the preference; active interactive copy and document language are tested together. No external language assets or services are requested.

## Responsive adaptation and findings addressed

Task execution found Welsh navigation overflow at 320px caused by the pinned library's `white-space:nowrap`. `wwwroot/interface.css` only permits translated navigation labels to wrap and flex items to shrink; it introduces no colours, typography, spacing or breakpoints and does not modify pinned assets. Chromium now checks English and Welsh at 320px and 1280px and retains screenshots. The header/service name remains full length rather than substituting an unexplained abbreviation.

The existing server-rendered patient-banner checks initially failed after language injection because their test service collection lacked the new service. Registered the real inventory-backed service there; no assertions were removed. An initial browser expected count of 15 recorded rows was incorrect: the immutable target-only volume fixture contains 18. Corrected that expectation to 18; no fixtures were changed. Failed attempts remain under `evidence/task-5-language/` and `evidence/task-5-regression/` for audit.

## Verification

Run from `lmf/migrations/hcwp` with a fresh evidence directory:

```sh
system-feel/refactor/verify-task-5 --evidence-dir system-feel/refactor/evidence/task-5-final
```

This executes all carried-forward task-4 checks, inventory-use/resource reconciliation checks, seven language unit checks, and six real Chromium language/retention flows, rejecting empty/failed/skipped results. It records source/evidence identities, commands, timestamps, runtime/browser versions and bilingual narrow/wide screenshots. Unit checks explicitly cover missing and blank Welsh fallback and unchanged unresolved resource identities. Browser checks cover language/document state, reload, list URL/filter/page retention, detail-return, unsaved fields across both switches and internal navigation, invalid-state translations and no external requests/runtime errors.

`evidence/task-5-regression-final/results.json` passed all carried-forward gates before the final task verifier. Final task results belong in `evidence/task-5-final/results.json`. The subsequent plan tasks still own expanded bilingual accessibility/contrast/keyboard coverage, the final slice verifier, format/style gate and final all-gates report. This document does not assert those tasks or iteration 002 are complete. Extracted-reference parity, synthetic input, local demonstration, EF in-memory and unverified Windows/Oracle/PostgreSQL/production limitations remain unchanged.
