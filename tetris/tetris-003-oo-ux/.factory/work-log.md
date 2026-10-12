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

## Follow-up: gameplay mechanics regression checks

Continued the next unfinished task: movement, rotation, falling, collision,
line clearing, scoring, and game over. These mechanics already exist in
`src/game.js`; added regression coverage in `test/game.test.js`.

- Verified cumulative scoring over three separate double-line clears, with an
  empty board and playable fresh piece after each clear.
- Verified soft dropping onto a stack locks without overwriting existing cells,
  and hard dropping locks exactly one piece while leaving its successor at spawn.
- Validator findings supplied with this request: none; nothing to address.

Validation: `npm test` passes all 30 tests. Left `.factory/plan.md` unchanged;
no task was marked done.

## Follow-up: complete 24-row display layout

Worked on the next unfinished task: render the board, score, controls, borders,
and game-over messages within 24 terminal rows. The existing renderer already
implements the layout, so added focused regressions in `test/renderer.test.js`.

- Checked both borders, all 20 board rows, exact cell positions at opposite
  corners and in the active piece, and the controls row within a 24-row frame.
- Checked that game over preserves settled cells, hides the active piece, and
  replaces the title and controls without adding rows.
- Checked all seven pieces in all four rotations for 24-row/22-column bounds
  and four visible cells.
- Validator findings supplied with this request: none; nothing to address.

Validation: `npm test` passes all 32 tests. Left `.factory/plan.md` unchanged;
no task was marked done.

## Follow-up: startup, controls, and display verification

Worked on the next unfinished task: verify startup, gameplay controls, and
24-row display height, including game over.

- Added a regression in `test/startup.test.js` using actual arrow-key escape
  sequences and Space/Q bytes through Node's keypress decoder, rather than
  synthesized keypress events. Verified movement, soft drop, blocked-spawn
  game over, frozen gameplay afterward, stopped gravity, and quit cleanup.
- Checked every rendered frame for exactly 24 rows, at most 22 columns, and
  both board borders; checked final game-over score and quit help.
- Ran `npm start` in a real 24-by-80 pseudo-terminal, sent all arrow controls
  and repeated hard drops, reached game over, and quit successfully. All 47
  captured game frames stayed within 24 rows; cursor/screen restoration was
  emitted and the process exited successfully.
- Validator findings supplied with this request: none; nothing to address.

Validation: `npm test` passes all 33 tests. No application changes were needed.
Left `.factory/plan.md` unchanged; no task was marked done.

## Follow-up: raw Up-arrow rotation verification

Continued the next unfinished task: verify startup, gameplay controls, and
24-row display height, including game over.

### Finding recorded and addressed

- **`test/startup.test.js`: Raw Up-arrow decoding is not verified: the O piece
  is rotation-invariant and no rotation assertion follows the input. Use an
  asymmetric piece and assert its shape changes.** Changed the raw-byte test
  to spawn a T piece first, followed by O pieces for the game-over stack.
  Immediately after sending the Up-arrow escape sequence, assert that the
  shape changes and equals the expected clockwise-rotated T. Movement checks
  now use the initial spawn position rather than O-specific coordinates.
  Retained raw controls, game-over, frame-height, and cleanup checks.

Validation: `npm test` passes all 33 tests. Left `.factory/plan.md` unchanged;
no task was marked done.

