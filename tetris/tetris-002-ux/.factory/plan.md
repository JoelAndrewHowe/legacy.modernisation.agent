# Task plan

- [ ] Provide a terminal Tetris application launched with `npm start`.
  - [x] Verify application-level readiness instructions, line-clear score updates, game-over feedback, and Enter-to-restart behavior.
  - [ ] Validator: resizing below 22×24 redraws the full frame and clips or wraps the board and quit instructions; show a resize prompt until sufficient space is restored.
    - [ ] Verify every positive undersized boundary fits its prompt, freezes gameplay, and restores the unchanged frame at 22×24.
    - [x] Verify minimizing active gameplay emits no frame content, freezes controls and gravity, and restores the unchanged 24-row frame at exactly 22×24 with timer cleanup on exit.
    - [x] Verify minimized terminals emit no visible content and still allow quitting with timer cleanup.
    - [x] Validator: a zero-column terminal emits a blank CRLF; suppress frame content when either terminal dimension is zero.
    - [x] Verify resizing while help is open preserves the paused game and help display on restoration.
    - [x] Verify resizing during active gameplay clears the board, pauses controls and gravity through partial restoration, and resumes the unchanged game only when both dimensions suffice.
    - [x] Handle an initially undersized terminal with the same bounded resize prompt; verify controls and gravity remain paused until it is restored.
  - [ ] Validator: the empty board and fixed score do not communicate readiness or next steps; add explicit status or instructions beyond quitting.
  - [ ] Validator: src/app.js displays only an empty board and fixed score and ignores non-quit controls; implement playable movement, scoring, and game-over feedback.
  - [ ] Validator: src/app.js labels the game 'Unfinished' without a useful next step; add readiness/start instructions and gameplay controls.
- [ ] Implement falling pieces, movement, rotation, collision detection, line clearing, scoring, and game over.
- [ ] Render the board, score, controls, borders, and game-over messages within 24 terminal rows.
- [ ] Verify startup, gameplay controls, scoring, game over, and the 24-row display limit.
