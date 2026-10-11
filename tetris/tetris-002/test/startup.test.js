import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { renderStartup, start } from '../src/index.js';

test('startup display fits in 24 rows', () => {
  assert.equal(renderStartup().split('\n').length, 24);
});

test('interactive startup and quit restore terminal state', () => {
  const input = new EventEmitter();
  Object.assign(input, {
    isTTY: true,
    isRaw: false,
    setRawMode(value) { this.isRaw = value; },
    resume() {},
    pause() {},
  });
  let display = '';
  const output = { isTTY: true, write(text) { display += text; } };
  const stop = start({ input, output });
  try {
    assert.equal(input.isRaw, true);
    assert.ok(display.includes('Tetris | Score: 0'));
    input.emit('keypress', 'q', { name: 'q' });
    assert.equal(input.isRaw, false);
    assert.equal(input.listenerCount('keypress'), 0);
    assert.ok(display.endsWith('\x1b[?25h\x1b[?1049l'));
  } finally {
    stop();
  }
});

test('npm start launches the entry point and explains non-interactive use', () => {
  const result = spawnSync('npm', ['start'], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stdout, /Tetris requires an interactive terminal/);
});
