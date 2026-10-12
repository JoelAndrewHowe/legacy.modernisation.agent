# Work log

## Gravity-timer validator follow-up

- Recorded medium-severity validator finding at `test/start.test.js:199`: timer tests could not detect gravity remaining fixed as levels increased; hardcoding `src/terminal-game.js:94` to 1000 ms passed all 28 tests. Recommendation: deterministic higher-level and level-transition fixtures with literal expected delays at startup and after rescheduling.
- Addressed it within the next unchecked keyboard-controls/rendering task: replaced the getter-derived timer expectation with literal 1000 ms and added deterministic startup fixtures at 0, 10, 40, 90, and 150 lines, asserting 1000, 900, 600, 100, and 100 ms respectively at startup and after repeated callbacks. Checks also require exactly one pending timer, removal of the fired timer, and cleanup on stop.
- Added a one-line-clear fixture at nine lines for gravity, Down, and Space. Each crosses to ten lines and asserts literal 900 ms on rescheduling and the following callback; keyboard actions can retain the already pending timeout until it fires.
- Validation: `npm test` passed all 30 tests. Temporary-copy mutations fixing gravity to 1000 ms failed both new tests; caching the startup interval failed the level-transition test. No production changes were needed.
- Left `.factory/plan.md` unchanged; no task was marked done.

## Header-value validator follow-up

- Recorded medium-severity validator finding in `test/start.test.js`: header assertions did not detect stale score, lines, or next-piece values; hardcoding `Score:0 Lines:0 Next:T` passed all 26 tests.
- Addressed it within the next unchecked keyboard-controls/rendering task: added deterministic fixtures and literal expected headers independent of renderer output and game-state getters. Checked direct frames and freshly emitted 24-row frames at startup, soft drop, gravity, two-line clearing via hard drop, and restart. A separate blocked-spawn fixture checks nonzero game-over counters and a known preview.
- Validation: `npm test` passed all 28 tests. Separate temporary-copy mutations hardcoding score to 0, lines to 0, and preview to T each failed the new independent header regression. No production changes were needed.
- Left `.factory/plan.md` unchanged; no task was marked done.

## Settled-block rendering validator follow-up

- Recorded validator finding: `test/start.test.js` did not detect missing or misplaced settled blocks because its redraw oracle reused `renderFrame`. Recommendation: render a deterministic board fixture and independently assert occupied and empty cell positions, including settled blocks after hard drop.
- Addressed it within the next unchecked keyboard-controls/rendering task: added a deterministic board with scattered settled blocks and an O piece, plus a coordinate-based oracle that checks all 200 cells and board borders independently of renderer and piece-cell helpers.
- Checked both direct frames and actual terminal output before and after Space: existing blocks stay in place, the O locks at exact bottom coordinates, its old cells become empty, and the next T appears at exact spawn coordinates. Post-drop output must be a freshly emitted frame.
- Validation: `npm test` passed all 26 tests. Temporary-copy mutations omitting settled blocks, shifting them one column, and omitting them only after hard drop each failed on the independent cell assertion. No production changes were needed.
- Left `.factory/plan.md` unchanged; no task was marked done.

## Fresh-frame validator follow-up

- Recorded validator finding: `test/start.test.js` keyboard and gravity tests did not detect missing redraws. Recommendation: assert newly emitted frames reflect state changes after input, gravity, and restart.
- Addressed it within the next unchecked keyboard-controls/rendering task: added an assertion helper that captures only output emitted by each action, requires a visible state change, and compares the fresh frame to the current rendered game state (including cursor positioning, screen clearing, and terminal line endings).
- Applied checks to Left, Right, decoded Up, Down, Space, gravity, and restart; game-over restart also verifies that the fresh display no longer contains GAME OVER.
- Validation: `npm test` passed all 25 tests. Separate temporary-copy mutations suppressing input, gravity, and restart redraws each failed on the fresh-frame assertion. No production changes were needed.
- Left `.factory/plan.md` unchanged; no task was marked done.

## Keyboard rotation validator follow-up

- Recorded validator finding: `test/start.test.js` sent Up without asserting rotation; random O pieces could hide ineffective rotation, and removing the adapter's Up handler still passed.
- Addressed the finding within the next unchecked keyboard-controls/rendering task: injected a deterministic T-piece source into the keyboard-actions test, sent the real Up escape sequence through readline, and asserted that orientation changes to the expected clockwise shape while position stays unchanged.
- Validation: `npm test` passed all 25 tests. In a temporary copy, removing the adapter's Up handler caused the keyboard-actions regression to fail on the orientation assertion.
- Left `.factory/plan.md` unchanged; no task was marked done.

