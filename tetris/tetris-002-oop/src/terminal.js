import { emitKeypressEvents } from 'node:readline';

export class Terminal {
  constructor(input = process.stdin, output = process.stdout) {
    this.input = input;
    this.output = output;
    this.active = false;
    this.previousRawMode = false;
  }

  open(onKey) {
    if (!this.input.isTTY || !this.output.isTTY) {
      throw new Error('Tetris requires an interactive terminal. Run npm start in a terminal.');
    }
    this.previousRawMode = Boolean(this.input.isRaw);
    emitKeypressEvents(this.input);
    this.onKey = onKey;
    this.input.on('keypress', this.onKey);
    this.active = true;
    this.input.setRawMode(true);
    this.input.resume();
    this.output.write('\x1b[?1049h\x1b[?25l');
  }

  render(lines) {
    this.output.write(`\x1b[H${lines.join('\n')}\x1b[J`);
  }

  close() {
    if (!this.active) return;
    this.active = false;
    this.input.removeListener('keypress', this.onKey);
    this.input.setRawMode(this.previousRawMode);
    this.input.pause();
    this.output.write('\x1b[?25h\x1b[?1049l');
  }
}
