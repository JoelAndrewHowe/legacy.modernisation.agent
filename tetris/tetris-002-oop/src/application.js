import { Terminal } from './terminal.js';
import { TetrisGame } from './game.js';

export class TetrisApplication {
  constructor(terminal = new Terminal(), signals = process,
    { game = new TetrisGame(), timers = globalThis } = {}) {
    this.terminal = terminal;
    this.signals = signals;
    this.game = game;
    this.timers = timers;
    this.running = false;
    this.timer = null;
    this.stop = this.stop.bind(this);
  }

  start() {
    if (this.running) return;
    this.running = true;
    try {
      this.terminal.open((_text, key) => this.handleKey(key));
      this.signals.on('SIGINT', this.stop);
      this.signals.on('SIGTERM', this.stop);
      this.signals.on('exit', this.stop);
      this.render();
      this.scheduleGravity();
    } catch (error) {
      this.stop();
      throw error;
    }
  }

  handleKey(key) {
    if (!this.running) return;
    if (key?.name === 'q' || (key?.ctrl && key.name === 'c')) {
      this.stop();
      return;
    }
    if (this.game.gameOver) return;
    const actions = {
      left: () => this.game.move(-1),
      right: () => this.game.move(1),
      up: () => this.game.rotate(),
      down: () => this.game.softDrop(),
      space: () => this.game.hardDrop(),
    };
    if (!actions[key?.name]) return;
    this.update(actions[key.name]);
  }

  update(action) {
    try {
      action();
      this.render();
      if (this.game.gameOver) this.cancelGravity();
    } catch (error) {
      this.stop();
      throw error;
    }
  }

  scheduleGravity() {
    if (!this.running || this.game.gameOver) return;
    this.timer = this.timers.setTimeout(() => {
      this.timer = null;
      if (!this.running) return;
      this.update(() => this.game.tick());
      this.scheduleGravity();
    }, this.game.gravityInterval);
  }

  cancelGravity() {
    if (this.timer !== null) this.timers.clearTimeout(this.timer);
    this.timer = null;
  }

  render() {
    const rows = this.game.board.rows.map((row) => [...row]);
    if (!this.game.gameOver) {
      for (const { x, y } of this.game.active.cells()) rows[y][x] = this.game.active.type;
    }
    const border = `+${'-'.repeat(this.game.board.width * 2)}+`;
    this.terminal.render([
      `TETRIS | Score: ${this.game.score} | Level: ${this.game.level}`,
      border,
      ...rows.map((row) => `|${row.map((cell) => cell ? '[]' : '  ').join('')}|`),
      border,
      this.game.gameOver ? 'GAME OVER | Q / Ctrl+C: quit' :
        'Left/Right: move | Up: rotate | Down: drop | Space: slam | Q/Ctrl+C: quit',
    ]);
  }

  stop() {
    this.running = false;
    this.cancelGravity();
    this.signals.removeListener('SIGINT', this.stop);
    this.signals.removeListener('SIGTERM', this.stop);
    this.signals.removeListener('exit', this.stop);
    this.terminal.close();
  }
}
