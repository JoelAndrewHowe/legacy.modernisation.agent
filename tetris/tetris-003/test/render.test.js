import assert from 'node:assert/strict';
import test from 'node:test';
import { Game, render } from '../src/game.js';

test('compact status preserves score and lines when they fit', () => {
  const game = new Game(() => 1 / 7);
  game.score = 336;
  game.lines = 2;
  const rows = render(game, 24).split('\n');
  assert.equal(rows.length, 24);
  assert.equal(rows[22], 'Tetris S:336 L:2');
});

test('narrow game-over displays retain score without adding or wrapping rows', () => {
  const game = new Game(() => 1 / 7);
  game.over = true;
  for (const score of [0, 336, 1234567890, Number.MAX_VALUE]) {
    game.score = score;
    for (const columns of [12, 13, 16, 20]) {
      const rows = render(game, columns).split('\n');
      assert.equal(rows.length, 24);
      assert.ok(rows.every(row => row.length <= columns));
      assert.match(rows[22], /^GAME OVER/);
      assert.match(rows[23], /Q/);
      const label = `S:${score}`;
      if (rows[22].includes(label)) continue;
      assert.ok(rows[0].includes(label.length <= rows[0].length - 2
        ? label : `S:${score.toExponential(1)}`));
      assert.ok(rows[0].startsWith('+') && rows[0].endsWith('+'));
      assert.equal(rows[21], `+${'-'.repeat(10)}+`);
    }
  }
});

test('render overlays the active piece without mutating the board and hides it on game over', () => {
  const game = new Game(() => 1 / 7);
  game.board[19][0] = 1;
  const before = JSON.stringify(game);
  const rows = render(game, 12).split('\n');
  assert.equal(rows[1], '|    ##    |');
  assert.equal(rows[2], '|    ##    |');
  assert.equal(rows[20], '|#         |');
  assert.equal(JSON.stringify(game), before);
  game.over = true;
  assert.equal(render(game, 12).split('\n')[1], '|          |');
});
