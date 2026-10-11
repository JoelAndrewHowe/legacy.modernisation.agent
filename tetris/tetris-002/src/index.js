import { emitKeypressEvents } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { Game } from './game.js';

export function renderGame(game) {
  const { board, score, lines, level, gameOver } = game.snapshot();
  return [
    `Tetris | Score: ${score} | Lines: ${lines} | Level: ${level}`,
    '+--------------------+',
    ...board.map(row => `|${row.map(cell => cell ? '[]' : '  ').join('')}|`),
    '+--------------------+',
    gameOver ? 'GAME OVER | R: restart | Q / Ctrl+C: quit'
      : '←→: move  ↑/X/Z: rotate  ↓: drop  Space: slam  Q: quit',
  ].join('\n');
}

export function renderStartup() {
  return renderGame(new Game());
}

export function start({
  input = process.stdin,
  output = process.stdout,
  game = new Game(),
  schedule = setTimeout,
  cancel = clearTimeout,
} = {}) {
  if (!input.isTTY || !output.isTTY) {
    output.write('Tetris requires an interactive terminal. Run npm start in a terminal.\n');
    return false;
  }

  const wasRaw = Boolean(input.isRaw);
  let stopped = false;
  let timer;
  const draw = () => {
    const rows = output.rows || 24;
    const columns = output.columns || 80;
    const display = rows < 24 || columns < 22
      ? 'Resize terminal to at least 22x24. Q: quit'
      : renderGame(game);
    // Clip to the terminal width so no line wraps into a 25th row.
    output.write(`\x1b[H\x1b[2J${display.split('\n')
      .map(line => Array.from(line).slice(0, columns).join('')).join('\r\n')}`);
  };
  const armTimer = () => {
    cancel(timer);
    if (stopped || game.gameOver) return;
    timer = schedule(() => {
      game.tick();
      draw();
      armTimer();
    }, game.dropInterval);
  };
  const stop = () => {
    if (stopped) return;
    stopped = true;
    cancel(timer);
    input.off('keypress', onKey);
    output.off?.('resize', draw);
    process.off('SIGINT', stop);
    process.off('SIGTERM', stop);
    process.off('exit', stop);
    input.setRawMode(wasRaw);
    input.pause();
    output.write('\x1b[?25h\x1b[?1049l');
  };
  const onKey = (text, key) => {
    const name = key?.name || text?.toLowerCase();
    if (name === 'q' || (key?.ctrl && name === 'c')) return stop();
    const restarting = game.gameOver;
    if (restarting) {
      if (name !== 'r') return;
      game = new Game();
    } else {
      switch (name) {
        case 'left': game.move(-1); break;
        case 'right': game.move(1); break;
        case 'up':
        case 'x': game.rotate(); break;
        case 'z': game.rotate(-1); break;
        case 'down': game.softDrop(); break;
        case 'space':
        case ' ': game.hardDrop(); break;
        default: return;
      }
    }
    draw();
    if (game.gameOver) cancel(timer);
    else if (restarting) armTimer();
  };

  emitKeypressEvents(input);
  input.setRawMode(true);
  input.resume();
  input.on('keypress', onKey);
  output.on?.('resize', draw);
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
  process.on('exit', stop);
  output.write('\x1b[?1049h\x1b[?25l');
  draw();
  armTimer();
  return stop;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (start() === false) process.exitCode = 1;
}
