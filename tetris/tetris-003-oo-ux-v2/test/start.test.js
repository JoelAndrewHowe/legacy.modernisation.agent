import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { TerminalGame } from '../src/terminal-game.js';

test('the terminal scaffold writes a brief startup message', () => {
  let output = '';
  const game = new TerminalGame({ write: (text) => { output += text; } });
  game.start();
  assert.match(output, /^Tetris\n/);
  assert.match(output, /gameplay is not implemented yet/);
  assert.ok(output.trimEnd().split('\n').length <= 24);
});

test('the Node entry point exits successfully', () => {
  const result = spawnSync(process.execPath, ['src/index.js'], {
    cwd: new URL('../', import.meta.url),
    encoding: 'utf8',
    timeout: 5000,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0);
  assert.equal(result.stderr, '');
  assert.match(result.stdout, /^Tetris\n/);
});
