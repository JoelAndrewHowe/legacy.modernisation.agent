export class TerminalGame {
  constructor(output = process.stdout) {
    this.output = output;
  }

  start() {
    this.output.write('Tetris\nTerminal game scaffold ready; gameplay is not implemented yet.\n');
  }
}
