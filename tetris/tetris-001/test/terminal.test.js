import test from 'node:test';
import assert from 'node:assert/strict';
import { Game } from '../src/game.js';
import { renderFrame, startTerminal } from '../src/terminal.js';

const game = () => new Game({ random: () => 0.5 });

test('entire display, including controls and status, fits 24 rows', () => {
  const g = game();
  for (const state of ['playing', 'paused', 'over']) {
    g.gameOver = state === 'over';
    const frame = renderFrame(g, { paused: state === 'paused' });
    const rows = frame.split('\n');
    assert.equal(rows.length, 24);
    assert.ok(rows.every(row => row.length <= 52));
    assert.match(frame, /Score: 0/);
    assert.match(frame, /Space: hard drop/);
    assert.match(frame, /Q or Ctrl-C: quit/);
    if (state === 'over') assert.match(rows[23], /GAME OVER/);
    if (state === 'paused') assert.match(rows[23], /PAUSED/);
  }
});

test('render overlays active blocks without changing the board', () => {
  const g = game();
  const before = structuredClone(g.board);
  assert.match(renderFrame(g), /\[\]/);
  assert.deepEqual(g.board, before);
  g.gameOver = true;
  assert.doesNotMatch(renderFrame(g), /\[\]/);
});

test('non-interactive startup reports the terminal requirement', () => {
  let message = '';
  assert.equal(startTerminal({ input: { isTTY: false }, output: {
    isTTY: false,
    write: text => { message += text; },
  } }), false);
  assert.match(message, /requires an interactive terminal/);
});
