# Required input reading evidence

This run performed only the first unfinished plan task: read the required inputs before product work. The plan remains unchanged and unchecked; this note is not a Characterise gate result or human approval.

Repository HEAD at inspection: `ef4e5b631efd99661a0ee62cd6c131f5b8140fbf`.
Paths below are relative to the repository root. SHA-256 hashes identify the actual inputs read, independently of working-tree state.

| Input read in full | SHA-256 |
| --- | --- |
| `lmf/docs/vision.md` | `a5280da556de24f8d6d9254df5b1bdd22ace59c7fc0a5ac64b9485dd71483444` |
| `lmf/iterations/001-characterise-and-migrate-hcwp.md` | `73c53da335f85625dd0ce180d69eec64a21431f9ab8247a58520e0dfbd3addcd` |
| `example-code/HCWP Core (pseudonymised) - single file.txt` | `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2` |

The bundle was read through its final `<<< END FILE 94/94` banner, including all eight layers and both supplied test files. A truncated first read was followed by reading the omitted lines 995–1000. The seed and run plan were also read.

## Constraints retained for subsequent tasks

- Scope is selected synthetic patient, KD03 add and persistence read-back, including applicable recording validation/warnings and repeat recalculation. No Convert or Refactor code before the separate human gate.
- The bundle is not a buildable application. Future evidence can establish only parity with extracted legacy logic, not the original Windows/Oracle system or full save service.
- Preserve contradictions and quirks. In original file 27, `KdpExaminationValidator.ValidateHeadCircumference` rejects values >=100, while `ValidateOnSave` uses the exclusive 0–1000 range. `NoResults` omits `PhysicalGeneral` and `CoreComponent`; do not silently add them.
- Original file 6, `KdpExaminationResultDelegate`, identifies KD03 and exposes heart, hips, eyes, testes and general assessment. Its contact-specific visibility logic does not establish a gender restriction on testes. Missing control designer/binding definitions limit conclusions about Windows presentation.
- Original files 6 and 44 obtain recommended age limits from schedule data rather than enforce the contact name as a mandatory age window. Schedule rows, BMI options, centile data and operational lookup values will need explicitly labelled synthetic fixtures or limitations.
- Original file 43, `ExaminationsCrudManager.UpdateRepeatFlags`, filters patient and code prefix, groups by exact code and compares full examination dates; all entries tied at the earliest date are non-repeat. Keep the bounded accepted repeat scenario categories; do not expand speculative mutation coverage.
- Original file 44 saves examination/given/KDP rows and conditionally a measurement row, then recalculates repeats and invokes appointment-status/recall updates. The latter dependencies are excluded, not evidence of full save-service parity.
- Original files 92–93 provide reason-not-examined and location-type seeds. Original file 94 explicitly reconstructs schema and omits triggers; it is not authoritative live-database evidence.

## Validator findings

The user supplied no findings after “Record and address these validator findings:”. There are therefore no supplied validator defects to record or repair. This does not assert that validation has run or passed.

## Verification at this step

Read-only inspection and `sha256sum` completed. No executable harness exists yet, no scenarios were executed, and no parity or approval is claimed. Only this note was written, inside the target's `characterise/` directory. Later plan tasks remain pending.
