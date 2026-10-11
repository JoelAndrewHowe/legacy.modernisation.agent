import test from 'node:test';
import assert from 'node:assert/strict';
import { Game } from '../src/game.js';
import { renderFrame } from '../src/app.js';

function game() {
  const g = new Game(() => 0);
  g.start();
  return g;
}

test('start spawns a falling piece; walls, floor and occupied cells block movement', () => {
  const g = game();
  assert.equal(g.status, 'playing');
  g.tick();
  assert.equal(g.piece.y, 1);
  while (g.move(-1)) {}
  assert.equal(g.piece.x, 0);
  assert.equal(g.move(-1), false);
  g.board[2][0] = 1;
  assert.equal(g.move(0, 1), false);
  g.board[2][0] = 0;
  while (g.move(0, 1)) {}
  assert.equal(g.piece.y, 19);
  g.tick();
  assert.equal(g.board[19].filter(Boolean).length, 4);
  assert.equal(g.piece.y, 0);
});

test('rotation changes orientation and kicks away from a wall', () => {
  const g = game();
  g.rotate();
  assert.deepEqual(g.piece.shape, [[1], [1], [1], [1]]);
  while (g.move(1)) {}
  g.rotate();
  assert.equal(g.piece.shape[0].length, 4);
  assert.ok(g.fits(g.piece));
});

test('soft and hard drops score; completed lines disappear', () => {
  const g = game();
  g.tick(true);
  assert.equal(g.score, 1);
  g.board[19] = [1, 1, 1, 0, 0, 0, 0, 1, 1, 1];
  g.drop();
  assert.equal(g.lines, 1);
  assert.equal(g.score, 137);
  assert.ok(g.board.every(row => row.every(cell => !cell)));
});

test('blocked spawn ends the game; restart resets score and board', () => {
  const g = game();
  g.move(-3);
  g.board[0][3] = 1;
  g.drop();
  assert.equal(g.status, 'over');
  assert.match(renderFrame(g), /GAME OVER/);
  assert.match(renderFrame(g), /Enter: restart/);
  const before = JSON.stringify(g);
  g.tick();
  g.drop();
  g.rotate();
  assert.equal(JSON.stringify(g), before);
  g.start();
  assert.equal(g.status, 'playing');
  assert.equal(g.score, 0);
  assert.ok(g.board.every(row => row.every(cell => !cell)));
});

test('every status and help frame fits in 22 columns and 24 rows', () => {
  const g = game();
  for (const status of ['ready', 'playing', 'over']) {
    g.status = status;
    for (const help of [false, true]) {
      const rows = renderFrame(g, help).split('\r\n');
      assert.equal(rows.length, 24);
      assert.ok(rows.every(row => row.length <= 22));
    }
  }
});
