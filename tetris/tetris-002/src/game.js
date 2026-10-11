export const WIDTH = 10;
export const HEIGHT = 20;

const SHAPES = {
  I: [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
  J: [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
  L: [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
  O: [[1, 1], [1, 1]],
  S: [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
  T: [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
  Z: [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
};

export class Game {
  constructor({ random = Math.random } = {}) {
    this.random = random;
    this.board = Array.from({ length: HEIGHT }, () => Array(WIDTH).fill(null));
    this.score = 0;
    this.lines = 0;
    this.gameOver = false;
    this.bag = [];
    this.active = null;
    this.spawn();
  }

  get level() {
    return Math.floor(this.lines / 10) + 1;
  }

  get dropInterval() {
    return Math.max(100, 1000 - (this.level - 1) * 75);
  }

  nextType() {
    if (!this.bag.length) {
      this.bag = Object.keys(SHAPES);
      for (let i = this.bag.length - 1; i > 0; i--) {
        const j = Math.floor(this.random() * (i + 1));
        [this.bag[i], this.bag[j]] = [this.bag[j], this.bag[i]];
      }
    }
    return this.bag.pop();
  }

  spawn() {
    if (this.gameOver) return false;
    const type = this.nextType();
    const matrix = SHAPES[type].map(row => [...row]);
    this.active = { type, matrix, x: Math.floor((WIDTH - matrix.length) / 2), y: 0 };
    if (!this.fits(this.active)) {
      this.active = null;
      this.gameOver = true;
      return false;
    }
    return true;
  }

  fits({ matrix, x, y }) {
    return matrix.every((row, dy) => row.every((cell, dx) => {
      if (!cell) return true;
      const bx = x + dx;
      const by = y + dy;
      return bx >= 0 && bx < WIDTH && by < HEIGHT
        && (by < 0 || this.board[by][bx] === null);
    }));
  }

  move(dx, dy = 0) {
    if (this.gameOver || !this.active) return false;
    const candidate = { ...this.active, x: this.active.x + dx, y: this.active.y + dy };
    if (!this.fits(candidate)) return false;
    this.active = candidate;
    return true;
  }

  rotate(direction = 1) {
    if (this.gameOver || !this.active) return false;
    if (this.active.type === 'O') return true;
    const old = this.active.matrix;
    const n = old.length;
    const matrix = Array.from({ length: n }, (_, y) =>
      Array.from({ length: n }, (_, x) =>
        direction === -1 ? old[x][n - 1 - y] : old[n - 1 - x][y]));
    // Small wall/floor kicks let pieces rotate against the board edges.
    for (const [dx, dy] of [[0, 0], [-1, 0], [1, 0], [-2, 0], [2, 0], [0, -1], [0, -2]]) {
      const candidate = { ...this.active, matrix, x: this.active.x + dx, y: this.active.y + dy };
      if (this.fits(candidate)) {
        this.active = candidate;
        return true;
      }
    }
    return false;
  }

  tick() {
    if (this.gameOver) return false;
    if (!this.move(0, 1)) this.lock();
    return !this.gameOver;
  }

  softDrop() {
    if (this.gameOver) return false;
    if (this.move(0, 1)) {
      this.score++;
      return true;
    }
    this.lock();
    return false;
  }

  hardDrop() {
    if (this.gameOver) return 0;
    let distance = 0;
    while (this.move(0, 1)) distance++;
    this.score += distance * 2;
    this.lock();
    return distance;
  }

  lock() {
    if (this.gameOver || !this.active) return;
    const { matrix, x, y, type } = this.active;
    if (matrix.some((row, dy) => row.some(cell => cell && y + dy < 0))) {
      this.gameOver = true;
      this.active = null;
      return;
    }
    matrix.forEach((row, dy) => row.forEach((cell, dx) => {
      if (cell) this.board[y + dy][x + dx] = type;
    }));
    this.active = null;
    this.clearLines();
    this.spawn();
  }

  clearLines() {
    const remaining = this.board.filter(row => row.some(cell => cell === null));
    const cleared = HEIGHT - remaining.length;
    this.score += [0, 100, 300, 500, 800][cleared] * this.level;
    this.lines += cleared;
    this.board = [
      ...Array.from({ length: cleared }, () => Array(WIDTH).fill(null)),
      ...remaining,
    ];
    return cleared;
  }

  // Return a renderable snapshot without exposing board rows for mutation.
  snapshot() {
    const board = this.board.map(row => [...row]);
    if (this.active) {
      const { matrix, x, y, type } = this.active;
      matrix.forEach((row, dy) => row.forEach((cell, dx) => {
        if (cell && y + dy >= 0) board[y + dy][x + dx] = type;
      }));
    }
    return { board, score: this.score, lines: this.lines, level: this.level, gameOver: this.gameOver };
  }
}
