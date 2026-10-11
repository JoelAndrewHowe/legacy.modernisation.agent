import assert from 'node:assert/strict';
import test from 'node:test';
import { Board, Piece, PieceBag, TetrisGame } from '../src/game.js';

const emptyRows = () => Array.from({ length: 20 }, () => Array(10).fill(null));
const gameWith = (type = 'O', board = new Board(), initialState = {}) =>
  new TetrisGame({ board, source: { next: () => type }, initialState });
const stateOf = (game) => ({ rows: game.board.rows, active: game.active,
  score: game.score, lines: game.lines, gameOver: game.gameOver });

test('each bag contains all seven four-cell pieces', () => {
  const bag = new PieceBag(() => 0.5);
  for (let round = 0; round < 3; round++) {
    const types = Array.from({ length: 7 }, () => bag.next());
    assert.deepEqual([...types].sort(), ['I', 'J', 'L', 'O', 'S', 'T', 'Z']);
    for (const type of types) {
      const piece = new Piece(type);
      assert.equal(piece.cells().length, 4);
      let rotated = piece;
      for (let i = 0; i < 4; i++) rotated = rotated.rotated();
      assert.deepEqual(rotated, piece);
    }
  }
});

test('movement rejects walls, floor and occupied cells without changing the piece', () => {
  const rows = emptyRows();
  rows[2][0] = 'T';
  const game = gameWith('O', new Board(10, 20, rows));
  assert.equal(game.active.x, 4);
  while (game.move(-1)) {}
  assert.equal(game.active.x, 0);
  const before = game.active;
  assert.equal(game.move(-1), false);
  assert.equal(game.active, before);
  assert.equal(game.move(0, 1), false);
  assert.equal(game.board.fits(new Piece('O', 9, 0)), false);
  assert.equal(game.board.fits(new Piece('O', 0, 19)), false);
  assert.equal(game.board.fits(new Piece('O', 0, -1)), false);
});

test('rotation kicks away from walls and rejects blocked rotations', () => {
  const game = gameWith('T', new Board(), { active: new Piece('T', -1, 2).rotated() });
  assert.equal(game.board.fits(game.active), true);
  assert.equal(game.rotate(), true);
  assert.equal(game.active.x, 0);
  const before = game.active;
  const rows = emptyRows().map((row) => row.map(() => 'Z'));
  for (const { x, y } of before.cells()) rows[y][x] = null;
  const blocked = gameWith('T', new Board(10, 20, rows), { active: before });
  assert.equal(blocked.rotate(), false);
  assert.equal(blocked.active, before);
});

test('gravity locks at the floor and spawns another piece without drop points', () => {
  const game = gameWith();
  for (let i = 0; i < 18; i++) game.tick();
  assert.equal(game.active.y, 18);
  game.tick();
  assert.equal(game.active.y, 0);
  assert.equal(game.board.rows[19][4], 'O');
  assert.equal(game.score, 0);
});

test('soft and hard drops award distance points and lock pieces', () => {
  const game = gameWith();
  game.softDrop();
  assert.equal(game.score, 1);
  game.hardDrop();
  assert.equal(game.score, 35);
  assert.equal(game.board.rows[18][4], 'O');
  assert.equal(game.active.y, 0);
});

for (const [count, points] of [[1, 100], [2, 300], [3, 500], [4, 800]]) {
  test(`${count} simultaneous line clears score ${points} points`, () => {
    const rows = emptyRows();
    for (let y = 20 - count; y < 20; y++) rows[y].fill('Z');
    const game = gameWith('I', new Board(10, 20, rows), { active: new Piece('I', 0, 0) });
    game.lock();
    assert.equal(game.lines, count);
    assert.equal(game.score, points);
    assert.equal(game.board.rows.length, 20);
    assert.equal(game.board.rows[1 + count].filter(Boolean).length, 4);
    assert.equal(game.board.rows.at(-1).every((cell) => cell === null), true);
    assert.equal(game.board.rows[0].every((cell) => cell === null), true);
    assert.notEqual(game.board.rows[0], game.board.rows[1]);
  });
}

