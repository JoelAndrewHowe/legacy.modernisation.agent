import assert from 'node:assert/strict';
import test from 'node:test';
import { Board, Piece, PieceBag, TetrisGame } from '../src/tetris.js';

const emptyRows = () => Array.from({ length: 20 }, () => Array(10).fill(null));
const gameWith = (type = 'O', board = new Board(), initialState = {}) =>
  new TetrisGame({ board, pieces: { next: () => type }, initialState });

test('seven-bag contains each tetromino once per refill', () => {
  const bag = new PieceBag(() => 0.5);
  for (let round = 0; round < 3; round++) {
    const types = Array.from({ length: 7 }, () => bag.next());
    assert.equal(new Set(types).size, 7);
    for (const type of types) {
      const piece = new Piece(type);
      assert.equal(piece.cells().length, 4);
      let rotated = piece;
      for (let i = 0; i < 4; i++) rotated = rotated.rotated();
      assert.deepEqual(rotated.shape, piece.shape);
      assert.deepEqual(piece.rotated().rotated(false).shape, piece.shape);
    }
  }
});

test('bag contents and random source cannot be exposed or replaced', () => {
  const bag = new PieceBag(() => 0.5);
  const control = new PieceBag(() => 0.5);
  assert.equal(bag.bag, undefined);
  assert.equal(bag.random, undefined);
  assert.throws(() => bag.bag.push('invalid'), TypeError);
  assert.throws(() => { bag.bag = ['invalid']; }, TypeError);
  assert.throws(() => { bag.random = () => NaN; }, TypeError);
  assert.throws(() => { bag.next = () => 'invalid'; }, TypeError);
  for (let i = 0; i < 21; i++) assert.equal(bag.next(), control.next());
});

test('retaining an injected bag cannot corrupt future game spawns', () => {
  const bag = new PieceBag(() => 0.5);
  const control = new PieceBag(() => 0.5);
  const game = new TetrisGame({ board: new Board(10, 100), pieces: bag });
  assert.throws(() => { bag.bag = ['invalid']; }, TypeError);
  assert.throws(() => { bag.random = () => NaN; }, TypeError);
  assert.throws(() => { bag.next = () => 'invalid'; }, TypeError);
  for (let i = 0; i < 21; i++) {
    assert.equal(game.gameOver, false);
    assert.equal(game.active.type, control.next());
    game.hardDrop();
  }
});

test('movement stops at walls and occupied cells without changing state', () => {
  const game = gameWith();
  while (game.move(-1)) { /* reach wall */ }
  assert.equal(game.active.x, 0);
  const previous = game.active;
  assert.equal(game.move(-1), false);
  assert.equal(game.active, previous);
  const rows = emptyRows();
  rows[0][2] = 'T';
  const blocked = gameWith('O', new Board(10, 20, rows), { active: new Piece('O', 0, 0) });
  assert.equal(blocked.move(1), false);
  assert.equal(game.move(2), false);
});

test('rotation changes orientation, kicks at walls, and rejects blocked rotations', () => {
  const game = gameWith('T');
  const initial = game.active.shape;
  assert.equal(game.rotate(), true);
  assert.notDeepEqual(game.active.shape, initial);
  const wallGame = gameWith('I');
  wallGame.rotate();
  while (wallGame.move(-1)) { /* vertical I can have a negative origin */ }
  assert.equal(wallGame.rotate(), true);
  assert.equal(wallGame.board.fits(wallGame.active), true);

  const active = new Piece('T');
  const rows = emptyRows();
  const cells = new Set(active.cells().map(({ x, y }) => `${x},${y}`));
  for (let y = 0; y < 4; y++) {
    for (let x = 0; x < 10; x++) {
      if (!cells.has(`${x},${y}`)) rows[y][x] = 'J';
    }
  }
  const blocked = gameWith('T', new Board(10, 20, rows), { active });
  const previous = blocked.active;
  assert.equal(blocked.rotate(), false);
  assert.equal(blocked.active, previous);
});

test('gravity descends, locks at the floor, then spawns a fresh piece', () => {
  const game = gameWith();
  assert.equal(game.tick(), true);
  assert.equal(game.active.y, 1);
  assert.equal(game.score, 0);
  for (let i = 0; i < 18; i++) game.tick();
  assert.equal(game.active.y, 0);
  assert.equal(game.board.rows[19][4], 'O');
  assert.equal(game.board.rows[18][5], 'O');
});

test('soft drop scores one point per row; hard drop scores two and locks', () => {
  const game = gameWith();
  game.softDrop();
  assert.equal(game.score, 1);
  assert.equal(game.hardDrop(), 17);
  assert.equal(game.score, 35);
  assert.equal(game.active.y, 0);
  assert.equal(game.board.rows[19][4], 'O');
});

test('line clearing collapses remaining rows and adds empty rows at the top', () => {
  const rows = emptyRows();
  rows[17][0] = 'J';
  rows[18].fill('T');
  rows[19].fill('L');
  const board = new Board(10, 20, rows);
  assert.equal(board.clearLines(), 2);
  assert.equal(board.rows.length, 20);
  assert.equal(board.rows[19][0], 'J');
  assert.ok(board.rows[0].every(cell => cell === null));
  assert.notEqual(board.rows[0], board.rows[1]);
});

