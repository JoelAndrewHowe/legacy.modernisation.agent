import test from 'node:test';
import assert from 'node:assert/strict';
import { PassThrough } from 'node:stream';
import { EventEmitter } from 'node:events';
import { renderFrame, startApp } from '../src/app.js';
import { Game } from '../src/game.js';

function terminal() {
  const input = new PassThrough();
  input.isTTY = true;
  input.isRaw = false;
  input.setRawMode = (raw) => { input.isRaw = raw; };
  const output = new PassThrough();
  output.isTTY = true;
  output.rows = 24;
  output.columns = 80;
  let text = '';
  output.on('data', (chunk) => { text += chunk.toString(); });
  return { input, output, signals: new EventEmitter(), text: () => text };
}

test('initial frame fits within 24 rows and includes a 20-row board', () => {
  const rows = renderFrame().split('\r\n');
  assert.equal(rows.length, 24);
  assert.equal(rows.filter((row) => row.startsWith('|')).length, 20);
  assert.ok(rows.every((row) => row.length <= 22));
  assert.match(rows[0], /TETRIS.*Score: 0/);
  assert.match(rows.join('\n'), /READY/);
  assert.match(rows.join('\n'), /Enter: start/);
  assert.match(rows.join('\n'), /Up: rotate/);
  assert.match(rows[23], /Q\/Esc:quit/);
});

for (const key of [{ name: 'q' }, { name: 'escape' }, { name: 'c', ctrl: true }]) {
  test(`startup and quit via ${JSON.stringify(key)} restore the terminal`, () => {
    const io = terminal();
    const stop = startApp(io);
    assert.equal(io.input.isRaw, true);
    assert.match(io.text(), /TETRIS/);
    io.input.emit('keypress', '', key);
    assert.equal(io.input.isRaw, false);
    assert.equal(io.input.listenerCount('keypress'), 0);
    assert.equal(io.output.listenerCount('resize'), 0);
    assert.equal(io.signals.listenerCount('SIGTERM'), 0);
    assert.ok(io.text().endsWith('\x1b[?25h\x1b[?1049l'));
    const before = io.text();
    stop();
    assert.equal(io.text(), before);
  });
}

test('resizing shows a bounded prompt until both dimensions are restored', () => {
  const io = terminal();
  const stop = startApp(io);
  for (const [columns, rows] of [[21, 24], [22, 23], [10, 2], [1, 1]]) {
    io.output.columns = columns;
    io.output.rows = rows;
    const before = io.text().length;
    io.output.emit('resize');
    const frame = io.text().slice(before).replace('\x1b[H\x1b[2J', '');
    const lines = frame.split('\r\n');
    assert.ok(lines.length <= rows);
    assert.ok(lines.every((line) => line.length <= columns));
    assert.doesNotMatch(frame, /TETRIS|\+---/);
    if (columns >= 14) assert.match(frame, /Resize to 22x24/);
    if (columns >= 11 && rows >= 2) assert.match(frame, /Q\/Esc: quit/);
  }
  io.output.columns = 22;
  io.output.rows = 24;
  const before = io.text().length;
  io.output.emit('resize');
  assert.equal(io.text().slice(before), '\x1b[H\x1b[2J' + renderFrame());
  stop();
});

test('active gameplay stays unchanged until both terminal dimensions are restored', () => {
  const io = terminal();
  const game = new Game(() => 0);
  let tick;
  const stop = startApp({ ...io, game,
    setInterval: (callback) => { tick = callback; return 42; },
    clearInterval: () => {},
  });
  try {
    io.input.emit('keypress', '', { name: 'return' });
    tick();
    const before = JSON.stringify(game);
    for (const [columns, rows] of [[10, 10], [22, 10], [10, 24]]) {
      io.output.columns = columns;
      io.output.rows = rows;
      const offset = io.text().length;
      io.output.emit('resize');
      const redraw = io.text().slice(offset);
      assert.ok(redraw.startsWith('\x1b[H\x1b[2J'));
      const frame = redraw.slice('\x1b[H\x1b[2J'.length);
      assert.doesNotMatch(frame, /TETRIS|\[\]|\+---/);
      assert.ok(frame.split('\r\n').length <= rows);
      assert.ok(frame.split('\r\n').every(line => line.length <= columns));
      for (const name of ['left', 'right', 'up', 'down', 'space', 'return']) {
        io.input.emit('keypress', '', { name });
      }
      io.input.emit('keypress', '?', {});
      tick();
      assert.equal(JSON.stringify(game), before);
    }
    io.output.columns = 22;
    io.output.rows = 24;
    const offset = io.text().length;
    io.output.emit('resize');
    assert.equal(io.text().slice(offset), '\x1b[H\x1b[2J' + renderFrame(game));
    assert.equal(JSON.stringify(game), before);
    tick();
    assert.equal(game.piece.y, 2);
    io.input.emit('keypress', '', { name: 'left' });
    assert.equal(game.piece.x, 2);
  } finally {
    stop();
  }
});

