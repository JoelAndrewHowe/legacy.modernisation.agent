import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

test('npm start launches the game successfully with a 24-row display', () => {
  const result = spawnSync('npm', ['--silent', 'start'], {
    cwd: new URL('../', import.meta.url),
    encoding: 'utf8',
    timeout: 5000,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stderr, '');
  const rows = result.stdout.trimEnd().split('\n');
  assert.equal(rows.length, 24);
  assert.equal(rows[0], '+--------------------+');
  assert.equal(rows[21], rows[0]);
  assert.match(rows[22], /Tetris.*Score: 0/);
  assert.match(rows[23], /Space drop Q quit/);
  assert.match(result.stdout, /\[\]/);
});
