# Running the LMF review lines with the tutorial factory

The target is `lmf/migrations/hcwp`. It owns the Characterise, Convert and
Refactor DOT lines and their machine configurations under `.assembly-lines/`.
The reusable factory engine remains in `factory/`. Each named run keeps its plan
and remembered settings in the ignored `factory/runs/` directory.

These lines are independent review loops. They do not automatically chain and
their validators do not replace LMF's executable gates. Run them in order, and
perform the human review between Characterise and Convert.

## 1. Characterise

From the repository root:

```sh
bin/factory --run hcwp-characterise \
  --target lmf/migrations/hcwp \
  --line characterise \
  --seed lmf/seeds/hcwp/characterise.md \
  --attempts 6
```

The first invocation remembers its target, line and seed. If it stops at the
attempt limit, inspect the reported findings and resume with:

```sh
bin/factory --run hcwp-characterise --attempts 6
```

## 2. Review and approve Characterise

Review the source references, behaviour, gaps, dependencies, fixtures, scenarios,
reference adaptations and actual verification output under `characterise/`.
Resolve blocking gaps before approval. Then calculate a review revision from the
files you actually reviewed and create `approvals/characterise-approved.md` by
hand. Record the revision, reviewed file list, verification command/results,
scope decisions, date and reviewer.

This manual record is a convention for these tutorial lines; it does not call
the separate `lmf/implementation/lmf approve` command or inherit its stronger
revision enforcement. Do not create it until the review has really occurred.

## 3. Convert

```sh
bin/factory --run hcwp-convert \
  --target lmf/migrations/hcwp \
  --line convert \
  --seed lmf/seeds/hcwp/convert.md \
  --attempts 6
```

Resume with `bin/factory --run hcwp-convert --attempts 6`.

## 4. Refactor

Start only after Convert's executable parity evidence is accepted:

```sh
bin/factory --run hcwp-refactor \
  --target lmf/migrations/hcwp \
  --line refactor \
  --seed lmf/seeds/hcwp/refactor.md \
  --attempts 6
```

Resume with `bin/factory --run hcwp-refactor --attempts 6`.

The final Refactor station is `nhsw-design-review`. It checks the rendered
Blazor UI against the official DHCW NHSW component library, including locally
vendored and traceable CSS, applicable component markup, accessibility and
browser evidence. The shared doer receives and addresses any findings.

All reviewers use Pi by default. Authenticate Pi before starting. Run one named
run at a time against this shared target. The factory commits completed product
tasks but excludes `.assembly-lines/` from those commits.

The existing `lmf/implementation/` CLI remains the stronger, purpose-built LMF
workflow with revision-bound approval and runner-owned verification. These DOT
lines let you exercise the tutorial factory design against the same vision; a
successful agent review result alone is not a parity or approval claim.
