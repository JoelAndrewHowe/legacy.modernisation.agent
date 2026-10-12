import assert from 'node:assert/strict';
import test from 'node:test';
import { EventEmitter } from 'node:events';
import { Game, render } from '../src/game.js';
import { run } from '../src/index.js';

const square = () => new Game(() => 1 / 7);

test('all seven pieces spawn with four occupied cells', () => {
  const seen = new Set();
  for (let i = 0; i < 7; i++) {
    const game = new Game(() => i / 7);
    assert.equal(game.piece.flat().filter(Boolean).length, 4);
    assert.equal(game.over, false);
    seen.add(JSON.stringify(game.piece));
  }
  assert.equal(seen.size, 7);
});

test('movement respects walls and occupied cells; rotation preserves blocks', () => {
  const game = new Game(() => 0);
  while (game.move(-1)) {}
  assert.equal(game.x, 0);
  game.board[0][4] = 1;
  assert.equal(game.move(1), false);
  assert.equal(game.rotate(), true);
  assert.equal(game.piece.length, 4);
  assert.equal(game.piece.flat().filter(Boolean).length, 4);
  game.board[0][4] = 0;
  while (game.move(1)) {}
  assert.equal(game.x, 9);
  assert.equal(game.rotate(), false); // cannot kick far enough
  game.move(-1);
  assert.equal(game.rotate(), true); // two-cell wall kick
  assert.equal(game.x, 6);
});

test('gravity locks at floor and spawns another piece', () => {
  const game = square();
  for (let i = 0; i < 18; i++) assert.equal(game.down(), true);
  assert.equal(game.down(), false);
  assert.equal(game.y, 0);
  assert.equal(game.board.flat().filter(Boolean).length, 4);
});

test('hard drop clears lines, awards points, and shifts rows', () => {
  const game = square();
  game.board[19].fill(1);
  game.board[18].fill(1);
  for (const y of [18, 19]) for (const x of [4, 5]) game.board[y][x] = 0;
  game.board[17][0] = 1;
  game.drop();
  assert.equal(game.lines, 2);
  assert.equal(game.score, 336);
  assert.equal(game.board[19][0], 1);
  assert.equal(game.board[0].some(Boolean), false);
});

test('blocked spawn ends the game and subsequent actions do nothing', () => {
  const game = square();
  game.board[0][4] = 1;
  game.drop();
  assert.equal(game.over, true);
  const snapshot = JSON.stringify(game);
  game.move(1); game.rotate(); game.down(); game.drop(); game.lock();
  assert.equal(JSON.stringify(game), snapshot);
});

test('locking clears one through four rows with the correct line scores', () => {
  for (const [cleared, points] of [[1, 100], [2, 300], [3, 500], [4, 800]]) {
    const game = new Game(() => 0);
    game.rotate();
    game.x = 4;
    game.y = 16;
    for (let y = 20 - cleared; y < 20; y++) {
      game.board[y].fill(1);
      game.board[y][4] = 0;
    }
    game.lock();
    assert.equal(game.lines, cleared);
    assert.equal(game.score, points);
    assert.equal(game.board.length, 20);
    assert.ok(game.board.every(row => row.length === 10));
    assert.equal(game.board.flat().filter(Boolean).length, 4 - cleared);
    assert.ok(game.board.slice(0, cleared).every(row => row.every(cell => cell === 0)));
  }
});

test('gravity locks on stacked blocks without overwriting them', () => {
  const game = square();
  game.board[10][4] = 1;
  for (let i = 0; i < 8; i++) assert.equal(game.down(), true);
  assert.equal(game.down(), false);
  assert.equal(game.board[10][4], 1);
  assert.deepEqual(game.board.slice(8, 10).map(row => row.slice(4, 6)), [[1, 1], [1, 1]]);
  assert.equal(game.board.flat().filter(Boolean).length, 5);
  assert.equal(game.y, 0);
});

test('blocked rotation leaves the active piece and board unchanged', () => {
  const game = new Game(() => 0);
  game.board[1].fill(1);
  const snapshot = JSON.stringify(game);
  assert.equal(game.rotate(), false);
  assert.equal(JSON.stringify(game), snapshot);
});

test('startup, gameplay, and game-over displays include controls within 24 rows', () => {
  const game = square();
  const check = label => {
    const rows = render(game).split('\n');
    assert.equal(rows.length, 24);
    assert.match(rows[22], label);
    assert.match(rows[23], /move.*rotate.*down.*drop.*quit/);
  };
  check(/Tetris/);
  game.move(-1); game.rotate(); game.drop(); game.down();
  check(/Score: [1-9]/);
  game.board[0][4] = 1;
  game.drop();
  assert.equal(game.over, true);
  check(/GAME OVER/);
});

test('physical display rows stay within 24 at every width and game state', () => {
  const game = square();
  const check = () => {
    for (let columns = 1; columns <= 100; columns++) {
      const rows = render(game, columns).split('\n');
      const physicalRows = rows.reduce((sum, row) => sum + Math.max(1, Math.ceil([...row].length / columns)), 0);
      assert.ok(physicalRows <= 24, `${columns} columns: ${physicalRows} physical rows`);
      assert.ok(rows.every(row => [...row].length <= columns));
      if (columns >= 12) {
        assert.equal(rows.length, 24);
        assert.match(rows[22], game.over ? /GAME OVER/ : /Tetris/);
        assert.match(rows[23], /Q/);
      }
    }
  };
  check();
  game.move(-1); game.drop(); game.down();
  check();
  game.board[0][4] = 1;
  game.drop();
  assert.equal(game.over, true);
  check();
});

