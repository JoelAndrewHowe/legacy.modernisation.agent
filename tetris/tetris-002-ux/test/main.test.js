import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

// Exercise the documented launcher rather than only calling startApp directly.
test('npm start rejects noninteractive input with actionable feedback', () => {
  const result = spawnSync('npm', ['start'], {
    cwd: new URL('..', import.meta.url),
    encoding: 'utf8',
    timeout: 10000,
    env: { ...process.env, NO_COLOR: '1' },
  });
  assert.ifError(result.error);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Tetris requires an interactive terminal\. Run npm start in a terminal\./);
  assert.doesNotMatch(result.stdout + result.stderr, /\x1b\[/);
});
