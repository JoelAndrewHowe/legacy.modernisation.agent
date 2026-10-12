import readline from 'node:readline';
import { TetrisGame } from './tetris.js';

const ENTER = '\x1b[?1049h\x1b[?25l';
const LEAVE = '\x1b[?25h\x1b[?1049l';
const CONTROLS = '< > move | Up spin | Down drop | Space slam | R new | Q quit';
const MIN_COLUMNS = CONTROLS.length;

// One header + twenty board rows + two borders + one help row = 24.
export function renderFrame(game) {
  const rows = game.board.rows.map(row => row.map(cell => cell ? '#' : ' '));
  if (!game.gameOver) {
    for (const { x, y } of game.active.cells()) {
      if (y >= 0 && y < rows.length && x >= 0 && x < rows[y].length) rows[y][x] = '@';
    }
  }
  const status = game.gameOver ? 'GAME OVER R:new Q:quit' : 'Tetris';
  const header = `${status} Score:${game.score} Lines:${game.lines} Next:${game.nextType}`;
  const border = `+${'-'.repeat(game.board.width)}+`;
  return [header.slice(0, MIN_COLUMNS), border,
    ...rows.map(row => `|${row.join('')}|`), border, CONTROLS].join('\n');
}

export class TerminalGame {
  constructor(output = process.stdout, {
    input = process.stdin,
    signals = process,
    createGame = () => new TetrisGame(),
    setTimer = setTimeout,
    clearTimer = clearTimeout,
  } = {}) {
    this.output = output;
    this.input = input;
    this.signals = signals;
    this.createGame = createGame;
    this.setTimer = setTimer;
    this.clearTimer = clearTimer;
    this.game = createGame();
    this.running = false;
    this.timer = null;
    this.onKey = (text, key) => this.handleKey(text, key);
    this.onResize = () => this.render();
    this.onExit = () => this.stop();
  }

  start() {
    if (this.running) return;
    // A redirected invocation prints a snapshot without owning any resources.
    if (!this.input.isTTY || !this.output.isTTY) {
      this.output.write(`${renderFrame(this.game)}\n`);
      return;
    }
    this.running = true;
    this.wasRaw = Boolean(this.input.isRaw);
    this.wasPaused = this.input.isPaused();
    readline.emitKeypressEvents(this.input);
    this.input.on('keypress', this.onKey);
    this.output.on('resize', this.onResize);
    for (const event of ['SIGINT', 'SIGTERM', 'SIGHUP', 'exit']) {
      this.signals.on(event, this.onExit);
    }
    try {
      this.input.setRawMode(true);
      this.input.resume();
      this.output.write(ENTER);
      this.render();
      this.scheduleTick();
    } catch (error) {
      this.stop();
      throw error;
    }
  }

  fitsTerminal() {
    return (this.output.rows ?? 24) >= 24 &&
      (this.output.columns ?? MIN_COLUMNS) >= MIN_COLUMNS;
  }

  render() {
    const frame = this.fitsTerminal() ? renderFrame(this.game) :
      `Resize to ${MIN_COLUMNS}x24; Q quits`.slice(0, Math.max(0, (this.output.columns ?? 1) - 1));
    // No trailing newline: the bottom row must not scroll a 24-row terminal.
    this.output.write(`\x1b[H\x1b[2J${frame.replaceAll('\n', '\r\n')}`);
  }

  scheduleTick() {
    if (!this.running || this.game.gameOver) return;
    this.timer = this.setTimer(() => {
      this.timer = null;
      if (!this.running) return;
      if (this.fitsTerminal()) this.game.tick();
      this.render();
      this.scheduleTick();
    }, this.game.gravityInterval);
  }

  handleKey(text, key = {}) {
    if (!this.running) return;
    const name = key.name ?? text?.toLowerCase();
    if (name === 'q' || (key.ctrl && name === 'c')) {
      this.stop();
      return;
    }
    if (!this.fitsTerminal()) return;
    if (name === 'r') this.game = this.createGame();
    else if (name === 'left') this.game.move(-1);
    else if (name === 'right') this.game.move(1);
    else if (name === 'up') this.game.rotate();
    else if (name === 'down') this.game.softDrop();
    else if (name === 'space' || text === ' ') this.game.hardDrop();
    else return;
    if (this.game.gameOver && this.timer !== null) {
      this.clearTimer(this.timer);
      this.timer = null;
    }
    if (this.timer === null) this.scheduleTick();
    this.render();
  }

  stop() {
    if (!this.running) return;
    this.running = false;
    if (this.timer !== null) this.clearTimer(this.timer);
    this.timer = null;
    this.input.removeListener('keypress', this.onKey);
    this.output.removeListener('resize', this.onResize);
    for (const event of ['SIGINT', 'SIGTERM', 'SIGHUP', 'exit']) {
      this.signals.removeListener(event, this.onExit);
    }
    try {
      this.input.setRawMode(this.wasRaw);
    } finally {
      if (this.wasPaused) this.input.pause();
      this.output.write(LEAVE);
    }
  }
}
