import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import test from 'node:test';
import { TerminalGame, renderFrame } from '../src/terminal-game.js';
import { Board, Piece, TetrisGame } from '../src/tetris.js';

function terminal(createGame) {
  const input = new PassThrough();
  input.isTTY = true;
  input.isRaw = false;
  input.setRawMode = value => { input.isRaw = value; };
  input.pause();
  const output = new EventEmitter();
  Object.assign(output, { isTTY: true, rows: 24, columns: 80, text: '' });
  output.write = text => { output.text += text; };
  const signals = new EventEmitter();
  const timers = new Map();
  let id = 0;
  const adapter = new TerminalGame(output, {
    input, signals, createGame,
    setTimer: (callback, delay) => { timers.set(++id, { callback, delay }); return id; },
    clearTimer: timer => timers.delete(timer),
  });
  const key = name => input.emit('keypress', '', { name });
  const tick = () => {
    const [timer, { callback }] = timers.entries().next().value;
    timers.delete(timer);
    callback();
  };
  return { adapter, input, output, signals, timers, key, tick };
}

function assertRedraw(t, action) {
  const previousFrame = renderFrame(t.adapter.game);
  const offset = t.output.text.length;
  action();
  const expectedFrame = renderFrame(t.adapter.game);
  assert.notEqual(expectedFrame, previousFrame, 'fixture must visibly change');
  assert.equal(t.output.text.slice(offset),
    `\x1b[H\x1b[2J${expectedFrame.replaceAll('\n', '\r\n')}`,
    'action must emit a fresh frame reflecting the current game state');
}

test('normal and game-over frames include all UI in exactly 24 rows', () => {
  const blocked = new Board(10, 20, Array.from({ length: 20 }, () => Array(10).fill('T')));
  for (const game of [new TetrisGame(), new TetrisGame({ board: blocked })]) {
    const frame = renderFrame(game);
    const rows = frame.split('\n');
    assert.equal(rows.length, 24);
    assert.ok(rows.every(row => row.length <= 60));
    assert.match(rows[0], /Score:0 Lines:0 Next:/);
    assert.match(rows[1], /^\+----------\+$/);
    assert.match(rows[23], /Q quit/);
    if (game.gameOver) assert.match(rows[0], /GAME OVER R:new Q:quit/);
    else assert.equal((frame.match(/@/g) ?? []).length, 4);
  }
});

test('rendered cells preserve settled blocks and place hard-drop blocks exactly', () => {
  // Coordinates are an independent oracle, not derived from renderFrame or cells().
  const settled = [[9, 12], [0, 17], [8, 19]];
  const rows = Array.from({ length: 20 }, () => Array(10).fill(null));
  for (const [x, y] of settled) rows[y][x] = 'J';
  const t = terminal(() => new TetrisGame({
    board: new Board(10, 20, rows),
    initialState: { active: new Piece('O', 1, 2) },
    pieces: { next: () => 'T' },
  }));
  const assertCells = (frame, blocks, active) => {
    const lines = frame.split(/\r?\n/);
    assert.equal(lines.length, 24);
    assert.equal(lines[1], '+----------+');
    assert.equal(lines[22], '+----------+');
    const expected = new Map(blocks.map(([x, y]) => [`${x},${y}`, '#']));
    for (const [x, y] of active) expected.set(`${x},${y}`, '@');
    for (let y = 0; y < 20; y++) {
      assert.equal(lines[y + 2].length, 12);
      assert.equal(lines[y + 2][0], '|');
      assert.equal(lines[y + 2][11], '|');
      for (let x = 0; x < 10; x++) {
        assert.equal(lines[y + 2][x + 1], expected.get(`${x},${y}`) ?? ' ',
          `rendered cell (${x}, ${y})`);
      }
    }
  };
  t.adapter.start();
  try {
    const initialActive = [[1, 2], [2, 2], [1, 3], [2, 3]];
    assertCells(renderFrame(t.adapter.game), settled, initialActive);
    assertCells(t.output.text.split('\x1b[2J').at(-1), settled, initialActive);
    const offset = t.output.text.length;
    t.key('space');
    const locked = [...settled, [1, 18], [2, 18], [1, 19], [2, 19]];
    const spawned = [[4, 0], [3, 1], [4, 1], [5, 1]];
    assert.equal(t.adapter.game.score, 32);
    assert.equal(t.adapter.game.lines, 0);
    assertCells(renderFrame(t.adapter.game), locked, spawned);
    const freshOutput = t.output.text.slice(offset);
    assert.ok(freshOutput.startsWith('\x1b[H\x1b[2J'));
    assertCells(freshOutput.slice('\x1b[H\x1b[2J'.length), locked, spawned);
  } finally { t.adapter.stop(); }
});