for (const [count, points] of [[1, 100], [2, 300], [3, 500], [4, 800]]) {
  test(`${count} cleared lines score ${points} times the current level`, () => {
    const rows = emptyRows();
    for (let y = 20 - count; y < 20; y++) {
      rows[y].fill('J');
      rows[y][5] = null;
    }
    const game = gameWith('I', new Board(10, 20, rows), {
      lines: 10, active: new Piece('I', 3, 16).rotated(),
    });
    game.tick();
    assert.equal(game.score, points * 2);
    assert.equal(game.lines, 10 + count);
  });
}

test('ten cleared lines increase level and speed, with bounded gravity', () => {
  const rows = emptyRows();
  rows[18].fill('T');
  rows[18][4] = rows[18][5] = null;
  rows[19][4] = 'T';
  const game = gameWith('O', new Board(10, 20, rows), {
    lines: 9, active: new Piece('O', 4, 17),
  });
  game.tick();
  assert.equal(game.level, 2);
  assert.equal(game.gravityInterval, 900);
  assert.equal(gameWith('O', new Board(), { lines: 1000 }).gravityInterval, 100);
});

test('blocked spawn ends the game and all gameplay input becomes inert', () => {
  const rows = emptyRows();
  rows[0][4] = 'J';
  const board = new Board(10, 20, rows);
  const game = gameWith('O', board);
  assert.equal(game.gameOver, true);
  const snapshot = () => JSON.stringify({
    rows: game.board.rows, active: game.active, score: game.score,
    lines: game.lines, gameOver: game.gameOver, nextType: game.nextType,
  });
  const before = snapshot();
  assert.equal(game.move(-1), false);
  assert.equal(game.rotate(), false);
  assert.equal(game.tick(), false);
  assert.equal(game.softDrop(), false);
  assert.equal(game.hardDrop(), 0);
  assert.equal(snapshot(), before);
});

test('locking cells above the board tops out without clearing lines or spawning', () => {
  const rows = emptyRows();
  rows[1][4] = 'J';
  const game = gameWith('O', new Board(10, 20, rows), { active: new Piece('O', 4, -1) });
  game.tick();
  assert.equal(game.gameOver, true);
  assert.equal(game.lines, 0);
});

test('gameplay state is read-only and constructor fixtures are isolated', () => {
  const rows = emptyRows();
  const board = new Board(10, 20, rows);
  const active = new Piece('O');
  const game = gameWith('O', board, { active, lines: 9, score: 42 });
  rows[0][0] = 'J';
  board.lock(new Piece('O', 0, 18));
  assert.equal(game.board.rows[19][0], null);
  assert.equal(board.rows[0][0], null);
  for (const mutate of [
    () => { board.rows[0][0] = 'J'; },
    () => { board.rows = rows; },
    () => { board.width = 1; },
    () => { game.board.rows[0].fill('J'); },
    () => { game.board = board; },
    () => { game.active = new Piece('I'); },
    () => { game.active.x = -100; },
    () => { game.active.shape[0][0] = 0; },
    () => { game.lines = 1000; },
    () => { game.score = 1000; },
    () => { game.gameOver = true; },
  ]) assert.throws(mutate, TypeError);
  assert.equal(game.lines, 9);
  assert.equal(game.score, 42);
  assert.equal(game.board.lock, undefined);
  assert.equal(game.spawn, undefined);
  assert.equal(game.lock, undefined);
});

test('initial-state setup rejects malformed boards, pieces, and counters', () => {
  assert.throws(() => new Board(0, 20), RangeError);
  assert.throws(() => new Board(10, 20, []), RangeError);
  const rows = emptyRows();
  rows[0][4] = 'invalid';
  assert.throws(() => new Board(10, 20, rows), RangeError);
  rows[0][4] = 'J';
  assert.throws(() => gameWith('O', new Board(10, 20, rows), {
    active: new Piece('O', 4, 0),
  }), RangeError);
  assert.throws(() => gameWith('O', new Board(), { active: new Piece('O', 0, 19) }), RangeError);
  assert.throws(() => gameWith('O', new Board(), { active: {} }), RangeError);
  for (const initialState of [{ lines: -1 }, { lines: 1.5 }, { score: NaN }, { gameOver: true }]) {
    assert.throws(() => gameWith('O', new Board(), initialState), RangeError);
  }
  assert.throws(() => new Piece('O', 0.5, 0), TypeError);
  assert.throws(() => new Piece('O', 0, 0, [[1]]), RangeError);
});

test('board rejects overlaps and floor crossings', () => {
  const board = new Board();
  assert.equal(board.fits(new Piece('O', 0, 19)), false);
  board.lock(new Piece('O', 0, 18));
  assert.equal(board.fits(new Piece('O', 0, 18)), false);
  assert.throws(() => board.lock(new Piece('O', 0, 18)), /overlapping/);
});
