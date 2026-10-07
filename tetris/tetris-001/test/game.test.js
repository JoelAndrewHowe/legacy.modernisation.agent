import test from 'node:test';
import assert from 'node:assert/strict';
import { Game, SHAPES } from '../src/game.js';

const game = () => new Game({ random: () => 0.5 });
const piece = (g, type, x, y) => {
  g.active = { type, matrix: SHAPES[type].map(row => [...row]), x, y };
};

test('starts with an empty 10x20 board and a valid piece', () => {
  const g = game();
  assert.equal(g.board.length, 20);
  assert.ok(g.board.every(row => row.length === 10 && row.every(cell => cell === null)));
  assert.equal(g.collides(g.active), false);
  assert.equal(g.score, 0);
  assert.equal(g.gameOver, false);
});

test('seven-piece bag supplies every tetromino once per bag', () => {
  const g = game();
  const types = [g.active.type, ...Array.from({ length: 6 }, () => g.nextType())];
  assert.deepEqual(types.sort(), Object.keys(SHAPES).sort());
  assert.equal(new Set(Array.from({ length: 7 }, () => g.nextType())).size, 7);
});

test('movement respects walls, floor, and occupied cells', () => {
  const g = game();
  piece(g, 'O', 0, 18);
  assert.equal(g.move(-1), false);
  assert.equal(g.move(0, 1), false);
  assert.equal(g.move(1), true);
  g.board[18][3] = 'T';
  assert.equal(g.move(1), false);
  assert.equal(g.active.x, 1);
});

test('rotation is reversible and four clockwise turns restore the shape', () => {
  const g = game();
  piece(g, 'T', 3, 3);
  const original = structuredClone(g.active);
  assert.equal(g.rotate(), true);
  assert.notDeepEqual(g.active.matrix, original.matrix);
  g.rotate(-1);
  assert.deepEqual(g.active, original);
  for (let i = 0; i < 4; i++) g.rotate();
  assert.deepEqual(g.active, original);
});

test('rotation kicks a vertical I piece away from the wall', () => {
  const g = game();
  piece(g, 'I', 0, 3);
  g.rotate();
  g.move(-2);
  assert.equal(g.active.x, -2);
  assert.equal(g.rotate(), true);
  assert.equal(g.collides(g.active), false);
});

test('blocked rotation leaves the piece unchanged', () => {
  const g = game();
  piece(g, 'T', 3, 3);
  g.board = g.board.map(row => row.map(() => 'J'));
  g.active.matrix.forEach((row, dy) => row.forEach((cell, dx) => {
    if (cell) g.board[g.active.y + dy][g.active.x + dx] = null;
  }));
  const original = structuredClone(g.active);
  assert.equal(g.rotate(), false);
  assert.deepEqual(g.active, original);
});

test('gravity locks at the floor and spawns another piece without drop points', () => {
  const g = game();
  piece(g, 'O', 0, 17);
  g.tick();
  assert.equal(g.active.y, 18);
  g.tick();
  assert.equal(g.board[19][0], 'O');
  assert.equal(g.active.y, 0);
  assert.equal(g.score, 0);
});

test('soft and hard drops award points and lock the piece', () => {
  const g = game();
  piece(g, 'O', 0, 0);
  assert.equal(g.softDrop(), true);
  assert.equal(g.score, 1);
  assert.equal(g.hardDrop(), 17);
  assert.equal(g.score, 35);
  assert.equal(g.board[18][0], 'O');
  assert.equal(g.board[19][1], 'O');
});

test('locking clears full rows, shifts remaining blocks down, and scores', () => {
  const g = game();
  g.board[17][5] = 'T';
  for (const y of [18, 19]) g.board[y].fill('J', 2);
  piece(g, 'O', 0, 18);
  g.lock();
  assert.equal(g.lines, 2);
  assert.equal(g.score, 300);
  assert.equal(g.board[19][5], 'T');
  assert.ok(g.board.slice(0, 2).every(row => row.every(cell => cell === null)));
});

test('four-line clears and level progression affect scoring and speed', () => {
  const g = game();
  g.lines = 9;
  for (let y = 16; y < 20; y++) g.board[y].fill('I');
  assert.equal(g.clearLines(), 4);
  assert.equal(g.score, 800);
  assert.equal(g.level, 2);
  assert.ok(g.dropInterval < 800);
  g.board[19].fill('I');
  g.clearLines();
  assert.equal(g.score, 1000);
});

test('blocked spawn ends game and input becomes inert', () => {
  const g = game();
  g.board[0].fill('Z');
  g.board[1].fill('Z');
  assert.equal(g.spawn(), false);
  assert.equal(g.gameOver, true);
  const snapshot = structuredClone({ board: g.board, active: g.active, score: g.score });
  assert.equal(g.move(1), false);
  assert.equal(g.rotate(), false);
  assert.equal(g.tick(), false);
  assert.equal(g.softDrop(), false);
  assert.equal(g.hardDrop(), 0);
  g.lock();
  assert.deepEqual({ board: g.board, active: g.active, score: g.score }, snapshot);
});

test('locking above the board ends the game', () => {
  const g = game();
  piece(g, 'O', 0, -1);
  g.lock();
  assert.equal(g.gameOver, true);
});

test('rejects unusable board dimensions', () => {
  assert.throws(() => new Game({ width: 3 }), RangeError);
  assert.throws(() => new Game({ height: 2.5 }), RangeError);
});
