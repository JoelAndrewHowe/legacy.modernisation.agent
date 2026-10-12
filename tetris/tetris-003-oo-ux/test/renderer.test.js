import assert from 'node:assert/strict';
import test from 'node:test';
import { Game } from '../src/game.js';
import { renderGame } from '../src/renderer.js';

test('real game-over display fits 24 rows and includes score and quit help', () => {
  const game = new Game(() => 0);
  for (let i = 0; i < 10; i++) game.drop();
  const state = game.snapshot();
  const rows = renderGame(state).split('\n');
  assert.equal(rows.length, 24);
  assert.ok(rows.every(row => Array.from(row).length <= 22));
  assert.equal(rows[0], 'GAME OVER Score:0');
  assert.equal(rows.at(-1), 'Q / Ctrl-C: quit');
  assert.deepEqual(game.snapshot(), state);
});

test('board borders and cell positions stay inside the 24-row frame', () => {
  const snapshot = new Game(() => 0).snapshot();
  const board = snapshot.board.map((row, y) => row.map((_, x) =>
    (y === 0 && x === 0) || (y === 19 && x === 9)));
  const view = { ...snapshot, board, piece: { shape: [[1]], x: 5, y: 10 } };
  const original = structuredClone(view);
  const rows = renderGame(view).split('\n');
  assert.equal(rows.length, 24);
  assert.equal(rows[1], '+--------------------+');
  assert.equal(rows[22], rows[1]);
  for (const row of rows.slice(2, 22)) {
    assert.equal(row.length, 22);
    assert.ok(row.startsWith('|') && row.endsWith('|'));
  }
  assert.equal(rows[2], `|[]${'  '.repeat(9)}|`);
  assert.equal(rows[12], `|${'  '.repeat(5)}[]${'  '.repeat(4)}|`);
  assert.equal(rows[21], `|${'  '.repeat(9)}[]|`);
  assert.equal(rows[23], '←→ ↑ ↓ Space Q/^C');
  assert.deepEqual(view, original);

  const ended = renderGame({ ...view, gameOver: true }).split('\n');
  assert.equal(ended.length, 24);
  assert.equal(ended[12], `|${'  '.repeat(10)}|`);
  assert.equal(ended[2], rows[2]);
  assert.equal(ended[21], rows[21]);
  assert.equal(ended[0], 'GAME OVER Score:0');
  assert.equal(ended[23], 'Q / Ctrl-C: quit');
});

test('all seven pieces and rotations retain the compact display layout', () => {
  for (let index = 0; index < 7; index++) {
    const game = new Game(() => index / 7);
    for (let rotation = 0; rotation < 4; rotation++) {
      const rows = renderGame(game.snapshot()).split('\n');
      assert.equal(rows.length, 24);
      assert.ok(rows.every(row => Array.from(row).length <= 22));
      assert.equal((rows.slice(2, 22).join('').match(/\[\]/g) || []).length, 4);
      game.rotate();
    }
  }
});

test('renderer formats large scores without changing domain state', () => {
  const snapshot = new Game(() => 0).snapshot();
  // Presentation fixture only: no live game state is changed.
  for (const gameOver of [false, true]) {
    const view = { ...snapshot, score: 123456789, gameOver };
    const original = structuredClone(view);
    const rows = renderGame(view).split('\n');
    assert.equal(rows.length, 24);
    assert.ok(rows.every(row => Array.from(row).length <= 22));
    assert.match(rows[0], /1e\+8/);
    assert.deepEqual(view, original);
  }
});
