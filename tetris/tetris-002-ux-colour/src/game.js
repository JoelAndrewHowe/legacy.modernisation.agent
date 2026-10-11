export const WIDTH = 10;
export const HEIGHT = 20;
const SHAPES = {
  I: [[0, 1], [1, 1], [2, 1], [3, 1]],
  O: [[1, 0], [2, 0], [1, 1], [2, 1]],
  T: [[1, 0], [0, 1], [1, 1], [2, 1]],
  S: [[1, 0], [2, 0], [0, 1], [1, 1]],
  Z: [[0, 0], [1, 0], [1, 1], [2, 1]],
  J: [[0, 0], [0, 1], [1, 1], [2, 1]],
  L: [[2, 0], [0, 1], [1, 1], [2, 1]],
};

export class Game {
  constructor(random = Math.random) {
    this.random = random;
    this.restart();
  }

  restart() {
    this.board = Array.from({ length: HEIGHT }, () => Array(WIDTH).fill(null));
    this.score = 0;
    this.lines = 0;
    this.level = 1;
    this.over = false;
    this.bag = [];
    this.spawn();
  }

  spawn() {
    if (!this.bag.length) {
      this.bag = Object.keys(SHAPES);
      for (let i = this.bag.length - 1; i > 0; i--) {
        const j = Math.floor(this.random() * (i + 1));
        [this.bag[i], this.bag[j]] = [this.bag[j], this.bag[i]];
      }
    }
    const type = this.bag.pop();
    this.piece = { type, x: 3, y: 0, cells: SHAPES[type].map(cell => [...cell]) };
    if (!this.fits(this.piece)) this.over = true;
  }

  fits(piece) {
    return piece.cells.every(([dx, dy]) => {
      const x = piece.x + dx;
      const y = piece.y + dy;
      return x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT && !this.board[y][x];
    });
  }

  move(dx, dy = 0) {
    if (this.over) return false;
    const candidate = { ...this.piece, x: this.piece.x + dx, y: this.piece.y + dy };
    if (!this.fits(candidate)) return false;
    this.piece = candidate;
    return true;
  }

  rotate() {
    if (this.over || this.piece.type === 'O') return false;
    const size = this.piece.type === 'I' ? 4 : 3;
    const cells = this.piece.cells.map(([x, y]) => [size - 1 - y, x]);
    for (const offset of [0, -1, 1, -2, 2]) {
      const candidate = { ...this.piece, cells, x: this.piece.x + offset };
      if (this.fits(candidate)) {
        this.piece = candidate;
        return true;
      }
    }
    return false;
  }

  drop(soft = false) {
    if (this.over) return;
    if (this.move(0, 1)) {
      if (soft) this.score++;
    } else {
      this.lock();
    }
  }

  hardDrop() {
    if (this.over) return;
    while (this.move(0, 1)) this.score += 2;
    this.lock();
  }

  lock() {
    for (const [dx, dy] of this.piece.cells) {
      this.board[this.piece.y + dy][this.piece.x + dx] = this.piece.type;
    }
    const remaining = this.board.filter(row => row.some(cell => !cell));
    const cleared = HEIGHT - remaining.length;
    this.score += [0, 100, 300, 500, 800][cleared] * this.level;
    this.lines += cleared;
    this.level = 1 + Math.floor(this.lines / 10);
    this.board = [
      ...Array.from({ length: cleared }, () => Array(WIDTH).fill(null)),
      ...remaining,
    ];
    this.spawn();
  }

  get fallDelay() {
    return Math.max(100, 800 - (this.level - 1) * 60);
  }

  displayBoard() {
    const board = this.board.map(row => [...row]);
    if (!this.over) {
      for (const [dx, dy] of this.piece.cells) {
        board[this.piece.y + dy][this.piece.x + dx] = this.piece.type;
      }
    }
    return board;
  }
}
