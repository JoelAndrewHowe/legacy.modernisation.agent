import { emitKeypressEvents } from 'node:readline';
import { Game } from './game.js';

export const MIN_COLUMNS = 64;
export const MIN_ROWS = 24;
const PALETTE = { I: 96, O: 93, T: 95, S: 92, Z: 91, J: '38;5;111', L: '38;5;215' };

// Bright foregrounds on an explicit black background; labels also identify pieces
// without relying on hue. NO_COLOR's presence (even an empty value) disables SGR.
export function renderGame(game, { env = process.env, columns = 80, rows = 24 } = {}) {
  const colour = !Object.hasOwn(env, 'NO_COLOR');
  const paint = (text, code) => colour ? `\x1b[1;${code};40m${text}\x1b[0m` : text;
  if (columns < MIN_COLUMNS || rows < MIN_ROWS) {
    const messages = ['Terminal too small', `Need ${MIN_COLUMNS}x${MIN_ROWS}; resize to play`, 'Q/Esc quits'];
    return messages.slice(0, Math.max(0, rows)).map(text => paint(text.slice(0, Math.max(0, columns)), 93)).join('\n');
  }
  const border = paint(`+${'-'.repeat(20)}+`, 97);
  const display = [
    paint(`TETRIS | Score: ${game.score} | Lines: ${game.lines} | Level: ${game.level}`.slice(0, columns), 97),
    border,
  ];
  for (const row of game.displayBoard()) {
    display.push(paint('|', 97) + row.map(cell => cell ? paint(cell.repeat(2), PALETTE[cell]) : paint(' .', 90)).join('') + paint('|', 97));
  }
  display.push(border, game.over
    ? paint('GAME OVER | R restart | Q/Esc quit', 91)
    : paint('Left/Right move; Up rotate; Down drop; Space slam; Q/Esc quit', 96));
  return display.join('\n');
}

export function renderWelcome(options) {
  return renderGame(new Game(() => 0.5), options);
}

export function startTerminal(input = process.stdin, output = process.stdout, { game = new Game(), env = process.env, tickMs = 50 } = {}) {
  if (!input.isTTY || !output.isTTY) {
    throw new Error('Tetris requires an interactive terminal. Run npm start in a terminal.');
  }

  const wasRaw = Boolean(input.isRaw);
  let stopped = false;
  let timer;
  let elapsed = 0;
  const dimensions = () => ({ columns: output.columns ?? 80, rows: output.rows ?? 24 });
  const fits = () => {
    const { columns, rows } = dimensions();
    return columns >= MIN_COLUMNS && rows >= MIN_ROWS;
  };
  const draw = () => output.write('\x1b[H\x1b[2J' + renderGame(game, { env, ...dimensions() }));
  const onResize = () => { elapsed = 0; draw(); };
  const stop = () => {
    if (stopped) return;
    stopped = true;
    clearInterval(timer);
    input.off('keypress', onKeypress);
    output.off?.('resize', onResize);
    process.off('SIGINT', stop);
    process.off('SIGTERM', stop);
    process.off('exit', stop);
    input.setRawMode(wasRaw);
    input.pause();
    output.write('\x1b[?25h\x1b[?1049l');
  };
  const onKeypress = (_character, key) => {
    if (key?.name === 'q' || key?.name === 'escape' || (key?.ctrl && key.name === 'c')) {
      stop();
      return;
    }
    if (stopped || !fits()) return;
    if (game.over) {
      if (key?.name === 'r') { game.restart(); elapsed = 0; }
    } else {
      switch (key?.name) {
        case 'left': game.move(-1); break;
        case 'right': game.move(1); break;
        case 'up': game.rotate(); break;
        case 'down': game.drop(true); elapsed = 0; break;
        case 'space': game.hardDrop(); elapsed = 0; break;
      }
    }
    draw();
  };

  emitKeypressEvents(input);
  input.setRawMode(true);
  input.resume();
  input.on('keypress', onKeypress);
  output.on?.('resize', onResize);
  process.once('SIGINT', stop);
  process.once('SIGTERM', stop);
  process.once('exit', stop);
  output.write('\x1b[?1049h\x1b[?25l');
  draw();
  timer = setInterval(() => {
    if (!fits() || game.over) { elapsed = 0; return; }
    elapsed += tickMs;
    if (elapsed >= game.fallDelay) {
      elapsed = 0;
      game.drop();
      draw();
    }
  }, tickMs);
  return stop;
}
