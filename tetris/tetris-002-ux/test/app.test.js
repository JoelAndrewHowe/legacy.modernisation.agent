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

test('application displays readiness, line-clear scoring, game over, and restart', () => {
  const io = terminal();
  const game = new Game(() => 0);
  let tick;
  let cancelled;
  const stop = startApp({ ...io, game,
    setInterval: (callback) => { tick = callback; return 42; },
    clearInterval: (id) => { cancelled = id; },
  });
  const press = (name) => io.input.emit('keypress', '', { name });
  const latestFrame = () => io.text().split('\x1b[H\x1b[2J').at(-1);
  try {
    assert.match(latestFrame(), /READY/);
    assert.match(latestFrame(), /Enter: start/);
    assert.match(latestFrame(), /Left\/Right: move/);
    assert.doesNotMatch(latestFrame(), /Unfinished/);
    press('return');
    assert.match(latestFrame(), /\[\]/);
    game.board[19] = [1, 1, 1, 0, 0, 0, 0, 1, 1, 1];
    press('space');
    assert.equal(game.lines, 1);
    assert.equal(game.score, 138);
    assert.match(latestFrame(), /Score: 138/);
    assert.ok(game.board.every(row => row.every(cell => !cell)));

    // Block the next spawn without blocking the current piece's descent.
    press('left');
    press('left');
    press('left');
    game.board[0][3] = 1;
    press('space');
    assert.equal(game.status, 'over');
    assert.match(latestFrame(), /GAME OVER/);
    assert.match(latestFrame(), /Enter: restart/);
    assert.match(latestFrame(), /Lines: 1/);
    const before = JSON.stringify(game);
    for (const name of ['left', 'right', 'up', 'down', 'space']) press(name);
    tick();
    assert.equal(JSON.stringify(game), before);
    const rows = latestFrame().split('\r\n');
    assert.equal(rows.length, 24);
    assert.ok(rows.every(row => row.length <= 22));

    press('return');
    assert.equal(game.status, 'playing');
    assert.equal(game.score, 0);
    assert.equal(game.lines, 0);
    assert.match(latestFrame(), /Score: 0/);
    assert.doesNotMatch(latestFrame(), /GAME OVER/);
    assert.ok(game.board.every(row => row.every(cell => !cell)));
    tick();
    assert.equal(game.piece.y, 1);
  } finally {
    stop();
  }
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

test('minimized terminals show no content and allow quitting with timer cleanup', () => {
  for (const [columns, rows] of [[0, 24], [22, 0], [0, 0]]) {
    const io = terminal();
    io.output.columns = columns;
    io.output.rows = rows;
    let cancelled;
    const stop = startApp({ ...io,
      setInterval: () => 42,
      clearInterval: (id) => { cancelled = id; },
    });
    try {
      const frame = io.text().split('\x1b[H\x1b[2J').at(-1);
      assert.equal(frame, '');
      io.input.emit('keypress', '', { name: 'escape' });
      assert.equal(cancelled, 42);
      assert.equal(io.input.isRaw, false);
      assert.equal(io.output.listenerCount('resize'), 0);
      assert.ok(io.text().endsWith('\x1b[?25h\x1b[?1049l'));
    } finally {
      stop();
    }
  }
});

test('minimizing active gameplay pauses it until the exact minimum size is restored', () => {
  for (const [columns, rows] of [[0, 24], [22, 0], [0, 0]]) {
    const io = terminal();
    const game = new Game(() => 0);
    let tick;
    let cancelled;
    const stop = startApp({ ...io, game,
      setInterval: (callback) => { tick = callback; return 42; },
      clearInterval: (id) => { cancelled = id; },
    });
    try {
      io.input.emit('keypress', '', { name: 'return' });
      tick();
      const before = JSON.stringify(game);
      io.output.columns = columns;
      io.output.rows = rows;
      const offset = io.text().length;
      io.output.emit('resize');
      assert.equal(io.text().slice(offset), '\x1b[H\x1b[2J');
      for (const name of ['left', 'right', 'up', 'down', 'space', 'return']) {
        io.input.emit('keypress', '', { name });
      }
      tick();
      assert.equal(JSON.stringify(game), before);

      io.output.columns = 22;
      io.output.rows = 24;
      const restoredOffset = io.text().length;
      io.output.emit('resize');
      const restored = io.text().slice(restoredOffset);
      assert.equal(restored, '\x1b[H\x1b[2J' + renderFrame(game));
      const lines = restored.slice('\x1b[H\x1b[2J'.length).split('\r\n');
      assert.equal(lines.length, 24);
      assert.ok(lines.every(line => line.length <= 22));
      assert.equal(JSON.stringify(game), before);
      tick();
      assert.equal(game.piece.y, 2);
    } finally {
      stop();
    }
    assert.equal(cancelled, 42);
    assert.equal(io.input.isRaw, false);
  }
});

test('resizing preserves the help pause until explicitly resumed', () => {
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
    io.input.emit('keypress', '?', {});
    const before = JSON.stringify(game);
    io.output.columns = 21;
    io.output.emit('resize');
    io.input.emit('keypress', '?', {});
    tick();
    io.output.columns = 22;
    const offset = io.text().length;
    io.output.emit('resize');
    assert.equal(io.text().slice(offset), '\x1b[H\x1b[2J' + renderFrame(game, true));
    tick();
    io.input.emit('keypress', '', { name: 'space' });
    assert.equal(JSON.stringify(game), before);
    io.input.emit('keypress', '?', {});
    tick();
    assert.equal(game.piece.y, 2);
  } finally {
    stop();
  }
});

test('every positive undersized boundary clips the prompt and preserves gameplay', () => {
  const io = terminal();
  const game = new Game(() => 0);
  let tick;
  let cancelled;
  const stop = startApp({ ...io, game,
    setInterval: (callback) => { tick = callback; return 42; },
    clearInterval: (id) => { cancelled = id; },
  });
  try {
    io.input.emit('keypress', '', { name: 'return' });
    tick();
    const before = JSON.stringify(game);
    for (let columns = 1; columns <= 22; columns++) {
      for (let rows = 1; rows <= 24; rows++) {
        if (columns === 22 && rows === 24) continue;
        io.output.columns = columns;
        io.output.rows = rows;
        const offset = io.text().length;
        io.output.emit('resize');
        const expected = ['Resize to 22x24', 'Q/Esc: quit']
          .slice(0, rows).map(line => line.slice(0, columns)).join('\r\n');
        assert.equal(io.text().slice(offset), '\x1b[H\x1b[2J' + expected,
          `prompt at ${columns}x${rows}`);
        for (const name of ['return', 'left', 'right', 'up', 'down', 'space']) {
          io.input.emit('keypress', '', { name });
        }
        tick();
        assert.equal(JSON.stringify(game), before);
      }
    }
    io.output.columns = 22;
    io.output.rows = 24;
    const offset = io.text().length;
    io.output.emit('resize');
    assert.equal(io.text().slice(offset), '\x1b[H\x1b[2J' + renderFrame(game));
    tick();
    assert.equal(game.piece.y, 2);
  } finally {
    stop();
  }
  assert.equal(cancelled, 42);
});

test('every undersized startup boundary waits for restoration and cleans up its timer', () => {
  for (let columns = 0; columns <= 22; columns++) {
    for (let rows = 0; rows <= 24; rows++) {
      if (columns === 22 && rows === 24) continue;
      const io = terminal();
      io.output.columns = columns;
      io.output.rows = rows;
      const game = new Game(() => 0);
      let tick;
      let cancelled;
      const stop = startApp({ ...io, game,
        setInterval: (callback) => { tick = callback; return 42; },
        clearInterval: (id) => { cancelled = id; },
      });
      try {
        const expected = columns === 0 || rows === 0 ? ''
          : ['Resize to 22x24', 'Q/Esc: quit']
            .slice(0, rows).map(line => line.slice(0, columns)).join('\r\n');
        assert.equal(io.text().split('\x1b[H\x1b[2J').at(-1), expected,
          `startup at ${columns}x${rows}`);
        const before = JSON.stringify(game);
        for (const name of ['return', 'left', 'right', 'up', 'down', 'space']) {
          io.input.emit('keypress', '', { name });
        }
        io.input.emit('keypress', '?', {});
        tick();
        assert.equal(JSON.stringify(game), before);
        io.output.columns = 22;
        io.output.rows = 24;
        const offset = io.text().length;
        io.output.emit('resize');
        assert.equal(io.text().slice(offset), '\x1b[H\x1b[2J' + renderFrame(game));
        io.input.emit('keypress', '', { name: 'return' });
        tick();
        assert.equal(game.status, 'playing');
        assert.equal(game.piece.y, 1);
        io.input.emit('keypress', '', { name: 'q' });
        assert.equal(cancelled, 42);
        assert.equal(io.input.isRaw, false);
        assert.equal(io.input.listenerCount('keypress'), 0);
        assert.equal(io.output.listenerCount('resize'), 0);
      } finally {
        stop();
      }
    }
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
