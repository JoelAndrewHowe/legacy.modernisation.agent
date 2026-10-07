# Terminal Tetris plan

- [x] Create the Node.js project and game engine with piece movement, rotation, collision detection, line clearing, scoring, and game-over detection; add engine tests. (`npm test`: 13 tests passed.)
- [x] Implement the interactive terminal interface and `npm start`, keeping the entire display within 24 rows with board, score, controls, borders, and game-over messages. (`src/terminal.js`; movement, rotation, drops, pause/restart/quit, gravity, terminal cleanup, and size guard; `npm test`: 16 tests passed.)
- [x] Verify tests and terminal gameplay, fix any issues, and document controls and startup instructions. (`npm test`: 16 tests passed; `npm start` passed a 52×24 pseudo-terminal smoke test for movement/rotation/drops, pause/resume, game over, restart, quit, and terminal cleanup; no issues found; startup, controls, scoring, and tests documented in `README.md`.)
