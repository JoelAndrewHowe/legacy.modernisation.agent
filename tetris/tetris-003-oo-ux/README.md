# Terminal Tetris

Run `npm start` with Node.js 18 or newer in a terminal at least 22 columns
wide and 24 rows tall. No dependencies are required.

- Left / Right: move
- Up: rotate clockwise (with small wall kicks)
- Down: fall one step
- Space: drop and lock
- Q / Ctrl-C: quit, including after game over

Pieces fall every half second. Clearing 1, 2, 3, or 4 lines awards 100, 300,
500, or 800 points. A blocked spawn ends the game and shows the final score.
The board, borders, score, controls, and game-over message occupy 24 rows.
Raw mode and the cursor/alternate screen are restored on quit or termination
signals. Redirected startup prints one plain-text preview and exits.

Run `npm test` for gameplay, display, startup, controls, gravity, and cleanup
checks.
