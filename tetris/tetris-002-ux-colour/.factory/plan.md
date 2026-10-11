# Plan

- [x] Set up a terminal Tetris application launched with `npm start`.
  - [x] Address validator: `src/terminal.js` has terminal-management escapes but no accessible colour scheme for board, pieces, status, controls, or game-over feedback.
  - [x] Address validator: respect `NO_COLOR` and test both colour rendering and readable colour-disabled output; retain readable title, borders, score, and quit hint.
  - [x] Address validator: replace the empty static board with pieces, gameplay controls, progression feedback, and game-over messaging; remove README's gameplay deferral so the UX can be validated.
  - [x] Address validator: check terminal dimensions and show a small-terminal warning so the fixed 24-row display does not obscure controls.
  - [x] Address validator: expand the three starter-only tests to cover required colour and gameplay UX, beyond layout, restoration, and non-interactive rejection.
- [ ] Implement falling tetrominoes, movement, rotation, collision detection, line clearing, scoring, and game over.
- [ ] Render the board, score, controls, borders, and game-over messages within 24 terminal rows.
- [ ] Verify startup, gameplay controls, line clearing, and display height.