test('headers show independent score, line, and preview values after gameplay and restart', () => {
  const t = terminal(() => {
    const rows = Array.from({ length: 20 }, () => Array(10).fill(null));
    // An O fills both bottom-row gaps after dropping to y=18.
    for (const y of [18, 19]) {
      rows[y].fill('J');
      rows[y][4] = rows[y][5] = null;
    }
    const queue = ['I', 'L', 'Z'];
    return new TetrisGame({
      board: new Board(10, 20, rows),
      initialState: { active: new Piece('O', 4, 15), score: 7, lines: 3 },
      pieces: { next: () => queue.shift() },
    });
  });
  // Literal expectations come from fixture/drop arithmetic, never renderFrame
  // or the game's score/lines/nextType getters.
  const assertHeader = (emitted, expected) => {
    assert.equal(renderFrame(t.adapter.game).split('\n')[0], expected);
    assert.ok(emitted.startsWith('\x1b[H\x1b[2J'));
    const frame = emitted.slice('\x1b[H\x1b[2J'.length);
    assert.equal(frame.split('\r\n').length, 24);
    assert.equal(frame.split('\r\n')[0], expected);
  };
  const act = (action, expected) => {
    const offset = t.output.text.length;
    action();
    assertHeader(t.output.text.slice(offset), expected);
  };
  t.adapter.start();
  try {
    assertHeader(t.output.text.slice(t.output.text.indexOf('\x1b[H')),
      'Tetris Score:7 Lines:3 Next:I');
    act(() => t.key('down'), 'Tetris Score:8 Lines:3 Next:I');
    act(() => t.tick(), 'Tetris Score:8 Lines:3 Next:I');
    // One hard-drop row adds 2; clearing two rows adds 300 at level 1.
    // I becomes active and L replaces it in the preview.
    act(() => t.key('space'), 'Tetris Score:310 Lines:5 Next:L');
    act(() => t.key('r'), 'Tetris Score:7 Lines:3 Next:I');
  } finally { t.adapter.stop(); }
});

test('game-over header preserves nonzero counters and deterministic preview', () => {
  const t = terminal(() => {
    const queue = ['O', 'Z'];
    return new TetrisGame({
      board: new Board(10, 20, Array.from({ length: 20 }, () => Array(10).fill('T'))),
      initialState: { score: 1234, lines: 12 },
      pieces: { next: () => queue.shift() },
    });
  });
  t.adapter.start();
  try {
    const expected = 'GAME OVER R:new Q:quit Score:1234 Lines:12 Next:Z';
    assert.equal(renderFrame(t.adapter.game).split('\n')[0], expected);
    const emitted = t.output.text.split('\x1b[H\x1b[2J').at(-1);
    assert.equal(emitted.split('\r\n').length, 24);
    assert.equal(emitted.split('\r\n')[0], expected);
  } finally { t.adapter.stop(); }
});

