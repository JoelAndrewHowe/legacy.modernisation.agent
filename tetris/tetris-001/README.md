# Terminal Tetris

Requires Node.js 18 or newer and an interactive terminal at least **52 columns × 24 rows**. No packages need to be installed.

```sh
npm start
```

The entire display occupies 24 rows, including the 10×20 board, score, controls, borders, and game-over message. If the terminal is too small, resize it to resume gameplay.

## Controls

| Key | Action |
| --- | --- |
| Left / Right or A / D | Move |
| Up or W / X | Rotate clockwise |
| Z | Rotate counterclockwise |
| Down or S | Soft drop |
| Space | Hard drop |
| P | Pause / resume |
| R | Restart |
| Q or Ctrl-C | Quit |

Complete rows to score points. Clearing 1, 2, 3, or 4 rows earns 100, 300, 500, or 800 points multiplied by the current level. Soft drops earn 1 point per row; hard drops earn 2. Every 10 cleared rows increases the level and falling speed. The game ends when a new piece cannot spawn.

Quitting restores the cursor, line wrapping, and previous terminal screen.

## Tests

```sh
npm test
```

Tests cover the engine and the 24-row display, including paused and game-over states. Interactive startup, controls, game over, restart, and terminal cleanup have also been smoke-tested through a 52×24 pseudo-terminal using `npm start`.
