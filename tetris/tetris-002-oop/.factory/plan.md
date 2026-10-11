# Plan

- [x] Set up a terminal Tetris application launched with `npm start`.
- [x] Implement pieces, movement, rotation, gravity, collision detection, line clearing, scoring, and game over.
  - [x] Protect invariant-bearing state with immutable pieces, private board/game state, read-only snapshots, and validated constructor fixtures. Planner confirmed implementation and mutation/aliasing regression tests.
  - [x] Correct four line-clear assertions to check the actual shifted row and empty bottom row. Planner confirmed; `npm test` passes all 20 tests.
- [x] Add keyboard controls and render the board, score, controls, borders, and game-over messages within 24 terminal rows. Connect `TetrisGame` to `TetrisApplication`, schedule gravity, render active/locked pieces, and stop timers on exit or game over. Validated work committed in `84d2e68`.
- [ ] Verify gameplay, startup, terminal cleanup, and the 24-row display limit.
