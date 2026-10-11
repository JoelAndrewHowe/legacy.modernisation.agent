# Terminal Tetris

Requires Node.js 20 or newer. No dependencies are needed.

Run in an interactive terminal:

```sh
npm start
```

- Left/Right: move; Up: rotate; Down: soft drop; Space: hard drop.
- Clear lines to score; every ten lines increases the level and falling speed.
- A blocked spawn ends the game. Press R to restart at game over.
- Q, Escape, or Ctrl+C quits and restores the terminal.

The complete game uses 24 rows and requires at least 64 columns. Smaller
terminals show a resize warning and pause gameplay until the terminal fits.

Bright colours on a black background distinguish pieces, board, status,
controls and game-over feedback. Piece letters and explicit text convey the
same information without colour. Set `NO_COLOR` (even to an empty value) to
disable colours, for example `NO_COLOR=1 npm start`.

Run rendering, gameplay, controls, resize and terminal-lifecycle checks with
`npm test`.
