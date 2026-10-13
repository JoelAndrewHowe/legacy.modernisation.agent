# Terminal Tetris

Run `npm start` with Node.js 18 or newer in an interactive terminal at least
60 columns wide and 24 rows tall. The complete display occupies 24 rows;
a smaller terminal pauses gameplay until resized. Redirected input/output
prints a single game snapshot and exits instead of starting interactive play.

- Left/Right: move
- Up: rotate clockwise
- Down: soft drop
- Space: hard drop
- R: new game (also after game over)
- Q or Ctrl-C: quit

Solid two-column blocks mark falling and settled pieces, with a distinct colour
for each tetromino. The header shows score, cleared lines, next piece, and
game-over status. Gravity speeds up every ten
cleared lines. Quitting restores the cursor, normal input mode, and original
terminal screen.

Run `npm test` for engine and terminal-adapter tests.
On POSIX systems with Python 3, run `python3 test/verify-terminal.py` for real
60x24 pseudo-terminal checks of `npm start`, gameplay, and exit cleanup.
