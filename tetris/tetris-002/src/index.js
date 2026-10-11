import { emitKeypressEvents } from 'node:readline';
import { pathToFileURL } from 'node:url';

export function renderStartup() {
  return [
    'Tetris | Score: 0',
    '+--------------------+',
    ...Array.from({ length: 20 }, () => `|${' '.repeat(20)}|`),
    '+--------------------+',
    'Q / Ctrl+C: quit',
  ].join('\n');
}

export function start({ input = process.stdin, output = process.stdout } = {}) {
  if (!input.isTTY || !output.isTTY) {
    output.write('Tetris requires an interactive terminal. Run npm start in a terminal.\n');
    return false;
  }

  const wasRaw = Boolean(input.isRaw);
  let stopped = false;
  const stop = () => {
    if (stopped) return;
    stopped = true;
    input.off('keypress', onKey);
    process.off('SIGINT', stop);
    process.off('SIGTERM', stop);
    process.off('exit', stop);
    input.setRawMode(wasRaw);
    input.pause();
    output.write('\x1b[?25h\x1b[?1049l');
  };
  const onKey = (text, key) => {
    if (text?.toLowerCase() === 'q' || (key?.ctrl && key.name === 'c')) stop();
  };

  emitKeypressEvents(input);
  input.setRawMode(true);
  input.resume();
  input.on('keypress', onKey);
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
  process.on('exit', stop);
  output.write(`\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H${renderStartup().replaceAll('\n', '\r\n')}`);
  return stop;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (start() === false) process.exitCode = 1;
}
