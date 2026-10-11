import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import test from 'node:test';
import { Game } from '../src/game.js';
import { renderGame, start } from '../src/index.js';

function terminal(game) {
  const input = Object.assign(new EventEmitter(), {
    isTTY: true, isRaw: false,
    setRawMode(value) { this.isRaw = value; }, resume() {}, pause() {},
  });
  const frames = [];
  const output = Object.assign(new EventEmitter(), {
    isTTY: true, rows: 24, columns: 80,
    write(text) { frames.push(text); },
  });
  let tick;
  const stop = start({ input, output, game,
    schedule(fn) { tick = fn; return fn; },
    cancel() { tick = undefined; },
  });
  return { input, output, frames, stop,
    key(name) { input.emit('keypress', '', { name }); },
    tick() { assert.ok(tick); tick(); },
    get pending() { return Boolean(tick); },
  };
}

test('live and game-over displays include pieces, score and controls in 24 rows', () => {
  const game = new Game();
  assert.match(renderGame(game), /\[\]/);
  assert.match(renderGame(game), /Space: slam/);
  game.gameOver = true;
  game.score = 123;
  const frame = renderGame(game);
  assert.equal(frame.split('\n').length, 24);
  assert.match(frame, /Score: 123/);
  assert.match(frame, /GAME OVER.*R: restart.*quit/);
});

test('keyboard controls move, rotate, drop and gravity advances independently', () => {
  const game = new Game({ random: () => 0 });
  const tty = terminal(game);
  try {
    const x = game.active.x;
    tty.key('left');
    assert.equal(game.active.x, x - 1);
    tty.key('right');
    assert.equal(game.active.x, x);
    const matrix = JSON.stringify(game.active.matrix);
    tty.key('up');
    assert.notEqual(JSON.stringify(game.active.matrix), matrix);
    tty.key('z');
    assert.equal(JSON.stringify(game.active.matrix), matrix);
    const y = game.active.y;
    tty.key('down');
    assert.equal(game.active.y, y + 1);
    assert.equal(game.score, 1);
    tty.tick();
    assert.equal(game.active.y, y + 2);
    tty.key('space');
    assert.ok(game.board.some(row => row.some(Boolean)));
    assert.ok(game.score > 1);
    assert.ok(tty.frames.at(-1).includes(`Score: ${game.score}`));
  } finally { tty.stop(); }
  assert.equal(tty.pending, false);
  assert.equal(tty.output.listenerCount('resize'), 0);
});

test('game over stops gravity, ignores movement and allows restart', () => {
  const game = new Game();
  game.gameOver = true;
  const tty = terminal(game);
  try {
    assert.equal(tty.pending, false);
    tty.key('left');
    assert.match(tty.frames.at(-1), /GAME OVER/);
    tty.key('r');
    assert.equal(tty.pending, true);
    assert.ok(!tty.frames.at(-1).includes('GAME OVER'));
    tty.key('q');
    assert.equal(tty.input.isRaw, false);
    assert.equal(tty.pending, false);
  } finally { tty.stop(); }
});

test('narrow terminals never wrap and undersized terminals show a resize notice', () => {
  const tty = terminal(new Game());
  try {
    for (const [columns, rows] of [[22, 24], [80, 10], [15, 24]]) {
      Object.assign(tty.output, { columns, rows });
      tty.output.emit('resize');
      const frame = tty.frames.at(-1).replace(/\x1b\[[0-9;]*[A-Za-z]/g, '');
      assert.ok(frame.split('\r\n').length <= rows);
      assert.ok(frame.split('\r\n').every(line => Array.from(line).length <= columns));
      if (rows < 24 || columns < 22) assert.match(frame, /Resize terminal/);
    }
  } finally { tty.stop(); }
});