test('quit still restores the terminal while the resize prompt is displayed', () => {
  const io = terminal();
  startApp(io);
  io.output.rows = 10;
  io.output.emit('resize');
  io.input.emit('keypress', '', { name: 'q' });
  assert.equal(io.input.isRaw, false);
  assert.equal(io.output.listenerCount('resize'), 0);
  assert.ok(io.text().endsWith('\x1b[?25h\x1b[?1049l'));
});

test('controls, automatic falling, help and resize pauses, and timer cleanup', () => {
  const io = terminal();
  const game = new Game(() => 0);
  let tick;
  let cancelled;
  const stop = startApp({ ...io, game,
    setInterval: (callback) => { tick = callback; return 42; },
    clearInterval: (id) => { cancelled = id; },
  });
  const press = (name, text = '') => io.input.emit('keypress', text, { name });
  tick();
  assert.equal(game.status, 'ready');
  press('return');
  assert.equal(game.status, 'playing');
  tick();
  assert.equal(game.piece.y, 1);
  press('left');
  assert.equal(game.piece.x, 2);
  press('up');
  assert.equal(game.piece.shape.length, 4);
  press('down');
  assert.equal(game.score, 1);
  press(undefined, '?');
  const before = JSON.stringify(game);
  tick();
  press('right');
  assert.equal(JSON.stringify(game), before);
  assert.match(io.text(), /PAUSED: HELP/);
  press(undefined, '?');
  io.output.rows = 10;
  tick();
  press('space');
  assert.equal(JSON.stringify(game), before);
  io.output.rows = 24;
  io.output.emit('resize');
  press('space');
  assert.ok(game.score > 1);
  assert.match(io.text(), new RegExp(`Score: ${game.score}`));
  stop();
  assert.equal(cancelled, 42);
});

test('termination signals restore previous raw mode', () => {
  const io = terminal();
  io.input.isRaw = true;
  startApp(io);
  io.signals.emit('SIGTERM');
  assert.equal(io.input.isRaw, true);
  assert.equal(io.signals.listenerCount('SIGINT'), 0);
});

test('initially undersized terminals wait for resizing before starting gameplay', () => {
  for (const [columns, rows] of [[21, 24], [22, 23]]) {
    const io = terminal();
    io.output.columns = columns;
    io.output.rows = rows;
    const game = new Game(() => 0);
    let tick;
    const stop = startApp({ ...io, game,
      setInterval: (callback) => { tick = callback; return 42; },
      clearInterval: () => {},
    });
    assert.match(io.text(), /Resize to 22x24/);
    assert.doesNotMatch(io.text(), /TETRIS/);
    io.input.emit('keypress', '', { name: 'return' });
    tick();
    assert.equal(game.status, 'ready');
    io.output.columns = 22;
    io.output.rows = 24;
    io.output.emit('resize');
    assert.match(io.text(), /READY/);
    io.input.emit('keypress', '', { name: 'return' });
    tick();
    assert.equal(game.status, 'playing');
    assert.equal(game.piece.y, 1);
    stop();
    assert.equal(io.input.isRaw, false);
  }
});

test('rejects noninteractive terminals before changing state', () => {
  for (const change of [
    (io) => { io.input.isTTY = false; },
    (io) => { io.output.isTTY = false; },
  ]) {
    const io = terminal();
    change(io);
    assert.throws(() => startApp(io), /terminal/);
    assert.equal(io.input.isRaw, false);
    assert.equal(io.text(), '');
  }
});