## Keyboard controls and bounded terminal rendering

- Implemented the next unchecked task in `src/terminal-game.js`: raw-mode arrow-key movement/rotation/drop, Space hard drop, R restart, Q/Ctrl-C exit, and scheduled gravity using the existing engine.
- Added a complete 24-row renderer: header (score, lines, next piece or game-over instructions), twenty board rows, two borders, and one controls row. Interactive output has no trailing newline; terminals smaller than 60x24 show a bounded resize prompt and pause play.
- Added alternate-screen/cursor management and cleanup for quit and termination signals. Redirected invocations print one snapshot and exit. Documented usage and controls in `README.md`.
- Replaced scaffold checks with terminal-adapter tests for frame bounds, actual escape-sequence decoding, keyboard actions, gravity, restart, resize, and resource restoration.
- Validator findings: none were supplied in this request; there were no findings to address.
- Validation: `npm test` passed all 25 tests; `npm start` successfully printed the 24-row snapshot with redirected input/output. Interactive behavior was exercised with simulated terminal streams, not a manual live-terminal session; the separate verification task remains unchecked.
- Left `.factory/plan.md` unchanged; no task was marked done.

## PieceBag encapsulation validator follow-up

- Recorded validator finding: `src/tetris.js:55–68` exposed writable `bag` and `random` fields, permitting `bag.bag.push('invalid')` to corrupt consumption and future spawns when a caller retained an injected bag.
- Addressed the finding within the next unchecked gameplay task: moved contents and random source into private fields; froze the public instance to prevent field additions and replacement of `next()`. Consumption remains available only through `next()`.
- Added regressions for the reported push, field replacement, method replacement, three seven-bag refills, and future game spawns with a retained injected bag.
- Validation: `npm test` passed all 20 tests.
- Left `.factory/plan.md` unchanged; no task was marked done.

## Gameplay encapsulation validator follow-up

- Recorded validator finding: `src/tetris.js:59–61,94–99` exposed writable board rows and active-piece/line state; tests at `test/tetris.test.js:95–100,109–115` relied on direct mutation and bypassed gameplay invariants.
- Addressed it within the next unchecked gameplay task: Board stores rows privately and provides frozen inspection snapshots; Piece coordinates and shape are immutable. TetrisGame privately owns a copied board, active piece, counters, preview, and game-over state, exposing only read-only inspection and gameplay actions. Spawn, descend, and lock transitions are private.
- Added validated constructor fixtures (`Board(width, height, rows)` and `TetrisGame({ initialState: { active, lines, score } })`), checking dimensions, cell types, legal tetromino rotations, integer coordinates, collision-free active placement, and nonnegative integer counters.
- Reworked gameplay tests to build fixtures before construction and trigger locking through gravity rather than writing internals. Added regression checks for rejected mutations, fixture isolation, and invalid initial states.
- Validation: `npm test` passed all 18 tests. Terminal controls/rendering remain outside this task; `.factory/plan.md` is unchanged and no task was marked done.

## Node.js terminal project setup

- Implemented the next unchecked task only: set up an ES-module Node.js project with an `npm start` entry point and a `TerminalGame` scaffold.
- Added startup tests using the built-in Node.js test runner; no external packages are required.
- Validation: `npm test` passed (2 tests); `npm start` exited successfully and printed a two-row scaffold message.
- Validator findings: none were supplied in the request, so there were no findings to address.
- Gameplay, interactive controls, and terminal lifecycle verification remain for subsequent tasks.
- Left `.factory/plan.md` unchanged; no task was marked done.

## Gameplay engine

- Implemented the next unchecked task in `src/tetris.js`: `Piece`, `PieceBag`, `Board`, and `TetrisGame` encapsulate seven tetrominoes, shuffled seven-bag generation, horizontal movement, clockwise/counterclockwise rotation with simple horizontal wall kicks, collision, gravity ticks, soft/hard drops, locking, line clearing, scoring, levels, and game over.
- Line awards are 100/300/500/800 times the current level; soft/hard drops award 1/2 points per row. Every ten lines increases the level and reduces the gravity interval, down to 100 ms.
- Added `test/tetris.test.js` covering pieces, rotations, wall kicks, rejected actions, gravity, drop scores, all line awards, row collapse, level progression, blocked spawn, and top-out.
- Validation: `npm test` passed all 16 tests, including the existing startup checks.
- Validator findings: none were supplied in this request; there were no findings to address.
- Terminal input, rendering, and timer integration remain for the next task. The engine owns no terminal resources or timers; the current entry point remains a scaffold.
- Left `.factory/plan.md` unchanged; no task was marked done.
