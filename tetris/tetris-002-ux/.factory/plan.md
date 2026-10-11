# Task plan

- [ ] Provide a terminal Tetris application launched with `npm start`.
  - [ ] Validator: resizing below 22×24 redraws the full frame and clips or wraps the board and quit instructions; show a resize prompt until sufficient space is restored.
    - [ ] Verify resizing during active gameplay clears the board, pauses controls and gravity through partial restoration, and resumes the unchanged game only when both dimensions suffice.
    - [x] Handle an initially undersized terminal with the same bounded resize prompt; verify controls and gravity remain paused until it is restored.
  - [ ] Validator: the empty board and fixed score do not communicate readiness or next steps; add explicit status or instructions beyond quitting.
  - [ ] Validator: src/app.js displays only an empty board and fixed score and ignores non-quit controls; implement playable movement, scoring, and game-over feedback.
  - [ ] Validator: src/app.js labels the game 'Unfinished' without a useful next step; add readiness/start instructions and gameplay controls.
- [ ] Implement falling pieces, movement, rotation, collision detection, line clearing, scoring, and game over.
- [ ] Render the board, score, controls, borders, and game-over messages within 24 terminal rows.
- [ ] Verify startup, gameplay controls, scoring, game over, and the 24-row display limit.
