import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { TetrisApplication } from '../src/application.js';
import { Terminal } from '../src/terminal.js';
import { Board, Piece, TetrisGame } from '../src/game.js';

function fixture(game = new TetrisGame()) {
  const input = new EventEmitter();
  Object.assign(input, {
    isTTY: true,
    isRaw: false,
    setRawMode(value) { this.isRaw = value; },
    resume() {},
    pause() {},
  });
  const writes = [];
  const output = { isTTY: true, write: (text) => writes.push(text) };
  const signals = new EventEmitter();
  const pending = new Map();
  let nextId = 0;
  const timers = {
    setTimeout(callback, delay) {
      pending.set(++nextId, { callback, delay });
      return nextId;
    },
    clearTimeout(id) { pending.delete(id); },
    advance() {
      const [id, { callback }] = pending.entries().next().value;
      pending.delete(id);
      callback();
    },
  };
  return { input, writes, signals, game, pending, timers,
    app: new TetrisApplication(new Terminal(input, output), signals, { game, timers }) };
}

test('startup displays a 24-row board and quit restores terminal state', () => {
  const { app, input, writes, signals } = fixture();
  app.start();
  assert.equal(input.isRaw, true);
  assert.equal(writes[1].split('\n').length, 24);
  assert.match(writes[1], /TETRIS/);
  input.emit('keypress', 'q', { name: 'q' });
  assert.equal(input.isRaw, false);
  assert.equal(input.listenerCount('keypress'), 0);
  assert.equal(signals.listenerCount('SIGINT'), 0);
  assert.equal(writes.at(-1), '\x1b[?25h\x1b[?1049l');
  app.stop();
  assert.equal(writes.length, 3);
});

for (const signal of ['SIGINT', 'SIGTERM', 'exit']) {
  test(`${signal} restores the terminal`, () => {
    const { app, input, signals } = fixture();
    app.start();
    signals.emit(signal);
    assert.equal(input.isRaw, false);
    assert.equal(input.listenerCount('keypress'), 0);
  });
}

test('keyboard controls move, rotate, drop, and render active and locked pieces', () => {
  const game = new TetrisGame({ source: { next: () => 'T' } });
  const { app, input, writes } = fixture(game);
  app.start();
  const press = (name) => input.emit('keypress', '', { name });
  assert.equal((writes.at(-1).match(/\[\]/g) ?? []).length, 4);
  const original = game.active;
  press('left');
  assert.equal(game.active.x, original.x - 1);
  press('right');
  assert.equal(game.active.x, original.x);
  press('up');
  assert.notDeepEqual(game.active.matrix, original.matrix);
  press('down');
  assert.equal(game.active.y, 1);
  assert.equal(game.score, 1);
  press('space');
  assert.equal(game.active.y, 0);
  assert.equal(game.board.rows.flat().filter(Boolean).length, 4);
  assert.equal((writes.at(-1).match(/\[\]/g) ?? []).length, 8);
  assert.match(writes.at(-1), new RegExp(`Score: ${game.score}`));
  assert.equal(writes.at(-1).split('\n').length, 24);
  app.stop();
});

test('gravity ticks automatically and stops on quit', () => {
  const { app, game, pending, timers, input } = fixture();
  app.start();
  app.start();
  assert.equal(pending.size, 1);
  assert.equal([...pending.values()][0].delay, game.gravityInterval);
  const y = game.active.y;
  timers.advance();
  assert.equal(game.active.y, y + 1);
  assert.equal(pending.size, 1);
  input.emit('keypress', '', { ctrl: true, name: 'c' });
  assert.equal(pending.size, 0);
});

test('game over cancels gravity and displays its message within 24 rows', () => {
  const rows = Array.from({ length: 20 }, () => Array(10).fill(null));
  rows[0][4] = 'T';
  const game = new TetrisGame({
    board: new Board(10, 20, rows), source: { next: () => 'O' },
    initialState: { active: new Piece('O', 0, 18) },
  });
  const { app, pending, input, writes } = fixture(game);
  app.start();
  input.emit('keypress', '', { name: 'space' });
  assert.equal(game.gameOver, true);
  assert.equal(pending.size, 0);
  assert.match(writes.at(-1), /GAME OVER/);
  assert.equal(writes.at(-1).split('\n').length, 24);
  const count = writes.length;
  input.emit('keypress', '', { name: 'left' });
  assert.equal(writes.length, count);
  input.emit('keypress', '', { name: 'q' });
  assert.equal(input.isRaw, false);
});

test('gravity uses the new level interval after a line clear', () => {
  const rows = Array.from({ length: 20 }, () => Array(10).fill(null));
  rows[19].fill('T', 2);
  const game = new TetrisGame({
    board: new Board(10, 20, rows), source: { next: () => 'O' },
    initialState: { active: new Piece('O', 0, 18), lines: 9 },
  });
  const { app, pending, timers } = fixture(game);
  app.start();
  timers.advance();
  assert.equal(game.level, 2);
  assert.equal([...pending.values()][0].delay, 900);
  app.stop();
});

test('non-interactive startup fails clearly without terminal escape sequences', () => {
  const result = spawnSync(process.execPath, ['src/index.js'], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /requires an interactive terminal/);
  assert.equal(result.stdout, '');
});
