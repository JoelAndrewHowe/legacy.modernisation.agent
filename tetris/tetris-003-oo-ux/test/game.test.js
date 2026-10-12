import assert from 'node:assert/strict';
import test from 'node:test';
import { Game } from '../src/game.js';

function cells(piece) {
  return piece.shape.flatMap((row, y) => row.flatMap((cell, x) =>
    cell ? [[piece.x + x, piece.y + y]] : []));
}

function moveTo(game, x) {
  while (game.piece.x !== x) {
    assert.equal(game.move(Math.sign(x - game.piece.x)), true);
  }
}

test('state reads and snapshots cannot mutate gameplay; internal operations are private', () => {
  const game = new Game(() => 0);
  const original = game.snapshot();
  game.board[0][4] = true;
  game.piece.shape[0][0] = 0;
  const snapshot = game.snapshot();
  snapshot.board[0][4] = true;
  snapshot.piece.x = 100;
  snapshot.piece.shape[0][0] = 0;
  snapshot.score = 999;
  snapshot.gameOver = true;
  for (const key of ['board', 'piece', 'score', 'gameOver', 'width', 'height']) {
    assert.throws(() => { game[key] = null; }, TypeError);
  }
  for (const key of ['spawn', 'fits', 'cells', 'render']) assert.equal(game[key], undefined);
  assert.deepEqual(game.snapshot(), original);
  assert.equal(game.move(10), false);
  assert.equal(game.move(0.5), false);
  assert.deepEqual(game.snapshot(), original);
});

test('movement respects walls and naturally occupied cells', () => {
  const game = new Game(() => 0);
  moveTo(game, 0);
  assert.equal(game.move(-1), false);
  moveTo(game, 8);
  assert.equal(game.move(1), false);
  game.drop();
  moveTo(game, 6);
  for (let i = 0; i < 18; i++) assert.equal(game.tick(), true);
  assert.equal(game.move(1), false);
});

test('all seven tetrominoes have four cells and rotate through a full cycle', () => {
  for (let index = 0; index < 7; index++) {
    const game = new Game(() => index / 7);
    const original = game.piece;
    assert.equal(cells(original).length, 4);
    for (let turn = 0; turn < 4; turn++) assert.equal(game.rotate(), true);
    assert.deepEqual(game.piece, original);
  }
});

test('rotation kicks at a wall and rejects a floor collision', () => {
  const game = new Game(() => 1 / 7);
  game.rotate();
  while (game.move(-1)) {}
  assert.equal(game.piece.x, -2);
  assert.equal(game.rotate(), true);
  assert.ok(cells(game.piece).every(([x]) => x >= 0));
  for (let i = 0; i < 17; i++) assert.equal(game.tick(), true);
  const original = game.piece;
  assert.equal(game.rotate(), false);
  assert.deepEqual(game.piece, original);
});

test('gravity locks at floor and spawns a fresh piece', () => {
  const game = new Game(() => 0);
  for (let i = 0; i < 18; i++) assert.equal(game.tick(), true);
  assert.equal(game.piece.y, 18);
  assert.equal(game.tick(), false);
  assert.equal(game.board.flat().filter(Boolean).length, 4);
  assert.equal(game.piece.y, 0);
  assert.equal(game.score, 0);
});

test('a dropped piece lands on the stack without overwriting it', () => {
  const game = new Game(() => 0);
  game.drop();
  game.drop();
  assert.equal(game.board[16][4], true);
  assert.equal(game.board[19][5], true);
  assert.equal(game.board.flat().filter(Boolean).length, 8);
});

for (const [lines, score] of [[1, 100], [2, 300], [3, 500], [4, 800]]) {
  test(`clears ${lines} lines through gameplay and awards ${score} points`, () => {
    const game = new Game(() => 1 / 7);
    // Build eight-wide rows with horizontal I pieces, then fill both gaps
    // using vertical I pieces. No board or score injection is needed.
    for (let i = 0; i < lines; i++) {
      for (const x of [0, 4]) {
        moveTo(game, x);
        game.drop();
      }
    }
    for (const x of [6, 7]) {
      game.rotate();
      moveTo(game, x); // A vertical I occupies x + 2.
      game.drop();
    }
    assert.equal(game.score, score);
    assert.equal(game.board.length, 20);
    assert.ok(game.board.every(row => row.length === 10 && !row.every(Boolean)));
    assert.equal(game.board.flat().filter(Boolean).length, 8 - 2 * lines);
    assert.ok(game.board.slice(0, 16 + lines).every(row => row.every(cell => !cell)));
    game.drop();
    assert.equal(game.score, score);
  });
}

test('blocked spawn ends the game and freezes all gameplay operations', () => {
  const game = new Game(() => 0);
  for (let i = 0; i < 10; i++) game.drop();
  assert.equal(game.gameOver, true);
  const state = game.snapshot();
  assert.equal(game.move(-1), false);
  assert.equal(game.rotate(), false);
  assert.equal(game.tick(), false);
  game.drop();
  assert.deepEqual(game.snapshot(), state);
});