test('line clearing collapses rows and retains their order', () => {
  const board = new Board(4, 4, [['T', null, null, null], ['Z', 'Z', 'Z', 'Z'],
    [null, 'O', null, null], ['I', 'I', 'I', 'I']]);
  assert.equal(board.clearLines(), 2);
  assert.deepEqual(board.rows, [[null, null, null, null], [null, null, null, null],
    ['T', null, null, null], [null, 'O', null, null]]);
});

test('levels increase gravity speed and multiply line-clear scores', () => {
  const rows = emptyRows();
  rows[19].fill('Z');
  const game = gameWith('I', new Board(10, 20, rows), { lines: 9 });
  game.lock();
  assert.equal(game.level, 2);
  assert.equal(game.score, 100);
  assert.equal(game.gravityInterval, 900);
  const next = gameWith('I', new Board(10, 20, rows), {
    lines: game.lines, score: game.score,
  });
  next.lock();
  assert.equal(next.score, 300);
  assert.equal(gameWith('I', new Board(), { lines: 1000 }).gravityInterval, 100);
});

test('blocked spawn ends the game and all gameplay actions become no-ops', () => {
  const rows = emptyRows();
  rows[0][4] = 'Z';
  const board = new Board(10, 20, rows);
  const game = gameWith('O', board);
  assert.equal(game.gameOver, true);
  const snapshot = stateOf(game);
  for (const action of [() => game.move(1), () => game.rotate(), () => game.tick(),
    () => game.softDrop(), () => game.hardDrop()]) assert.equal(action(), false);
  game.lock();
  assert.deepEqual(stateOf(game), snapshot);
});

test('invariant-bearing state is read-only and snapshots cannot alter gameplay', () => {
  const game = gameWith();
  const before = stateOf(game);
  for (const mutate of [
    () => { game.active = new Piece('I'); },
    () => { game.active.x = -10; },
    () => { game.active.matrix = [[1]]; },
    () => { game.active.matrix[0][0] = 0; },
    () => { game.score = 999; },
    () => { game.lines = 999; },
    () => { game.gameOver = true; },
    () => { game.board = new Board(); },
    () => { game.board.rows[0][0] = 'Z'; },
    () => { game.board.rows = []; },
    () => { game.board.width = 1; },
  ]) assert.throws(mutate, TypeError);
  assert.equal(game.board.lock, undefined);
  assert.equal(game.board.clearLines, undefined);
  assert.deepEqual(stateOf(game), before);
  const view = game.board;
  game.hardDrop();
  assert.equal(view.rows[19][4], null);
  assert.equal(game.board.rows[19][4], 'O');
});

test('fixture inputs are copied and validated', () => {
  const rows = emptyRows();
  const board = new Board(10, 20, rows);
  const game = gameWith('O', board);
  rows[0][4] = 'Z';
  board.lock(new Piece('O', 4, 0));
  assert.equal(game.board.rows[0][4], null);
  assert.equal(game.move(0, 1), true);
  assert.throws(() => { board.rows[0][0] = 'T'; }, TypeError);
  assert.throws(() => { board.rows = rows; }, TypeError);
  assert.throws(() => { board.width = 1; }, TypeError);
  assert.throws(() => new Board(10, 20, []), /Invalid board rows/);
  const invalid = emptyRows();
  invalid[0][0] = 'unknown';
  assert.throws(() => new Board(10, 20, invalid), /Invalid board rows/);
  assert.throws(() => new Piece('T', 0, 0, [[1]]), /Invalid tetromino/);
  assert.throws(() => new Piece('T', 0.5, 0), /coordinates/);
  for (const initialState of [{ score: -1 }, { lines: 0.5 }, { score: NaN },
    { active: new Piece('O', 9, 0) }, { active: {} }]) {
    assert.throws(() => gameWith('O', new Board(), initialState));
  }
});

test('a lock that obstructs the next spawn triggers game over', () => {
  const game = gameWith();
  game.lock();
  assert.equal(game.gameOver, true);
});
