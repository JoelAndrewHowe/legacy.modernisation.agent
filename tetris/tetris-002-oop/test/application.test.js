import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { TetrisApplication } from '../src/application.js';
import { Terminal } from '../src/terminal.js';

function fixture() {
  const input = new EventEmitter();
  Object.assign(input, {
    isTTY: true,
    isRaw: false,
    setRawMode(value) { this.isRaw = value; },
    resume() {},
    pause() {},
  });
  const writes = [];
  const output = { isTTY: true, write: (text) => writes.push(text) };
  const signals = new EventEmitter();
  return { input, writes, signals, app: new TetrisApplication(new Terminal(input, output), signals) };
}

test('startup displays a 24-row board and quit restores terminal state', () => {
  const { app, input, writes, signals } = fixture();
  app.start();
  assert.equal(input.isRaw, true);
  assert.equal(writes[1].split('\n').length, 24);
  assert.match(writes[1], /TETRIS/);
  input.emit('keypress', 'q', { name: 'q' });
  assert.equal(input.isRaw, false);
  assert.equal(input.listenerCount('keypress'), 0);
  assert.equal(signals.listenerCount('SIGINT'), 0);
  assert.equal(writes.at(-1), '\x1b[?25h\x1b[?1049l');
  app.stop();
  assert.equal(writes.length, 3);
});

for (const signal of ['SIGINT', 'SIGTERM', 'exit']) {
  test(`${signal} restores the terminal`, () => {
    const { app, input, signals } = fixture();
    app.start();
    signals.emit(signal);
    assert.equal(input.isRaw, false);
    assert.equal(input.listenerCount('keypress'), 0);
  });
}

test('non-interactive startup fails clearly without terminal escape sequences', () => {
  const result = spawnSync(process.execPath, ['src/index.js'], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /requires an interactive terminal/);
  assert.equal(result.stdout, '');
});
