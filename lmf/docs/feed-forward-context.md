# Adding feed-forward context to an LMF implementation stage

The factory's stage seed is the input to the shared planner and doer. Put durable
external guidance in a small context pack, then make the applicable seed require
the agent to read it before implementation. This keeps context stage-specific:
for example, UI design-system guidance belongs in Refactor and should not distort
a literal Convert task.

## Add a context pack

1. Select the authoritative source and an immutable tag or commit. Do not base a
   repeatable implementation on a moving branch alone.
2. Read the source's agent guidance, design rules, component/API registry,
   licence and the exact components or APIs relevant to the slice.
3. Add `lmf/seeds/context/<name>.md`. Keep it bounded and operational: record
   provenance, implementation rules, relevant mappings, explicit exclusions,
   asset/dependency policy and evidence the doer must produce.
4. Add a **Feed-forward context** section to the applicable stage seed. Require
   the planner and doer to read the pack, and state when it applies. Resolve the
   path from the seed so it remains unambiguous when the agent works in a target
   directory.
5. Do this before starting the named run. The run remembers the seed path, and
   the seed points the implementation agent at the context pack.

For example, from a seed in `lmf/seeds/example/refactor.md`:

```md
## Feed-forward context

Before planning or changing user-facing code, read
`../context/example-design-system.md` (resolved relative to this seed). Apply it
only to UI work, and record any necessary framework adaptation.
```

## What belongs in the pack

A useful pack answers the questions an implementation agent otherwise has to
rediscover:

- Which source revision was reviewed, and which files are authoritative?
- Which existing components or APIs map to this migration slice?
- Which semantics, accessibility relationships and behavioural scripts must be
  preserved when translating between frameworks?
- What must not be copied, invented or inferred?
- How are binaries, CSS, scripts, licences, provenance and checksums managed?
- Which application-level checks prove the integration rather than merely the
  upstream library?

Summarise rules; do not paste an entire upstream repository into the prompt.
Keep vendored runtime assets separate from guidance. Pin and verify both, but do
not let refreshing a summary silently upgrade a dependency.

## Refresh it later

Resolve the new upstream tag or commit, diff the previously reviewed guidance
and relevant source, then update the pack's revision and review date. Record only
material changes. If the consumed asset changes, update its provenance and
checksum separately and rerun the real integration checks.
