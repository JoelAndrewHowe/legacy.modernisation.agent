# Work log

## First unfinished task: terminal-game setup

- Added a dependency-free Node.js application launched with `npm start`.
- Separated game state/rendering from terminal input and lifecycle handling.
- Added the initial board and piece preview, score, and quit controls in 24 rows.
- Added raw-input handling, alternate-screen rendering, and terminal restoration
  on Q, Ctrl-C, SIGINT, or SIGTERM. Redirected startup prints a preview and exits.
- Documented usage and the mechanics deferred to the next task in `README.md`.
- Validation: `npm test` passed all 3 tests (display, npm startup, terminal cleanup).
- Validator findings supplied with the request: none. No findings to address.
- Left `.factory/plan.md` unchanged; no task marked done.

## Follow-up: playable startup and validator findings

The first unchecked plan task remains terminal-game setup; it was not marked
complete. Expanded the startup scaffold into a playable game to address the
validator's outstanding checks without changing `.factory/plan.md`.

### Findings recorded and addressed

- **Only the three startup tests passed; movement, rotation, falling,
  collision, line clearing, scoring, and game over were unimplemented and
  untested.** Implemented all seven pieces, movement and wall-kicked rotation,
  half-second gravity, soft/hard drops, collision and locking, line compaction,
  cumulative scoring, blocked-spawn game over, and terminal input/redraws.
  Added mechanics and input tests, including all four line-clear scores,
  blocked rotations, stack collisions, frozen game-over state, and gravity.
  Startup and game-over displays are checked at 24 rows and at most 22 columns.
  Compact controls and large-score formatting prevent display wrapping.
- **Cleanup tested only Q with initially disabled raw mode.** Added all eight
  combinations of Q, Ctrl-C, SIGINT, and SIGTERM with raw mode initially on or
  off. Tests verify raw-mode restoration, input pause, handler removal,
  timer cancellation, cursor/screen restoration, and idempotent cleanup.

Updated `README.md` with gameplay controls, scoring, and test coverage.
Validation: `npm test` passes all 22 tests. No plan checkbox was changed.

## Follow-up: state encapsulation and presentation separation

Continued the first unfinished task, terminal-game setup. Left
`.factory/plan.md` unchanged and did not mark any task done.

### Findings recorded and addressed

- **`src/game.js`: Game exposes mutable board, piece, score, and gameOver
  state; tests directly modify them. Callers can bypass collision, scoring,
  and game-over invariants instead of using controlled game operations.**
  Moved all domain state to JavaScript private fields. Read-only accessors
  return detached copies for nested state, and `snapshot()` supplies a detached
  display view. Spawn, collision checks, and cell enumeration are private;
  gameplay changes go through movement, rotation, ticking, and dropping.
  Movement accepts only single-column steps to prevent jumping through stacks.
  Replaced board/score injection and public spawning in gameplay tests with
  seeded piece selection and real moves/drops. Added mutation-isolation,
  read-only-property, private-operation, and invalid-movement regressions.
- **`src/game.js:render`: Game owns both gameplay rules and terminal
  presentation, including borders, control labels, and score formatting.
  Terminal.draw delegates layout back to the domain object, coupling game
  behavior to this particular terminal display.**
  Removed `Game.render`; `src/renderer.js` now owns terminal layout and consumes
  snapshots. Both interactive drawing and redirected startup use that renderer.
  Added separate presentation tests for real game over, large-score formatting,
  24-row/22-column bounds, and non-mutating rendering.

Validation: `npm test` passes all 25 tests, including npm startup, gameplay,
gravity, terminal input/cleanup, encapsulation, and display checks.

## Follow-up: startup lifecycle regression checks

Continued the first unchecked task: terminal-game setup launched with
`npm start`. The application already implements that task, so added targeted
regression coverage in `test/startup.test.js` rather than replacing it.

- Verify repeated interactive startup creates no duplicate timer, input handler,
  signal handlers, or screen output.
- Verify startup with either stdin or stdout redirected prints a plain-text
  preview without enabling raw mode, starting timers, or registering handlers.
- Verify stopping after redirected startup leaves the preview unchanged.
- Validator findings supplied with this request: none; nothing to address.

Validation: `npm test` passes all 28 tests. Left `.factory/plan.md` unchanged;
no task was marked done.

