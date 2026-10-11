import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { Game } from '../src/game.js';
import { renderGame, renderWelcome, startTerminal } from '../src/terminal.js';

const strip = text => text.replace(/\x1b\[[0-9;]*m/g, '');
function terminal() {
  const input = new EventEmitter();
  Object.assign(input, {
    isTTY: true, isRaw: false,
    setRawMode(value) { this.isRaw = value; }, resume() {}, pause() {},
  });
  const output = new EventEmitter();
  Object.assign(output, { isTTY: true, columns: 64, rows: 24, written: '', write(text) { this.written += text; } });
  return { input, output };
}

test('playable display fits 24 rows and 64 columns, including game over', () => {
  const game = new Game(() => 0.5);
  for (const over of [false, true]) {
    game.over = over;
    const rows = strip(renderGame(game)).split('\n');
    assert.equal(rows.length, 24);
    assert.ok(rows.every(row => row.length <= 64));
    assert.match(rows[0], /TETRIS.*Score: 0.*Lines: 0.*Level: 1/);
    assert.match(rows[23], /quit/);
    if (over) assert.match(rows[23], /GAME OVER.*R restart/);
    else {
      assert.match(rows[23], /Left\/Right.*Up.*Down.*Space/);
      assert.match(rows.slice(2, 22).join(''), /[IOTSZJL]{2}/);
    }
  }
});

test('full boards keep both borders and feedback within the 24-row budget', () => {
  const game = new Game(() => 0.5);
  game.board = Array.from({ length: 20 }, () => Array(10).fill('T'));
  game.score = 123456789;
  game.lines = 12345;
  game.level = 1235;
  for (const env of [{}, { NO_COLOR: '' }]) {
    for (const [columns, rows] of [[64, 24], [80, 24], [120, 40]]) {
      for (const over of [false, true]) {
        game.over = over;
        const display = strip(renderGame(game, { env, columns, rows })).split('\n');
        assert.equal(display.length, 24);
        assert.ok(display.every(line => line.length <= columns));
        assert.match(display[0], /Score: 123456789.*Lines: 12345.*Level: 1235/);
        assert.equal(display[1], '+--------------------+');
        assert.equal(display[22], display[1]);
        assert.ok(display.slice(2, 22).every(line => /^\|[IOTSZJL]{20}\|$/.test(line)));
        assert.match(display[23], over ? /GAME OVER.*R restart.*Q\/Esc quit/ : /Left\/Right.*Up.*Down.*Space.*Q\/Esc quit/);
      }
    }
  }
});

test('colour covers pieces, board, status, controls, and game-over feedback', () => {
  const game = new Game();
  game.board[19] = ['I', 'O', 'T', 'S', 'Z', 'J', 'L', null, null, null];
  const text = renderGame(game, { env: {} });
  for (const code of [90, 91, 92, 93, 95, 96, 97, '38;5;111', '38;5;215']) assert.ok(text.includes(`\x1b[1;${code};40m`));
  assert.match(text, /\x1b\[1;97;40mTETRIS/);
  assert.match(text, /\x1b\[1;96;40mLeft\/Right/);
  game.over = true;
  assert.match(renderGame(game, { env: {} }), /\x1b\[1;91;40mGAME OVER/);
});

test('NO_COLOR including empty value preserves all readable information without SGR', () => {
  const game = new Game(() => 0.5);
  for (const over of [false, true]) {
    game.over = over;
    for (const value of ['', '1']) {
      const plain = renderGame(game, { env: { NO_COLOR: value } });
      assert.equal(plain, strip(renderGame(game, { env: {} })));
      assert.ok(!plain.includes('\x1b'));
      assert.match(plain, /TETRIS.*Score/);
      assert.match(plain, /\+--------------------\+/);
      assert.match(plain, /quit/);
    }
  }
});

test('terminal starts in raw mode and restores it on quit', () => {
  const { input, output } = terminal();
  const stop = startTerminal(input, output, { game: new Game(() => 0.5), env: { NO_COLOR: '' } });
  try {
    assert.equal(input.isRaw, true);
    assert.ok(output.written.includes(renderWelcome({ env: { NO_COLOR: '' } })));
    input.emit('keypress', 'q', { name: 'q' });
    assert.equal(input.isRaw, false);
    assert.ok(output.written.endsWith('\x1b[?25h\x1b[?1049l'));
    assert.equal(output.written, strip(output.written));
    assert.equal(input.listenerCount('keypress'), 0);
    assert.equal(output.listenerCount('resize'), 0);
    const written = output.written;
    stop();
    assert.equal(output.written, written);
  } finally { stop(); }
});

test('keys drive movement, rotation, soft/hard drop and restart', () => {
  const { input, output } = terminal();
  const game = new Game(() => 0.5);
  const stop = startTerminal(input, output, { game });
  const press = name => input.emit('keypress', '', { name });
  try {
    const x = game.piece.x;
    press('left'); assert.equal(game.piece.x, x - 1);
    press('right'); assert.equal(game.piece.x, x);
    const cells = game.piece.cells;
    press('up'); assert.notDeepEqual(game.piece.cells, cells);
    press('down'); assert.equal(game.piece.y, 1); assert.equal(game.score, 1);
    press('space'); assert.ok(game.board.flat().some(Boolean)); assert.equal(game.piece.y, 0);
    game.over = true;
    press('left'); assert.match(strip(output.written), /GAME OVER/);
    press('r'); assert.equal(game.over, false); assert.equal(game.score, 0);
    assert.ok(game.board.flat().every(cell => !cell));
  } finally { stop(); }
});

test('gravity locks pieces and stops advancing at game over until restart', t => {
  t.mock.timers.enable({ apis: ['setInterval'] });
  const { input, output } = terminal();
  const game = new Game(() => 0.5);
  game.piece = { type: 'O', x: 3, y: 17, cells: [[1, 0], [2, 0], [1, 1], [2, 1]] };
  const stop = startTerminal(input, output, { game });
  try {
    t.mock.timers.tick(750);
    assert.equal(game.piece.y, 17);
    t.mock.timers.tick(50);
    assert.equal(game.piece.y, 18);
    t.mock.timers.tick(800);
    assert.equal(game.board.flat().filter(Boolean).length, 4);
    assert.equal(game.piece.y, 0);
    assert.equal(game.score, 0);
    game.over = true;
    const before = JSON.stringify(game);
    t.mock.timers.tick(2400);
    assert.equal(JSON.stringify(game), before);
    input.emit('keypress', 'r', { name: 'r' });
    t.mock.timers.tick(800);
    assert.equal(game.over, false);
    assert.equal(game.piece.y, 1);
  } finally { stop(); }
});

test('small terminals show bounded warning, pause play, and recover on resize', t => {
  t.mock.timers.enable({ apis: ['setInterval'] });
  const { input, output } = terminal();
  output.columns = 30; output.rows = 10;
  const game = new Game();
  const stop = startTerminal(input, output, { game });
  try {
    assert.match(strip(output.written), /Terminal too small.*\nNeed 64x24/);
    const original = JSON.stringify(game.piece);
    input.emit('keypress', '', { name: 'space' });
    t.mock.timers.tick(2000);
    assert.equal(JSON.stringify(game.piece), original);
    for (const [columns, rows] of [[10, 2], [64, 23], [63, 24]]) {
      const lines = strip(renderGame(game, { columns, rows })).split('\n');
      assert.ok(lines.length <= rows);
      assert.ok(lines.every(line => line.length <= columns));
    }
    output.columns = 64; output.rows = 24;
    output.emit('resize');
    assert.match(strip(output.written), /Left\/Right move/);
    t.mock.timers.tick(800);
    assert.equal(game.piece.y, 1);
    stop();
    const written = output.written;
    t.mock.timers.tick(2000);
    assert.equal(output.written, written);
  } finally { stop(); }
});

test('entry point rejects non-interactive input with a useful error', () => {
  const result = spawnSync(process.execPath, ['src/index.js'], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /requires an interactive terminal/);
});
