export const SHAPES = Object.freeze({
  I: [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
  J: [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
  L: [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
  O: [[1, 1], [1, 1]],
  S: [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
  T: [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
  Z: [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
});

// The engine has no terminal dependencies. Board cells contain a piece name or null.
export class Game {
  constructor({ width = 10, height = 20, random = Math.random } = {}) {
    if (!Number.isInteger(width) || width < 4 || !Number.isInteger(height) || height < 4) {
      throw new RangeError('Board dimensions must be integers of at least 4');
    }
    this.width = width;
    this.height = height;
    this.random = random;
    this.board = Array.from({ length: height }, () => Array(width).fill(null));
    this.score = 0;
    this.lines = 0;
    this.gameOver = false;
    this.bag = [];
    this.spawn();
  }

  get level() {
    return 1 + Math.floor(this.lines / 10);
  }

  get dropInterval() {
    return Math.max(100, 800 - (this.level - 1) * 60);
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
    this.active = { type, matrix, x: Math.floor((this.width - matrix.length) / 2), y: 0 };
    if (this.collides(this.active)) {
      this.gameOver = true;
      return false;
    }
    return true;
  }

  collides({ matrix, x, y }) {
    return matrix.some((row, dy) => row.some((cell, dx) => {
      if (!cell) return false;
      const bx = x + dx;
      const by = y + dy;
      return bx < 0 || bx >= this.width || by >= this.height ||
        (by >= 0 && this.board[by][bx] !== null);
    }));
  }

  move(dx, dy = 0) {
    if (this.gameOver) return false;
    const candidate = { ...this.active, x: this.active.x + dx, y: this.active.y + dy };
    if (this.collides(candidate)) return false;
    this.active = candidate;
    return true;
  }

  rotate(direction = 1) {
    if (this.gameOver) return false;
    const old = this.active.matrix;
    const n = old.length;
    const matrix = Array.from({ length: n }, (_, y) =>
      Array.from({ length: n }, (_, x) => direction === -1 ? old[x][n - 1 - y] : old[n - 1 - x][y]));
    // Try small horizontal kicks to permit rotation against a wall.
    for (const offset of [0, -1, 1, -2, 2]) {
      const candidate = { ...this.active, matrix, x: this.active.x + offset };
      if (!this.collides(candidate)) {
        this.active = candidate;
        return true;
      }
    }
    return false;
  }

  tick() {
    if (this.gameOver) return false;
    if (!this.move(0, 1)) this.lock();
    return true;
  }

  softDrop() {
    if (this.gameOver) return false;
    if (this.move(0, 1)) {
      this.score += 1;
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
    if (this.gameOver) return;
    const { matrix, x, y, type } = this.active;
    // A piece that cannot fit entirely on the board ends the game.
    if (matrix.some((row, dy) => row.some(cell => cell && y + dy < 0))) {
      this.gameOver = true;
      return;
    }
    matrix.forEach((row, dy) => row.forEach((cell, dx) => {
      if (cell) this.board[y + dy][x + dx] = type;
    }));
    this.clearLines();
    this.spawn();
  }

  clearLines() {
    const remaining = this.board.filter(row => row.some(cell => cell === null));
    const cleared = this.height - remaining.length;
    this.score += [0, 100, 300, 500, 800][cleared] * this.level;
    this.lines += cleared;
    this.board = [
      ...Array.from({ length: cleared }, () => Array(this.width).fill(null)),
      ...remaining,
    ];
    return cleared;
  }
}
