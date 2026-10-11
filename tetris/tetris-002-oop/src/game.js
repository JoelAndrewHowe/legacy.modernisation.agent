const SHAPES = {
  I: [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
  J: [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
  L: [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
  O: [[1, 1], [1, 1]],
  S: [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
  T: [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
  Z: [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
};

const snapshot = (rows) => Object.freeze(rows.map((row) => Object.freeze([...row])));
const rotateMatrix = (matrix) => matrix.map((row, y) =>
  row.map((_, x) => matrix[matrix.length - 1 - x][y]));
const nonnegativeInteger = (value) => Number.isSafeInteger(value) && value >= 0;

// Pieces are immutable values; movement and rotation always produce a new value.
export class Piece {
  constructor(type, x = 0, y = 0, matrix = SHAPES[type]) {
    if (!Object.hasOwn(SHAPES, type)) throw new Error(`Unknown piece: ${type}`);
    if (!Number.isSafeInteger(x) || !Number.isSafeInteger(y)) {
      throw new Error('Piece coordinates must be integers');
    }
    let orientation = SHAPES[type];
    let valid = false;
    for (let i = 0; i < 4; i++) {
      if (JSON.stringify(matrix) === JSON.stringify(orientation)) valid = true;
      orientation = rotateMatrix(orientation);
    }
    if (!valid) throw new Error('Invalid tetromino matrix');
    this.type = type;
    this.x = x;
    this.y = y;
    this.matrix = snapshot(matrix);
    Object.freeze(this);
  }

  cells() {
    return this.matrix.flatMap((row, y) => row.flatMap((filled, x) =>
      filled ? [{ x: this.x + x, y: this.y + y }] : []));
  }

  moved(dx, dy) {
    return new Piece(this.type, this.x + dx, this.y + dy, this.matrix);
  }

  rotated() {
    return new Piece(this.type, this.x, this.y,
      this.type === 'O' ? this.matrix : rotateMatrix(this.matrix));
  }
}

export class Board {
  #rows;

  // Fixture rows are validated and copied, never retained by reference.
  constructor(width = 10, height = 20, rows = null) {
    if (!Number.isSafeInteger(width) || width <= 0 ||
        !Number.isSafeInteger(height) || height <= 0) throw new Error('Invalid board dimensions');
    const initial = rows ?? Array.from({ length: height }, () => Array(width).fill(null));
    if (!Array.isArray(initial) || initial.length !== height || initial.some((row) =>
      !Array.isArray(row) || row.length !== width ||
      Array.from(row).some((cell) => cell !== null && !Object.hasOwn(SHAPES, cell)))) {
      throw new Error('Invalid board rows');
    }
    this.width = width;
    this.height = height;
    this.#rows = initial.map((row) => [...row]);
    Object.freeze(this);
  }

  get rows() { return snapshot(this.#rows); }

  fits(piece) {
    return piece instanceof Piece && piece.cells().every(({ x, y }) =>
      x >= 0 && x < this.width && y >= 0 && y < this.height && !this.#rows[y][x]);
  }

  lock(piece) {
    if (!this.fits(piece)) throw new Error('Cannot lock a colliding piece');
    for (const { x, y } of piece.cells()) this.#rows[y][x] = piece.type;
  }

  clearLines() {
    const remaining = this.#rows.filter((row) => row.some((cell) => cell === null));
    const count = this.height - remaining.length;
    this.#rows = [
      ...Array.from({ length: count }, () => Array(this.width).fill(null)),
      ...remaining,
    ];
    return count;
  }
}

// Each shuffled bag contains all seven tetrominoes once.
export class PieceBag {
  constructor(random = Math.random) {
    this.random = random;
    this.types = [];
  }

  next() {
    if (this.types.length === 0) {
      this.types = Object.keys(SHAPES);
      for (let i = this.types.length - 1; i > 0; i--) {
        const j = Math.floor(this.random() * (i + 1));
        [this.types[i], this.types[j]] = [this.types[j], this.types[i]];
      }
    }
    return this.types.pop();
  }
}

export class TetrisGame {
  #board;
  #source;
  #active;
  #score;
  #lines;
  #gameOver = false;

  // Controlled initial-state fixtures: no mid-game state setters are exposed.
  constructor({ board = new Board(), source = new PieceBag(),
    initialState = {} } = {}) {
    const { active = null, score = 0, lines = 0 } = initialState;
    if (!(board instanceof Board) || !nonnegativeInteger(score) || !nonnegativeInteger(lines)) {
      throw new Error('Invalid initial game state');
    }
    if (active !== null && (!(active instanceof Piece) || !board.fits(active))) {
      throw new Error('Initial active piece must fit the board');
    }
    // The caller cannot mutate the game through the original board reference.
    this.#board = new Board(board.width, board.height, board.rows);
    this.#source = source;
    this.#score = score;
    this.#lines = lines;
    if (active) this.#active = active;
    else this.#spawn();
    Object.freeze(this);
  }

  get board() {
    return Object.freeze({ width: this.#board.width, height: this.#board.height,
      rows: this.#board.rows, fits: (piece) => this.#board.fits(piece) });
  }
  get active() { return this.#active; }
  get score() { return this.#score; }
  get lines() { return this.#lines; }
  get gameOver() { return this.#gameOver; }

  get level() { return Math.floor(this.#lines / 10) + 1; }

  get gravityInterval() {
    return Math.max(100, 1000 - (this.level - 1) * 100);
  }

  #spawn() {
    const piece = new Piece(this.#source.next());
    this.#active = piece.moved(Math.floor((this.#board.width - piece.matrix.length) / 2), 0);
    if (!this.#board.fits(this.#active)) this.#gameOver = true;
  }

  move(dx, dy = 0) {
    if (this.#gameOver) return false;
    const candidate = this.#active.moved(dx, dy);
    if (!this.#board.fits(candidate)) return false;
    this.#active = candidate;
    return true;
  }

  rotate() {
    if (this.#gameOver) return false;
    const rotated = this.#active.rotated();
    // Simple horizontal wall kicks (not the full SRS rotation system).
    for (const dx of [0, -1, 1, -2, 2]) {
      const candidate = rotated.moved(dx, 0);
      if (this.#board.fits(candidate)) {
        this.#active = candidate;
        return true;
      }
    }
    return false;
  }

  tick() {
    if (this.#gameOver) return false;
    if (!this.move(0, 1)) this.lock();
    return true;
  }

  softDrop() {
    if (this.#gameOver) return false;
    if (this.move(0, 1)) this.#score += 1;
    else this.lock();
    return true;
  }

  hardDrop() {
    if (this.#gameOver) return false;
    let distance = 0;
    while (this.move(0, 1)) distance++;
    this.#score += distance * 2;
    this.lock();
    return true;
  }

  lock() {
    if (this.#gameOver) return;
    this.#board.lock(this.#active);
    const level = this.level;
    const cleared = this.#board.clearLines();
    this.#score += [0, 100, 300, 500, 800][Math.min(cleared, 4)] * level;
    this.#lines += cleared;
    this.#spawn();
  }
}
