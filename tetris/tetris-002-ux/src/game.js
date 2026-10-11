const SHAPES = [
  [[1, 1, 1, 1]],
  [[1, 1], [1, 1]],
  [[0, 1, 0], [1, 1, 1]],
  [[0, 1, 1], [1, 1, 0]],
  [[1, 1, 0], [0, 1, 1]],
  [[1, 0, 0], [1, 1, 1]],
  [[0, 0, 1], [1, 1, 1]],
];

export class Game {
  constructor(random = Math.random) {
    this.random = random;
    this.reset();
  }

  reset() {
    this.board = Array.from({ length: 20 }, () => Array(10).fill(0));
    this.score = 0;
    this.lines = 0;
    this.status = 'ready';
    this.piece = null;
  }

  start() {
    this.reset();
    this.status = 'playing';
    this.spawn();
  }

  spawn() {
    const shape = SHAPES[Math.floor(this.random() * SHAPES.length)].map(row => [...row]);
    this.piece = { shape, x: Math.floor((10 - shape[0].length) / 2), y: 0 };
    if (!this.fits(this.piece)) this.status = 'over';
  }

  fits({ shape, x, y }) {
    return shape.every((row, dy) => row.every((cell, dx) => !cell || (
      x + dx >= 0 && x + dx < 10 && y + dy >= 0 && y + dy < 20 &&
      !this.board[y + dy][x + dx]
    )));
  }

  move(dx, dy = 0) {
    if (this.status !== 'playing') return false;
    const next = { ...this.piece, x: this.piece.x + dx, y: this.piece.y + dy };
    if (!this.fits(next)) return false;
    this.piece = next;
    return true;
  }

  rotate() {
    if (this.status !== 'playing') return;
    const old = this.piece.shape;
    const shape = old[0].map((_, x) => old.map(row => row[x]).reverse());
    for (const offset of [0, -1, 1, -2, 2, -3, 3]) {
      const next = { ...this.piece, shape, x: this.piece.x + offset };
      if (this.fits(next)) {
        this.piece = next;
        return;
      }
    }
  }

  tick(soft = false) {
    if (this.status !== 'playing') return;
    if (this.move(0, 1)) {
      if (soft) this.score++;
    } else {
      this.lock();
    }
  }

  drop() {
    if (this.status !== 'playing') return;
    while (this.move(0, 1)) this.score += 2;
    this.lock();
  }

  lock() {
    const { shape, x, y } = this.piece;
    shape.forEach((row, dy) => row.forEach((cell, dx) => {
      if (cell) this.board[y + dy][x + dx] = 1;
    }));
    const remaining = this.board.filter(row => !row.every(Boolean));
    const cleared = 20 - remaining.length;
    this.lines += cleared;
    this.score += [0, 100, 300, 500, 800][cleared];
    this.board = [...Array.from({ length: cleared }, () => Array(10).fill(0)), ...remaining];
    this.spawn();
  }

  cells() {
    const cells = this.board.map(row => [...row]);
    if (this.piece && this.status !== 'over') {
      const { shape, x, y } = this.piece;
      shape.forEach((row, dy) => row.forEach((cell, dx) => {
        if (cell) cells[y + dy][x + dx] = 2;
      }));
    }
    return cells;
  }
}
