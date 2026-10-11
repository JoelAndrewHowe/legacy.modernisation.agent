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
