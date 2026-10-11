import { Terminal } from './terminal.js';

// Application lifecycle; game rules and gameplay will be added separately.
export class TetrisApplication {
  constructor(terminal = new Terminal(), signals = process) {
    this.terminal = terminal;
    this.signals = signals;
    this.stop = this.stop.bind(this);
  }

  start() {
    try {
      this.terminal.open((_text, key) => {
        if (key?.name === 'q' || (key?.ctrl && key.name === 'c')) this.stop();
      });
      this.signals.on('SIGINT', this.stop);
      this.signals.on('SIGTERM', this.stop);
      this.signals.on('exit', this.stop);
      this.terminal.render([
        'TETRIS | Score: 0',
        '+--------------------+',
        ...Array(20).fill('|                    |'),
        '+--------------------+',
        'Q / Ctrl+C: quit',
      ]);
    } catch (error) {
      this.stop();
      throw error;
    }
  }

  stop() {
    this.signals.removeListener('SIGINT', this.stop);
    this.signals.removeListener('SIGTERM', this.stop);
    this.signals.removeListener('exit', this.stop);
    this.terminal.close();
  }
}
