# Work log

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