function terminal(game = square(), columns = 80) {
  const input = new EventEmitter();
  input.isTTY = true;
  const raw = [];
  input.setRawMode = value => raw.push(value);
  input.resume = () => {};
  input.pause = () => { input.paused = true; };
  const output = new EventEmitter();
  Object.assign(output, { isTTY: true, columns, text: '', write(text) { this.text += text; } });
  const signals = new EventEmitter();
  let tick;
  let clears = 0;
  const stop = run({ input, output, signals, game,
    setTimer(fn) { tick = fn; return 123; },
    clearTimer(id) { assert.equal(id, 123); clears++; },
  });
  return { input, output, signals, raw, stop, tick: () => tick(), clears: () => clears };
}

test('interactive startup, gameplay, game over, and resize use terminal width', () => {
  const game = square();
  const t = terminal(game, 40);
  const check = () => {
    const frame = t.output.text.split('\x1b[H\x1b[2J').at(-1);
    assert.equal(frame, render(game, t.output.columns));
    const physicalRows = frame.split('\n').reduce((sum, row) =>
      sum + Math.max(1, Math.ceil([...row].length / t.output.columns)), 0);
    assert.ok(physicalRows <= 24);
  };
  check();
  t.input.emit('keypress', ' ', { name: 'space' });
  check();
  t.output.columns = 12;
  t.output.emit('resize');
  check();
  game.board[0][4] = 1;
  t.input.emit('keypress', ' ', { name: 'space' });
  assert.equal(game.over, true);
  check();
  t.output.columns = 1;
  t.output.emit('resize');
  check();
  t.stop();
  assert.equal(t.output.listenerCount('resize'), 0);
});

test('interactive controls and timer drive gameplay; quit restores terminal', () => {
  const game = new Game(() => 0);
  const t = terminal(game);
  const key = name => t.input.emit('keypress', '', { name });
  key('left'); assert.equal(game.x, 2);
  key('d'); assert.equal(game.x, 3);
  key('up'); assert.equal(game.piece.length, 4);
  key('s'); assert.equal(game.y, 1);
  t.tick(); assert.equal(game.y, 2);
  key('space'); assert.equal(game.board.flat().filter(Boolean).length, 4);
  key('q'); t.stop();
  assert.deepEqual(t.raw, [true, false]);
  assert.equal(t.clears(), 1);
  assert.equal(t.input.paused, true);
  assert.equal(t.input.listenerCount('keypress'), 0);
  assert.equal(t.signals.listenerCount('SIGINT'), 0);
  assert.ok(t.output.text.endsWith('\x1b[?25h\x1b[?1049l'));
});

test('signals, EOF, and Ctrl-C clean up terminal', () => {
  for (const event of ['SIGINT', 'SIGTERM', 'exit', 'end', 'ctrl-c']) {
    const t = terminal();
    if (event === 'end') t.input.emit('end');
    else if (event === 'ctrl-c') t.input.emit('keypress', '', { name: 'c', ctrl: true });
    else t.signals.emit(event);
    assert.deepEqual(t.raw, [true, false]);
    assert.equal(t.clears(), 1);
  }
});

test('all control aliases work and Escape quits without further updates', () => {
  const game = new Game(() => 0);
  const t = terminal(game);
  const key = name => t.input.emit('keypress', '', { name });
  key('a'); assert.equal(game.x, 2);
  key('right'); assert.equal(game.x, 3);
  key('w'); assert.equal(game.piece.length, 4);
  key('down'); assert.equal(game.y, 1);
  const snapshot = JSON.stringify(game);
  key('unknown'); assert.equal(JSON.stringify(game), snapshot);
  key('escape');
  t.tick(); key('left');
  assert.equal(JSON.stringify(game), snapshot);
  assert.deepEqual(t.raw, [true, false]);
  assert.equal(t.clears(), 1);
  for (const event of ['SIGINT', 'SIGTERM', 'exit']) {
    assert.equal(t.signals.listenerCount(event), 0);
  }
});

test('keyboard, gravity, and resize failures restore the terminal before propagating', () => {
  for (const source of ['keyboard', 'gravity', 'resize']) {
    const game = square();
    const t = terminal(game);
    const failure = new Error(`${source} failed`);
    let trigger;
    if (source === 'resize') {
      const write = t.output.write;
      t.output.write = function (text) {
        if (text.includes('Tetris')) throw failure;
        write.call(this, text);
      };
      trigger = () => t.output.emit('resize');
    } else {
      game.down = () => { throw failure; };
      trigger = source === 'gravity' ? t.tick
        : () => t.input.emit('keypress', '', { name: 'down' });
    }
    assert.throws(trigger, error => error === failure);
    t.stop();
    assert.deepEqual(t.raw, [true, false]);
    assert.equal(t.clears(), 1);
    assert.equal(t.input.listenerCount('keypress'), 0);
    assert.equal(t.output.listenerCount('resize'), 0);
    assert.equal(t.signals.listenerCount('exit'), 0);
    assert.ok(t.output.text.endsWith('\x1b[?25h\x1b[?1049l'));
  }
});

test('game over stops gravity, renders message, and still accepts quit', () => {
  const game = square();
  const t = terminal(game);
  game.board[0][4] = 1;
  t.input.emit('keypress', ' ', { name: 'space' });
  assert.equal(game.over, true);
  assert.equal(t.clears(), 1);
  assert.match(t.output.text, /GAME OVER/);
  t.input.emit('keypress', 'q', { name: 'q' });
  assert.deepEqual(t.raw, [true, false]);
  assert.equal(t.clears(), 1);
});
