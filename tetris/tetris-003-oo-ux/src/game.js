const SHAPES = [
  [[1, 1], [1, 1]],
  [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
  [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
  [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
  [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
  [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
  [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
];

export class Game {
  #width = 10;
  #height = 20;
  #board;
  #score = 0;
  #gameOver = false;
  #random;
  #piece;

  get width() { return this.#width; }
  get height() { return this.#height; }
  get board() { return this.#board.map(row => [...row]); }
  get piece() { return { ...this.#piece, shape: this.#piece.shape.map(row => [...row]) }; }
  get score() { return this.#score; }
  get gameOver() { return this.#gameOver; }

  snapshot() {
    return { width: this.width, height: this.height, board: this.board,
      piece: this.piece, score: this.score, gameOver: this.gameOver };
  }

  constructor(random = Math.random) {
    this.#board = Array.from({ length: this.#height }, () => Array(this.#width).fill(false));
    this.#random = random;
    this.#spawn();
  }

  #spawn() {
    const index = Math.floor(this.#random() * SHAPES.length);
    const shape = SHAPES[index].map(row => [...row]);
    this.#piece = { shape, x: Math.floor((this.#width - shape.length) / 2), y: 0 };
    if (!this.#fits(this.#piece)) this.#gameOver = true;
  }

  #cells(piece = this.#piece) {
    return piece.shape.flatMap((row, y) => row.flatMap((cell, x) =>
      cell ? [[piece.x + x, piece.y + y]] : []));
  }

  #fits(piece) {
    return this.#cells(piece).every(([x, y]) =>
      x >= 0 && x < this.#width && y >= 0 && y < this.#height && !this.#board[y][x]);
  }

  move(dx) {
    if (this.#gameOver || ![-1, 1].includes(dx)) return false;
    const next = { ...this.#piece, x: this.#piece.x + dx };
    if (!this.#fits(next)) return false;
    this.#piece = next;
    return true;
  }

  rotate() {
    if (this.#gameOver) return false;
    const shape = this.#piece.shape[0].map((_, x) =>
      this.#piece.shape.map(row => row[x]).reverse());
    // Small wall kicks let a rotation succeed beside a wall when space permits.
    for (const dx of [0, -1, 1, -2, 2]) {
      const next = { ...this.#piece, shape, x: this.#piece.x + dx };
      if (this.#fits(next)) {
        this.#piece = next;
        return true;
      }
    }
    return false;
  }

  tick() {
    if (this.#gameOver) return false;
    const next = { ...this.#piece, y: this.#piece.y + 1 };
    if (this.#fits(next)) {
      this.#piece = next;
      return true;
    }
    for (const [x, y] of this.#cells()) this.#board[y][x] = true;
    const remaining = this.#board.filter(row => !row.every(Boolean));
    const cleared = this.#height - remaining.length;
    this.#score += [0, 100, 300, 500, 800][cleared];
    this.#board = [
      ...Array.from({ length: cleared }, () => Array(this.#width).fill(false)),
      ...remaining,
    ];
    this.#spawn();
    return false;
  }

  drop() {
    while (this.tick()) { /* Fall until the current piece locks. */ }
  }
}
