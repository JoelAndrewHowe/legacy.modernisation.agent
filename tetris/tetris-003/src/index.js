#!/usr/bin/env node
import { emitKeypressEvents } from 'node:readline';
import { pathToFileURL } from 'node:url';
import { Game, render } from './game.js';

export function run({ input = process.stdin, output = process.stdout, signals = process,
  game = new Game(), setTimer = setInterval, clearTimer = clearInterval } = {}) {
  const interactive = Boolean(input.isTTY && output.isTTY);
  let timer;
  let stopped = false;
  const draw = () => {
    try {
      output.write(`${interactive ? '\x1b[H\x1b[2J' : ''}${render(game, output.columns)}${interactive ? '' : '\n'}`);
    } catch (error) {
      cleanup();
      throw error;
    }
  };
  const cleanup = () => {
    if (stopped) return;
    stopped = true;
    if (timer !== undefined) clearTimer(timer);
    input.removeListener('keypress', onKey);
    input.removeListener('end', cleanup);
    output.removeListener?.('resize', draw);
    signals.removeListener('SIGINT', cleanup);
    signals.removeListener('SIGTERM', cleanup);
    signals.removeListener('exit', cleanup);
    if (interactive) {
      input.setRawMode(false);
      input.pause();
      output.write('\x1b[?25h\x1b[?1049l');
    }
  };
  const update = action => {
    if (stopped || game.over) return;
    try {
      action();
      draw();
      if (game.over && timer !== undefined) {
        clearTimer(timer);
        timer = undefined;
      }
    } catch (error) {
      cleanup();
      throw error;
    }
  };
  function onKey(text, key = {}) {
    const name = key.name || text;
    if (name === 'q' || name === 'escape' || (key.ctrl && name === 'c')) return cleanup();
    if (name === 'left' || name === 'a') update(() => game.move(-1));
    else if (name === 'right' || name === 'd') update(() => game.move(1));
    else if (name === 'up' || name === 'w') update(() => game.rotate());
    else if (name === 'down' || name === 's') update(() => game.down());
    else if (name === 'space' || text === ' ') update(() => game.drop());
  }
  if (!interactive) {
    draw();
    return cleanup;
  }
  try {
    output.write('\x1b[?1049h\x1b[2J\x1b[?25l');
    input.setRawMode(true);
    emitKeypressEvents(input);
    input.on('keypress', onKey);
    input.on('end', cleanup);
    output.on?.('resize', draw);
    signals.on('SIGINT', cleanup);
    signals.on('SIGTERM', cleanup);
    signals.on('exit', cleanup);
    input.resume();
    draw();
    timer = setTimer(() => update(() => game.down()), 650);
  } catch (error) {
    cleanup();
    throw error;
  }
  return cleanup;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) run();
