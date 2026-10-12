# Validation record

## Current doer pass

- No new validator findings were supplied in this request; previous findings remain recorded below.
- Worked on the next unchecked task (the gameplay engine), without marking it done or changing `.factory/plan.md`.
- Guarded `Game.lock()` after game over so it cannot mutate the board, score, or active piece once play ends.
- Added deterministic coverage for all four line-clear scores, board dimensions, locking on stacked blocks, and rejected rotations preserving state. Extended game-over immutability coverage to direct locking.
- Verification: `npm test` passes all 15 tests, including startup, gameplay, controls, cleanup, and physical display-height checks.

## Findings supplied

- `npm test` passed but verified only a static startup scaffold; gameplay, controls, cleanup, and game-over behavior were unimplemented and untested.
- `test/startup.test.js` bypassed `npm start`, so it could not detect a broken package start script.
- Display-height coverage included only startup, not gameplay or game-over displays with controls.
- Follow-up validator: all 10 tests passed, but height tests counted newline-separated rows, not physical terminal rows. The reported 48-column controls line wrapped at 40 columns, producing 25 rows. The seed specifies no minimum terminal width; startup, gameplay, and game-over coverage must account for wrapping.

## Work performed

- Replaced the scaffold with a playable Node.js terminal game launched by `npm start`, addressing the next unchecked setup task and the functional gaps identified by validation.
- Added seven pieces, movement, rotation with limited wall kicks, gravity, collision detection, locking, hard drop, line clearing, scoring, and blocked-spawn game over in `src/game.js`.
- Added keyboard controls, alternate-screen rendering, timer shutdown on game over, and terminal restoration on quit, Ctrl-C, SIGINT, SIGTERM, and input end in `src/index.js`.
- Non-TTY startup emits one complete game frame and exits; interactive TTY startup runs the game.
- Changed `test/startup.test.js` to execute `npm --silent start`, exercising the package start script without npm's banner.
- Added deterministic gameplay and interactive lifecycle tests in `test/game.test.js`, including complete 24-row startup, gameplay, and game-over frames containing controls.

## Verification

- `npm test`: all 12 tests pass after the width-aware changes.
- Real pseudo-terminal smoke check: `npm --silent start`, hard drop, quit, successful exit, and cursor/alternate-screen restoration passed.
- Game display uses 20 board rows, two borders, one score/game-over row, and one controls row when at least 12 columns are available. Removed the previous unsupported 48-column minimum-width assumption.
- `src/game.js` now accepts terminal width, uses compact controls/status and single-character board cells as needed, and bounds every line to that width. Below 12 columns, a bounded resize notice replaces the board; this keeps the display within the height limit even when a full board cannot fit.
- `src/index.js` passes the actual output width and redraws on resize, clearing stale content and removing the resize listener on cleanup.
- New tests count wrapped physical rows across widths 1–100 for startup, gameplay, and game over. Interactive coverage verifies width propagation at 40 columns and resizing to 12 and 1 columns, including game-over redraw and resize-listener cleanup.
- `.factory/plan.md` remains unchanged; no task was marked done.
