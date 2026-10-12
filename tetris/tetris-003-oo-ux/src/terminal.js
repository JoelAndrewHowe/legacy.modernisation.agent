import { emitKeypressEvents } from 'node:readline';
import { renderGame } from './renderer.js';

export class Terminal {
  constructor(game, input = process.stdin, output = process.stdout) {
    this.game = game;
    this.input = input;
    this.output = output;
    this.running = false;
    this.onKeypress = (_text, key) => {
      if (key?.name === 'q' || (key?.ctrl && key.name === 'c')) {
        this.stop();
        return;
      }
      if (!this.running) return;
      switch (key?.name) {
        case 'left': this.game.move(-1); break;
        case 'right': this.game.move(1); break;
        case 'up': this.game.rotate(); break;
        case 'down': this.game.tick(); break;
        case 'space': this.game.drop(); break;
        default: return;
      }
      this.draw();
    };
    this.onSignal = () => this.stop();
  }

  draw() {
    this.output.write(`\x1b[H${renderGame(this.game.snapshot()).replaceAll('\n', '\r\n')}\x1b[J`);
    if (this.game.gameOver) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
  }

  start() {
    if (this.running) return;
    if (!this.input.isTTY || !this.output.isTTY) {
      this.output.write(`${renderGame(this.game.snapshot())}\n`);
      return;
    }
    this.running = true;
    this.wasRaw = Boolean(this.input.isRaw);
    emitKeypressEvents(this.input);
    this.input.setRawMode(true);
    this.input.resume();
    this.input.on('keypress', this.onKeypress);
    process.on('SIGINT', this.onSignal);
    process.on('SIGTERM', this.onSignal);
    this.output.write('\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H');
    this.timer = setInterval(() => {
      this.game.tick();
      this.draw();
    }, 500);
    this.draw();
  }

  stop() {
    if (!this.running) return;
    this.running = false;
    clearInterval(this.timer);
    this.timer = undefined;
    this.input.removeListener('keypress', this.onKeypress);
    process.removeListener('SIGINT', this.onSignal);
    process.removeListener('SIGTERM', this.onSignal);
    this.input.setRawMode(this.wasRaw);
    this.input.pause();
    this.output.write('\x1b[?25h\x1b[?1049l');
  }
}