test('Node entry point prints a bounded snapshot and exits when redirected', () => {
  const result = spawnSync(process.execPath, ['src/index.js'], {
    cwd: new URL('../', import.meta.url), encoding: 'utf8', timeout: 5000,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0);
  assert.equal(result.stderr, '');
  assert.match(result.stdout, /^Tetris/);
  assert.equal(result.stdout.trimEnd().split('\n').length, 24);
  assert.ok(!result.stdout.includes('\x1b'));
});

test('keyboard actions, gravity, and restart redraw the changed game state', () => {
  const t = terminal(() => new TetrisGame({ pieces: { next: () => 'T' } }));
  t.adapter.start();
  try {
    const game = t.adapter.game;
    const { x, y } = game.active;
    assertRedraw(t, () => t.key('left'));
    assert.equal(game.active.x, x - 1);
    assertRedraw(t, () => t.key('right'));
    assert.equal(game.active.x, x);
    const beforeRotation = game.active;
    assert.equal(beforeRotation.type, 'T');
    assertRedraw(t, () => t.input.write('\x1b[A')); // Real Up-arrow decoder.
    assert.notDeepEqual(game.active.shape, beforeRotation.shape);
    assert.deepEqual(game.active.shape, beforeRotation.rotated().shape);
    assert.equal(game.active.x, x);
    assert.equal(game.active.y, y);
    assertRedraw(t, () => t.key('down'));
    assert.equal(game.active.y, y + 1);
    assert.equal(game.score, 1);
    assert.equal([...t.timers.values()][0].delay, 1000);
    assertRedraw(t, () => t.tick());
    assert.equal(game.active.y, y + 2);
    assertRedraw(t, () => t.key('space'));
    assert.ok(game.board.rows.flat().some(Boolean));
    assert.ok(game.score > 1);
    assertRedraw(t, () => t.key('r'));
    assert.notEqual(t.adapter.game, game);
    assert.equal(t.adapter.game.score, 0);
    assert.equal(t.timers.size, 1);
    assert.match(t.output.text, /\x1b\[\?1049h\x1b\[\?25l/);
    assert.ok(!t.output.text.endsWith('\n'));
  } finally { t.adapter.stop(); }
});

test('gravity timers use literal level-dependent delays at startup and on repeat ticks', () => {
  // Independent expectations: every ten lines reduces 1000 ms by 100 ms,
  // with a 100 ms floor, including levels beyond the floor.
  for (const [lines, delay] of [[0, 1000], [10, 900], [40, 600], [90, 100], [150, 100]]) {
    const t = terminal(() => new TetrisGame({
      initialState: { lines }, pieces: { next: () => 'T' },
    }));
    const assertTimer = () => {
      assert.equal(t.timers.size, 1);
      assert.equal([...t.timers.values()][0].delay, delay, `lines=${lines}`);
    };
    t.adapter.start();
    try {
      assertTimer();
      for (let i = 0; i < 2; i++) {
        const previousTimer = t.adapter.timer;
        t.tick();
        assert.ok(!t.timers.has(previousTimer));
        assertTimer();
      }
    } finally { t.adapter.stop(); }
    assert.equal(t.timers.size, 0);
  }
});

test('line clears across a level boundary reschedule gravity at the new delay', () => {
  for (const action of ['gravity', 'down', 'space']) {
    const t = terminal(() => {
      const rows = Array.from({ length: 20 }, () => Array(10).fill(null));
      rows[19].fill('J');
      rows[19][4] = rows[19][5] = null;
      return new TetrisGame({
        board: new Board(10, 20, rows),
        initialState: { lines: 9, active: new Piece('O', 4, 18) },
        pieces: { next: () => 'T' },
      });
    });
    t.adapter.start();
    try {
      assert.equal(t.timers.size, 1);
      assert.equal([...t.timers.values()][0].delay, 1000);
      if (action === 'gravity') t.tick();
      else t.key(action);
      assert.equal(t.adapter.game.lines, 10, `${action} must clear the boundary line`);
      // Keyboard actions may leave the current timeout pending; the next
      // gravity callback must replace it using the updated level.
      if (action !== 'gravity') t.tick();
      assert.equal(t.timers.size, 1);
      assert.equal([...t.timers.values()][0].delay, 900, action);
      t.tick();
      assert.equal(t.timers.size, 1);
      assert.equal([...t.timers.values()][0].delay, 900, action);
    } finally { t.adapter.stop(); }
    assert.equal(t.timers.size, 0);
  }
});

test('real keypress decoder handles arrow escape sequences and quit', () => {
  const t = terminal();
  t.adapter.start();
  const x = t.adapter.game.active.x;
  t.input.write('\x1b[D');
  assert.equal(t.adapter.game.active.x, x - 1);
  t.input.write('q');
  assert.equal(t.adapter.running, false);
  assert.equal(t.timers.size, 0);
});

test('too-small terminals pause play and redraw after resize', () => {
  const t = terminal();
  t.output.rows = 23;
  t.adapter.start();
  try {
    const piece = t.adapter.game.active;
    t.key('down');
    t.tick();
    assert.equal(t.adapter.game.active, piece);
    assert.match(t.output.text, /Resize to 60x24/);
    t.output.rows = 24;
    t.output.columns = 20;
    t.output.emit('resize');
    assert.ok(t.output.text.split('\x1b[2J').at(-1).length < 20);
    t.output.columns = 80;
    t.output.emit('resize');
    t.tick();
    assert.equal(t.adapter.game.active.y, piece.y + 1);
  } finally { t.adapter.stop(); }
});

test('game-over stops gravity, displays instructions, and allows restart', () => {
  let count = 0;
  const t = terminal(() => ++count === 1
    ? new TetrisGame({ board: new Board(10, 20, Array.from({ length: 20 }, () => Array(10).fill('T'))) })
    : new TetrisGame());
  t.adapter.start();
  try {
    assert.match(t.output.text, /GAME OVER/);
    assert.equal(t.timers.size, 0);
    assertRedraw(t, () => t.key('r'));
    assert.equal(t.adapter.game.gameOver, false);
    assert.doesNotMatch(t.output.text.split('\x1b[2J').at(-1), /GAME OVER/);
    assert.equal(t.timers.size, 1);
  } finally { t.adapter.stop(); }
});

test('quit, Ctrl-C and signals restore terminal state and release resources', () => {
  for (const exit of ['q', 'ctrl-c', 'SIGINT', 'SIGTERM', 'SIGHUP', 'exit']) {
    const t = terminal();
    t.adapter.start();
    if (exit === 'q') t.key('q');
    else if (exit === 'ctrl-c') t.input.emit('keypress', '\x03', { name: 'c', ctrl: true });
    else t.signals.emit(exit);
    assert.equal(t.adapter.running, false);
    assert.equal(t.input.isRaw, false);
    assert.equal(t.input.isPaused(), true);
    assert.equal(t.timers.size, 0);
    assert.equal(t.input.listenerCount('keypress'), 0);
    assert.equal(t.output.listenerCount('resize'), 0);
    assert.deepEqual(t.signals.eventNames(), []);
    assert.ok(t.output.text.endsWith('\x1b[?25h\x1b[?1049l'));
    const output = t.output.text;
    t.adapter.stop();
    assert.equal(t.output.text, output);
  }
});
