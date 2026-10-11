# Verification: startup, controls, line clearing, display height

Task remains unchecked in `.factory/plan.md`; completion belongs to the planner.
No validator findings were supplied in this request.

- `npm test`: 20 tests passed, zero failures.
- Added `test/terminal.test.js` coverage that sends the hard-drop key through the terminal handler, clears a prepared line, and verifies score 100, lines 10, level 2, remaining cells, and a 24-row redraw within 64 columns.
- Ran `npm start` in a real 64x24 pseudo-terminal, with colour enabled and with empty `NO_COLOR`. Both runs produced six game frames, each exactly 24 rows and at most 64 columns, with a visible quit hint.
- Sent actual left/right/up/down escape sequences and Space through the pseudo-terminal; each caused a redraw. Existing automated tests assert their gameplay effects, gravity, restart, and collision handling.
- Q exited both startup runs successfully (exit 0), emitted cursor/alternate-screen restoration, and restored the original terminal attributes.
- Existing tests also verify single through four-line clears, game-over display, resize warnings and paused gameplay, and readable colour-disabled output.

The initial pseudo-terminal probe incorrectly required restoration escapes to be the final process output. npm emits spinner cleanup afterward. The corrected probe checks restoration is present and terminal attributes are restored; it passed. No application defect was found.
