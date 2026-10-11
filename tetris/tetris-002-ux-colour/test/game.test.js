import assert from 'node:assert/strict';
import test from 'node:test';
import { Game } from '../src/game.js';
import { renderGame } from '../src/terminal.js';

test('seven-piece bag supplies every tetromino and valid spawning', () => {
  const game = new Game(() => 0.5);
  const types = new Set();
  for (let i = 0; i < 7; i++) {
    types.add(game.piece.type);
    assert.equal(game.fits(game.piece), true);
    game.spawn();
  }
  assert.equal(types.size, 7);
});

test('movement and rotation cannot cross walls, floor or settled blocks', () => {
  const game = new Game();
  game.piece = { type: 'T', x: 0, y: 0, cells: [[1, 0], [0, 1], [1, 1], [2, 1]] };
  assert.equal(game.move(-1), false);
  game.board[1][3] = 'O';
  assert.equal(game.move(1), false);
  assert.equal(game.rotate(), true);
  assert.equal(game.fits(game.piece), true);
  game.hardDrop();
  assert.equal(game.board.flat().filter(Boolean).length, 5);
  assert.ok(game.score > 0);
  assert.equal(game.piece.y, 0);
});

test('line clearing updates score, lines, level, speed and visible status', () => {
  const game = new Game();
  game.lines = 9;
  game.board[19].fill('J');
  game.board[19][4] = null;
  game.board[19][5] = null;
  game.piece = { type: 'O', x: 3, y: 18, cells: [[1, 0], [2, 0], [1, 1], [2, 1]] };
  game.drop();
  assert.equal(game.score, 100);
  assert.equal(game.lines, 10);
  assert.equal(game.level, 2);
  assert.equal(game.fallDelay, 740);
  assert.equal(game.board.flat().filter(Boolean).length, 2);
  assert.match(renderGame(game, { env: { NO_COLOR: '' } }), /Score: 100.*Lines: 10.*Level: 2/);
});

test('four-line clear earns a Tetris bonus', () => {
  const game = new Game();
  for (let y = 16; y < 20; y++) {
    game.board[y].fill('T');
    game.board[y][4] = null;
  }
  game.piece = { type: 'I', x: 4, y: 16, cells: [[0, 0], [0, 1], [0, 2], [0, 3]] };
  game.drop();
  assert.equal(game.lines, 4);
  assert.equal(game.score, 800);
  assert.ok(game.board.flat().every(cell => !cell));
});

test('automatic drops fall without points, lock on the floor, and spawn the next piece', () => {
  const game = new Game(() => 0.5);
  game.piece = { type: 'O', x: 3, y: 17, cells: [[1, 0], [2, 0], [1, 1], [2, 1]] };
  game.bag = ['T'];
  game.drop();
  assert.equal(game.piece.y, 18);
  assert.equal(game.score, 0);
  assert.equal(game.move(0, 1), false);
  game.drop();
  assert.deepEqual(game.board[18].slice(4, 6), ['O', 'O']);
  assert.deepEqual(game.board[19].slice(4, 6), ['O', 'O']);
  assert.equal(game.piece.type, 'T');
  assert.equal(game.piece.y, 0);
  assert.equal(game.score, 0);
});

test('four rotations restore each rotating tetromino and O stays unchanged', () => {
  const game = new Game(() => 0.5);
  const sorted = cells => cells.map(cell => cell.join(',')).sort();
  for (let i = 0; i < 7; i++) {
    const original = structuredClone(game.piece);
    for (let turn = 0; turn < 4; turn++) {
      assert.equal(game.rotate(), original.type !== 'O');
      assert.equal(game.fits(game.piece), true);
    }
    assert.deepEqual(sorted(game.piece.cells), sorted(original.cells));
    assert.equal(game.piece.x, original.x);
    assert.equal(game.piece.y, original.y);
    game.spawn();
  }
});

test('rotation kicks away from walls and rejects fully blocked rotations', () => {
  const game = new Game();
  game.piece = { type: 'I', x: -2, y: 4, cells: [[2, 0], [2, 1], [2, 2], [2, 3]] };
  assert.equal(game.fits(game.piece), true);
  assert.equal(game.rotate(), true);
  assert.equal(game.piece.x, 0);
  assert.equal(game.fits(game.piece), true);

  game.piece = { type: 'T', x: 3, y: 4, cells: [[1, 0], [0, 1], [1, 1], [2, 1]] };
  game.board = game.board.map(row => row.map(() => 'J'));
  for (const [dx, dy] of game.piece.cells) game.board[game.piece.y + dy][game.piece.x + dx] = null;
  const before = structuredClone(game.piece);
  assert.equal(game.rotate(), false);
  assert.deepEqual(game.piece, before);
});

for (const [count, bonus] of [[2, 300], [3, 500]]) {
  test(`${count}-line clear scores at the current level and preserves unfilled rows`, () => {
    const game = new Game();
    game.lines = 10;
    game.level = 2;
    game.board[10][0] = 'J';
    for (let y = 20 - count; y < 20; y++) {
      game.board[y].fill('Z');
      game.board[y][4] = null;
    }
    game.piece = { type: 'I', x: 4, y: 16, cells: [[0, 0], [0, 1], [0, 2], [0, 3]] };
    game.drop();
    assert.equal(game.score, bonus * 2);
    assert.equal(game.lines, 10 + count);
    assert.equal(game.board[10 + count][0], 'J');
    assert.equal(game.board.flat().filter(Boolean).length, 5 - count);
    assert.ok(game.board.slice(0, count).flat().every(cell => cell === null));
  });
}

test('blocked spawn ends game, freezes controls, and restart resets it', () => {
  const game = new Game();
  game.board[0].fill('Z');
  game.board[1].fill('Z');
  game.bag = ['O'];
  game.spawn();
  assert.equal(game.over, true);
  assert.match(renderGame(game, { env: { NO_COLOR: '1' } }), /GAME OVER.*R restart.*quit/);
  const before = JSON.stringify(game);
  game.move(1); game.rotate(); game.drop(); game.hardDrop();
  assert.equal(JSON.stringify(game), before);
  game.restart();
  assert.equal(game.over, false);
  assert.equal(game.lines, 0);
  assert.equal(game.level, 1);
  assert.equal(game.score, 0);
});
