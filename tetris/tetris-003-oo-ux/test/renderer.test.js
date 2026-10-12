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
