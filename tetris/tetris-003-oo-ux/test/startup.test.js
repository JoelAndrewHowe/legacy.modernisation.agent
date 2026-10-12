import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { Game } from '../src/game.js';
import { Terminal } from '../src/terminal.js';
import { renderGame } from '../src/renderer.js';

function fixture(game = new Game()) {
  const input = new EventEmitter();
  input.isTTY = true;
  input.isRaw = false;
  input.setRawMode = raw => { input.isRaw = raw; };
  input.resume = () => { input.paused = false; };
  input.pause = () => { input.paused = true; };
  let output = '';
  const terminal = new Terminal(game, input, {
    isTTY: true,
    write: text => { output += text; },
  });
  return { input, terminal, output: () => output };
}

test('initial display includes board, score, and controls within 24 rows', () => {
  const rows = renderGame(new Game(() => 0).snapshot()).split('\n');
  assert.equal(rows.length, 24);
  assert.ok(rows.every(row => Array.from(row).length <= 22));
  assert.match(rows[0], /TETRIS  Score: 0/);
  assert.match(rows.join('\n'), /\[\]\[\]/);
  assert.match(rows.at(-1), /Space Q\/\^C/);
});

test('npm start prints the initial display when not attached to a terminal', () => {
  const result = spawnSync('npm', ['start', '--silent'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const rows = result.stdout.trimEnd().split('\n');
  assert.equal(rows.length, 24);
  assert.match(rows[0], /TETRIS  Score: 0/);
  assert.equal((result.stdout.match(/\[\]/g) || []).length, 4);
});

test('starting twice does not duplicate timers or terminal handlers', () => {
  const { input, terminal, output } = fixture();
  const signals = ['SIGINT', 'SIGTERM'].map(s => process.listenerCount(s));
  try {
    terminal.start();
    const timer = terminal.timer;
    const firstOutput = output();
    terminal.start();
    assert.equal(terminal.timer, timer);
    assert.equal(output(), firstOutput);
    assert.equal(input.listenerCount('keypress'), 1);
    assert.deepEqual(
      ['SIGINT', 'SIGTERM'].map(s => process.listenerCount(s)),
      signals.map(count => count + 1),
    );
  } finally {
    terminal.stop();
  }
});

for (const inputTTY of [false, true]) {
  test(`redirected startup does not enable raw mode or timers (input TTY ${inputTTY})`, () => {
    const { input, terminal, output } = fixture();
    input.isTTY = inputTTY;
    terminal.output.isTTY = !inputTTY;
    const signals = ['SIGINT', 'SIGTERM'].map(s => process.listenerCount(s));
    try {
      terminal.start();
      assert.equal(terminal.running, false);
      assert.equal(terminal.timer, undefined);
      assert.equal(input.isRaw, false);
      assert.equal(input.paused, undefined);
      assert.equal(input.listenerCount('keypress'), 0);
      assert.deepEqual(['SIGINT', 'SIGTERM'].map(s => process.listenerCount(s)), signals);
      assert.equal(output(), `${renderGame(terminal.game.snapshot())}\n`);
      assert.ok(!output().includes('\x1b'));
      const preview = output();
      terminal.stop();
      assert.equal(output(), preview);
    } finally {
      terminal.stop();
    }
  });
}

for (const wasRaw of [false, true]) {
  for (const exit of ['q', 'ctrl-c', 'SIGINT', 'SIGTERM']) {
    test(`${exit} restores terminal state (initial raw mode ${wasRaw})`, () => {
      const { input, terminal, output } = fixture();
      input.isRaw = wasRaw;
      const signals = ['SIGINT', 'SIGTERM'].map(s => process.listenerCount(s));
      try {
        terminal.start();
        assert.equal(input.isRaw, true);
        assert.match(output(), /TETRIS/);
        const timer = terminal.timer;
        if (exit.startsWith('SIG')) process.emit(exit);
        else input.emit('keypress', '', exit === 'q' ? { name: 'q' } : { name: 'c', ctrl: true });
        assert.equal(input.isRaw, wasRaw);
        assert.equal(input.paused, true);
        assert.equal(terminal.running, false);
        assert.equal(input.listenerCount('keypress'), 0);
        assert.deepEqual(['SIGINT', 'SIGTERM'].map(s => process.listenerCount(s)), signals);
        assert.equal(terminal.timer, undefined);
        assert.equal(timer._destroyed, true);
        assert.ok(output().endsWith('\x1b[?25h\x1b[?1049l'));
        const restored = output();
        terminal.stop();
        assert.equal(output(), restored);
      } finally {
        terminal.stop();
      }
    });
  }
}

test('interactive keys move, rotate, fall, and drop, and redraw', () => {
  const game = new Game(() => 2 / 7);
  const { input, terminal, output } = fixture(game);
  try {
    terminal.start();
    const x = game.piece.x;
    input.emit('keypress', '', { name: 'left' });
    assert.equal(game.piece.x, x - 1);
    input.emit('keypress', '', { name: 'right' });
    assert.equal(game.piece.x, x);
    const shape = game.piece.shape;
    input.emit('keypress', '', { name: 'up' });
    assert.notDeepEqual(game.piece.shape, shape);
    input.emit('keypress', '', { name: 'down' });
    assert.equal(game.piece.y, 1);
    input.emit('keypress', '', { name: 'space' });
    assert.equal(game.board.flat().filter(Boolean).length, 4);
    assert.equal(game.piece.y, 0);
    assert.ok(output().split('\x1b[H').length >= 7);
  } finally {
    terminal.stop();
  }
});

test('automatic gravity falls and stops at game over', async () => {
  const game = new Game(() => 0);
  const { terminal, output } = fixture(game);
  try {
    terminal.start();
    await new Promise(resolve => setTimeout(resolve, 550));
    assert.equal(game.piece.y, 1);
    for (let i = 0; i < 10; i++) game.drop();
    terminal.draw();
    assert.equal(game.gameOver, true);
    assert.equal(terminal.timer, undefined);
    assert.match(output(), /GAME OVER/);
  } finally {
    terminal.stop();
  }
});
