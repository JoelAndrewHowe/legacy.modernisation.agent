const SHAPES = {
  I: [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
  O: [[1, 1], [1, 1]],
  T: [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
  S: [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
  Z: [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
  J: [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
  L: [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
};

export class Piece {
  constructor(type, x = 3, y = 0, shape = SHAPES[type]) {
    if (!Object.hasOwn(SHAPES, type)) throw new RangeError(`Unknown piece: ${type}`);
    if (!Number.isInteger(x) || !Number.isInteger(y)) {
      throw new TypeError('Piece coordinates must be integers');
    }
    let orientation = SHAPES[type];
    const orientations = [];
    for (let i = 0; i < 4; i++) {
      orientations.push(JSON.stringify(orientation));
      orientation = orientation[0].map((_, y) =>
        orientation.map((_, x) => orientation[orientation.length - 1 - x][y]));
    }
    if (!orientations.includes(JSON.stringify(shape))) {
      throw new RangeError('Shape must be a rotation of its tetromino');
    }
    this.type = type;
    this.x = x;
    this.y = y;
    this.shape = Object.freeze(shape.map(row => Object.freeze([...row])));
    Object.freeze(this);
  }

  cells() {
    return this.shape.flatMap((row, y) => row.flatMap((filled, x) =>
      filled ? [{ x: this.x + x, y: this.y + y }] : []));
  }

  moved(dx, dy) {
    return new Piece(this.type, this.x + dx, this.y + dy, this.shape);
  }

  rotated(clockwise = true) {
    const n = this.shape.length;
    const shape = Array.from({ length: n }, (_, y) =>
      Array.from({ length: n }, (_, x) => clockwise
        ? this.shape[n - 1 - x][y]
        : this.shape[x][n - 1 - y]));
    return new Piece(this.type, this.x, this.y, shape);
  }
}

export class PieceBag {
  #random;
  #bag = [];

  constructor(random = Math.random) {
    this.#random = random;
    Object.freeze(this);
  }

  next() {
    if (!this.#bag.length) {
      this.#bag = Object.keys(SHAPES);
      for (let i = this.#bag.length - 1; i > 0; i--) {
        const j = Math.floor(this.#random() * (i + 1));
        [this.#bag[i], this.#bag[j]] = [this.#bag[j], this.#bag[i]];
      }
    }
    return this.#bag.pop();
  }
}

export class Board {
  #rows;

  constructor(width = 10, height = 20, rows = null) {
    if (!Number.isInteger(width) || width < 4 ||
        !Number.isInteger(height) || height < 4) {
      throw new RangeError('Board dimensions must be integers of at least four');
    }
    rows ??= Array.from({ length: height }, () => Array(width).fill(null));
    if (!Array.isArray(rows) || rows.length !== height || Array.from(rows).some(row =>
      !Array.isArray(row) || row.length !== width ||
      Array.from(row).some(cell => cell !== null && !Object.hasOwn(SHAPES, cell)))) {
      throw new RangeError('Board rows must match dimensions and contain tetromino types or null');
    }
    this.width = width;
    this.height = height;
    this.#rows = rows.map(row => [...row]);
    Object.freeze(this);
  }

  get rows() {
    return Object.freeze(this.#rows.map(row => Object.freeze([...row])));
  }

  fits(piece) {
    return piece instanceof Piece && piece.cells().every(({ x, y }) =>
      x >= 0 && x < this.width && y < this.height &&
      (y < 0 || this.#rows[y][x] === null));
  }

  lock(piece) {
    if (!this.fits(piece)) throw new Error('Cannot lock an overlapping piece');
    const cells = piece.cells();
    for (const { x, y } of cells) {
      if (y >= 0) this.#rows[y][x] = piece.type;
    }
    return cells.some(({ y }) => y < 0);
  }

  clearLines() {
    const remaining = this.#rows.filter(row => row.some(cell => cell === null));
    const cleared = this.height - remaining.length;
    this.#rows = [
      ...Array.from({ length: cleared }, () => Array(this.width).fill(null)),
      ...remaining,
    ];
    return cleared;
  }
}

// Pure gameplay state: the terminal adapter will supply input and call tick()
// once per gravityInterval. No timers or terminal resources are owned here.
export class TetrisGame {
  #board;
  #pieces;
  #score;
  #lines;
  #gameOver = false;
  #active;
  #nextType;
  #boardView;

  constructor({ board = new Board(), pieces = new PieceBag(), initialState = {} } = {}) {
    if (!(board instanceof Board)) throw new TypeError('Expected a Board');
    const { active = null, lines = 0, score = 0 } = initialState;
    if (Object.keys(initialState).some(key => !['active', 'lines', 'score'].includes(key)) ||
        !Number.isSafeInteger(lines) || lines < 0 ||
        !Number.isSafeInteger(score) || score < 0) {
      throw new RangeError('Initial state requires nonnegative integer lines and score');
    }
    this.#board = new Board(board.width, board.height, board.rows);
    if (active !== null && (!(active instanceof Piece) || !this.#board.fits(active))) {
      throw new RangeError('Initial active piece must fit the board');
    }
    this.#pieces = pieces;
    this.#lines = lines;
    this.#score = score;
    const boardOwner = this;
    this.#boardView = Object.freeze({
      width: board.width,
      height: board.height,
      get rows() { return boardOwner.#board.rows; },
      fits: piece => this.#board.fits(piece),
    });
    this.#nextType = this.#pieces.next();
    if (active === null) this.#spawn();
    else this.#active = active;
    Object.freeze(this);
  }

  get board() { return this.#boardView; }
  get active() { return this.#active; }
  get score() { return this.#score; }
  get lines() { return this.#lines; }
  get gameOver() { return this.#gameOver; }
  get nextType() { return this.#nextType; }

  get level() { return Math.floor(this.lines / 10) + 1; }
  get gravityInterval() { return Math.max(100, 1000 - (this.level - 1) * 100); }

  #spawn() {
    const piece = new Piece(this.#nextType);
    this.#active = piece.moved(Math.floor((this.#board.width - piece.shape.length) / 2) - piece.x, 0);
    this.#nextType = this.#pieces.next();
    if (!this.#board.fits(this.#active)) this.#gameOver = true;
  }

  move(dx) {
    if (this.gameOver || !Number.isInteger(dx) || Math.abs(dx) !== 1) return false;
    const candidate = this.active.moved(dx, 0);
    if (!this.board.fits(candidate)) return false;
    this.#active = candidate;
    return true;
  }

  rotate(clockwise = true) {
    if (this.gameOver) return false;
    const rotated = this.active.rotated(clockwise);
    // Simple horizontal wall kicks, rather than full SRS rotation rules.
    for (const dx of [0, -1, 1, -2, 2]) {
      const candidate = rotated.moved(dx, 0);
      if (this.board.fits(candidate)) {
        this.#active = candidate;
        return true;
      }
    }
    return false;
  }

  tick() { return this.#descend(false); }
  softDrop() { return this.#descend(true); }

  #descend(scored) {
    if (this.gameOver) return false;
    const candidate = this.active.moved(0, 1);
    if (this.board.fits(candidate)) {
      this.#active = candidate;
      if (scored) this.#score++;
      return true;
    }
    this.#lock();
    return false;
  }

  hardDrop() {
    if (this.gameOver) return 0;
    let distance = 0;
    while (this.board.fits(this.active.moved(0, 1))) {
      this.#active = this.active.moved(0, 1);
      distance++;
    }
    this.#score += distance * 2;
    this.#lock();
    return distance;
  }

  #lock() {
    if (this.gameOver) return;
    if (this.#board.lock(this.active)) {
      this.#gameOver = true;
      return;
    }
    const cleared = this.#board.clearLines();
    this.#score += [0, 100, 300, 500, 800][cleared] * this.level;
    this.#lines += cleared;
    this.#spawn();
  }
}
