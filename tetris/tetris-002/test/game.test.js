import assert from 'node:assert/strict';
import test from 'node:test';
import { Game, WIDTH, HEIGHT } from '../src/game.js';

const game = () => new Game({ random: () => 0.999 });
const square = (x, y) => ({ type: 'O', matrix: [[1, 1], [1, 1]], x, y });

test('empty 10x20 board spawns one piece; each bag contains all seven types', () => {
  const g = game();
  assert.equal(g.board.length, HEIGHT);
  assert.ok(g.board.every(row => row.length === WIDTH && row.every(cell => cell === null)));
  const types = [g.active.type];
  for (let i = 0; i < 6; i++) { g.spawn(); types.push(g.active.type); }
  assert.equal(new Set(types).size, 7);
  assert.equal(g.snapshot().board.flat().filter(Boolean).length, 4);
  assert.equal(g.board.flat().filter(Boolean).length, 0);
});

test('movement rejects walls, floor and settled blocks', () => {
  const g = game();
  g.active = square(0, 18);
  assert.equal(g.move(-1), false);
  assert.equal(g.move(0, 1), false);
  g.board[18][2] = 'T';
  assert.equal(g.move(1), false);
  g.board[18][2] = null;
  assert.equal(g.move(1), true);
  g.active = square(8, 0);
  assert.equal(g.move(1), false);
});

test('rotation is reversible and kicks away from walls and floor', () => {
  const g = game();
  g.active = { type: 'T', matrix: [[0, 1, 0], [1, 1, 1], [0, 0, 0]], x: 3, y: 0 };
  const before = structuredClone(g.active);
  assert.equal(g.rotate(), true);
  assert.equal(g.rotate(-1), true);
  assert.deepEqual(g.active, before);
  g.active = { type: 'I', matrix: [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0]], x: -2, y: 2 };
  assert.equal(g.rotate(), true);
  assert.equal(g.fits(g.active), true);
  g.active = { ...before, y: 18 };
  assert.equal(g.rotate(), true);
  assert.equal(g.fits(g.active), true);
});

test('blocked rotation leaves the active piece unchanged', () => {
  const g = game();
  g.board = Array.from({ length: HEIGHT }, () => Array(WIDTH).fill('J'));
  g.active = { type: 'T', matrix: [[0, 1, 0], [1, 1, 1], [0, 0, 0]], x: 3, y: 5 };
  g.active.matrix.forEach((row, dy) => row.forEach((cell, dx) => {
    if (cell) g.board[5 + dy][3 + dx] = null;
  }));
  const before = structuredClone(g.active);
  assert.equal(g.rotate(), false);
  assert.deepEqual(g.active, before);
});

test('gravity locks at floor and spawns a new piece without awarding drop points', () => {
  const g = game();
  g.active = square(0, 17);
  g.tick();
  assert.equal(g.active.y, 18);
  g.tick();
  assert.equal(g.board.flat().filter(Boolean).length, 4);
  assert.equal(g.active.y, 0);
  assert.equal(g.score, 0);
});

test('soft and hard drops award points for distance and hard drop locks', () => {
  const g = game();
  g.active = square(0, 0);
  assert.equal(g.softDrop(), true);
  assert.equal(g.score, 1);
  assert.equal(g.hardDrop(), 17);
  assert.equal(g.score, 35);
  assert.equal(g.board[19][0], 'O');
});

for (const [count, points] of [[1, 100], [2, 300], [3, 500], [4, 800]]) {
  test(`${count} full rows clear, compact and score at the current level`, () => {
    const g = game();
    g.lines = 10;
    g.board[HEIGHT - count - 1][0] = 'T';
    for (let y = HEIGHT - count; y < HEIGHT; y++) g.board[y].fill('I');
    assert.equal(g.clearLines(), count);
    assert.equal(g.score, points * 2);
    assert.equal(g.lines, 10 + count);
    assert.equal(g.board[19][0], 'T');
    assert.ok(g.board.slice(0, count).every(row => row.every(cell => cell === null)));
    assert.notEqual(g.board[0], g.board[1]);
  });
}

test('locking completes and clears a row before spawning', () => {
  const g = game();
  g.board[19].fill('I');
  g.board[19][0] = g.board[19][1] = null;
  g.active = square(0, 18);
  g.tick();
  assert.equal(g.lines, 1);
  assert.equal(g.score, 100);
  assert.equal(g.board[19][0], 'O');
  assert.equal(g.board[19][2], null);
});

test('blocked spawn ends the game and further actions do nothing', () => {
  const g = game();
  g.board[0].fill('I');
  g.board[1].fill('I');
  assert.equal(g.spawn(), false);
  assert.equal(g.gameOver, true);
  const before = g.snapshot();
  assert.equal(g.move(1), false);
  assert.equal(g.rotate(), false);
  assert.equal(g.tick(), false);
  assert.equal(g.softDrop(), false);
  assert.equal(g.hardDrop(), 0);
  assert.deepEqual(g.snapshot(), before);
});

test('locking a piece above the ceiling ends the game', () => {
  const g = game();
  g.active = square(0, -1);
  g.lock();
  assert.equal(g.gameOver, true);
  assert.equal(g.active, null);
});

test('snapshots are independent and level increases accelerate gravity', () => {
  const g = game();
  const snapshot = g.snapshot();
  snapshot.board[19][0] = 'I';
  assert.equal(g.board[19][0], null);
  const interval = g.dropInterval;
  g.lines = 10;
  assert.equal(g.level, 2);
  assert.ok(g.dropInterval < interval);
  g.lines = 1000;
  assert.equal(g.dropInterval, 100);
});
