import { emitKeypressEvents } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { Game } from './game.js';

// 24 rows total: status, top border, 20 board rows, bottom border, footer.
export function renderFrame(game, { paused = false } = {}) {
  const cells = game.board.map(row => [...row]);
  if (!game.gameOver) {
    const { matrix, x, y, type } = game.active;
    matrix.forEach((row, dy) => row.forEach((cell, dx) => {
      if (cell && cells[y + dy]?.[x + dx] !== undefined) cells[y + dy][x + dx] = type;
    }));
  }
  const help = [
    'CONTROLS',
    'Left/Right or A/D: move',
    'Up or W/X: rotate',
    'Z: rotate counterclockwise',
    'Down or S: soft drop',
    'Space: hard drop',
    'P: pause/resume',
    'R: restart',
    'Q or Ctrl-C: quit',
  ];
  const border = `+${'-'.repeat(game.width * 2)}+`;
  return [
    `TETRIS  Score: ${game.score}  Lines: ${game.lines}  Level: ${game.level}`,
    border,
    ...cells.map((row, i) => `|${row.map(cell => cell ? '[]' : '  ').join('')}|${help[i] ? `  ${help[i]}` : ''}`),
    border,
    game.gameOver ? 'GAME OVER - R: restart / Q: quit' : paused ? 'PAUSED - P: resume / Q: quit' : 'Stack blocks; complete rows to score.',
  ].join('\n');
}

export function startTerminal({ input = process.stdin, output = process.stdout } = {}) {
  if (!input.isTTY || !output.isTTY || typeof input.setRawMode !== 'function') {
    output.write('Tetris requires an interactive terminal. Run npm start in a terminal.\n');
    return false;
  }

  let game = new Game();
  let paused = false;
  let stopped = false;
  let lastDrop = Date.now();
  let timer;
  const wasRaw = Boolean(input.isRaw);
  const fits = () => (output.rows ?? 24) >= 24 && (output.columns ?? 52) >= 52;
  const draw = () => {
    const frame = fits() ? renderFrame(game, { paused }) : 'Resize terminal to 52x24. Q: quit';
    // Disable wrapping and omit a final newline so row 24 never scrolls.
    output.write(`\x1b[H${frame.replaceAll('\n', '\r\n')}\x1b[J`);
  };
  const stop = () => {
    if (stopped) return;
    stopped = true;
    clearInterval(timer);
    input.off('keypress', onKey);
    output.off('resize', onResize);
    process.off('SIGINT', stop);
    process.off('SIGTERM', stop);
    process.off('exit', stop);
    input.setRawMode(wasRaw);
    input.pause();
    output.write('\x1b[?7h\x1b[?25h\x1b[?1049l');
  };
  const onKey = (text, key = {}) => {
    const name = key.name ?? text?.toLowerCase();
    if (name === 'q' || (key.ctrl && name === 'c')) return stop();
    if (name === 'r') {
      game = new Game();
      paused = false;
      lastDrop = Date.now();
    } else if (name === 'p' && !game.gameOver) {
      paused = !paused;
      lastDrop = Date.now();
    } else if (!paused && !game.gameOver && fits()) {
      switch (name) {
        case 'left': case 'a': game.move(-1); break;
        case 'right': case 'd': game.move(1); break;
        case 'up': case 'w': case 'x': game.rotate(); break;
        case 'z': game.rotate(-1); break;
        case 'down': case 's': game.softDrop(); lastDrop = Date.now(); break;
        case 'space': game.hardDrop(); lastDrop = Date.now(); break;
      }
    }
    draw();
  };
  const onResize = () => {
    lastDrop = Date.now();
    output.write('\x1b[2J');
    draw();
  };

  emitKeypressEvents(input);
  input.setRawMode(true);
  input.resume();
  input.on('keypress', onKey);
  output.on('resize', onResize);
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
  process.on('exit', stop);
  output.write('\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[2J');
  draw();
  timer = setInterval(() => {
    if (paused || game.gameOver || !fits()) {
      lastDrop = Date.now();
      return;
    }
    if (Date.now() - lastDrop >= game.dropInterval) {
      game.tick();
      lastDrop = Date.now();
      draw();
    }
  }, 30);
  return stop;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!startTerminal()) process.exitCode = 1;
}
