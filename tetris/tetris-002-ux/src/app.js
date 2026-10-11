import { emitKeypressEvents } from 'node:readline';
import { Game } from './game.js';

export function renderFrame(game = new Game(), help = false) {
  const board = game.cells().map(row => '|' + row.map(cell => cell === 2 ? '[]' : cell ? '##' : '  ').join('') + '|');
  const instructions = [
    game.status === 'over' ? 'GAME OVER' : game.status === 'ready' ? 'READY' : 'PAUSED: HELP',
    game.status === 'over' ? 'Enter: restart' : game.status === 'ready' ? 'Enter: start' : '?: resume',
    'Left/Right: move',
    'Up: rotate',
    'Down: soft drop',
    'Space: hard drop',
    '?: help / pause',
    'Q/Esc: quit',
    `Lines: ${game.lines}`,
  ];
  if (game.status !== 'playing' || help) {
    instructions.forEach((text, i) => { board[i + 4] = '|' + text.padEnd(20) + '|'; });
  }
  return [
    `TETRIS | Score: ${game.score}`.slice(0, 22),
    '+--------------------+',
    ...board,
    '+--------------------+',
    '?:help Q/Esc:quit',
  ].join('\r\n');
}

export function startApp({ input = process.stdin, output = process.stdout, signals = process,
  game = new Game(), setInterval: schedule = globalThis.setInterval,
  clearInterval: cancel = globalThis.clearInterval } = {}) {
  if (!input.isTTY || !output.isTTY) {
    throw new Error('Tetris requires an interactive terminal. Run npm start in a terminal.');
  }

  const wasRaw = Boolean(input.isRaw);
  let stopped = false;
  let help = false;
  let timer;
  const tooSmall = () => output.rows < 24 || output.columns < 22;
  const draw = () => {
    const small = tooSmall();
    const frame = output.columns <= 0 || output.rows <= 0 ? '' : small
      ? ['Resize to 22x24', 'Q/Esc: quit']
        .slice(0, Math.max(0, output.rows))
        .map((line) => line.slice(0, Math.max(0, output.columns)))
        .join('\r\n')
      : renderFrame(game, help);
    output.write('\x1b[H\x1b[2J' + frame);
  };
  const stop = () => {
    if (stopped) return;
    stopped = true;
    cancel(timer);
    input.removeListener('keypress', onKey);
    output.removeListener('resize', draw);
    signals.removeListener('SIGINT', stop);
    signals.removeListener('SIGTERM', stop);
    input.setRawMode(wasRaw);
    input.pause();
    output.write('\x1b[?25h\x1b[?1049l');
  };
  const onKey = (_text, key = {}) => {
    if (key.name === 'q' || key.name === 'escape' || (key.ctrl && key.name === 'c')) {
      stop();
      return;
    }
    if (tooSmall()) return;
    if (_text === '?') help = !help;
    else if (!help) {
      if (key.name === 'return' && game.status !== 'playing') game.start();
      else if (key.name === 'left') game.move(-1);
      else if (key.name === 'right') game.move(1);
      else if (key.name === 'up') game.rotate();
      else if (key.name === 'down') game.tick(true);
      else if (key.name === 'space') game.drop();
    }
    draw();
  };

  emitKeypressEvents(input);
  input.setRawMode(true);
  input.resume();
  input.on('keypress', onKey);
  output.on('resize', draw);
  signals.on('SIGINT', stop);
  signals.on('SIGTERM', stop);
  output.write('\x1b[?1049h\x1b[?25l');
  draw();
  timer = schedule(() => {
    if (stopped || tooSmall() || help || game.status !== 'playing') return;
    game.tick();
    draw();
  }, 600);
  return stop;
}
