export const WIDTH = 10;
export const HEIGHT = 20;
const shapes = [
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
    this.board = Array.from({ length: HEIGHT }, () => Array(WIDTH).fill(0));
    this.score = 0;
    this.lines = 0;
    this.over = false;
    this.spawn();
  }

  spawn() {
    this.piece = shapes[Math.floor(this.random() * shapes.length)].map(row => [...row]);
    this.x = Math.floor((WIDTH - this.piece[0].length) / 2);
    this.y = 0;
    if (!this.fits(this.piece, this.x, this.y)) this.over = true;
  }

  fits(piece, x, y) {
    return piece.every((row, dy) => row.every((cell, dx) => !cell || (
      x + dx >= 0 && x + dx < WIDTH && y + dy >= 0 && y + dy < HEIGHT &&
      !this.board[y + dy][x + dx]
    )));
  }

  move(dx) {
    if (this.over || !this.fits(this.piece, this.x + dx, this.y)) return false;
    this.x += dx;
    return true;
  }

  rotate() {
    if (this.over) return false;
    const rotated = this.piece[0].map((_, x) => this.piece.map(row => row[x]).reverse());
    for (const kick of [0, -1, 1, -2, 2]) {
      if (this.fits(rotated, this.x + kick, this.y)) {
        this.piece = rotated;
        this.x += kick;
        return true;
      }
    }
    return false;
  }

  down() {
    if (this.over) return false;
    if (this.fits(this.piece, this.x, this.y + 1)) {
      this.y++;
      return true;
    }
    this.lock();
    return false;
  }

  drop() {
    if (this.over) return;
    while (this.fits(this.piece, this.x, this.y + 1)) {
      this.y++;
      this.score += 2;
    }
    this.lock();
  }

  lock() {
    this.piece.forEach((row, dy) => row.forEach((cell, dx) => {
      if (cell) this.board[this.y + dy][this.x + dx] = 1;
    }));
    const remaining = this.board.filter(row => !row.every(Boolean));
    const cleared = HEIGHT - remaining.length;
    this.lines += cleared;
    this.score += [0, 100, 300, 500, 800][cleared];
    this.board = [
      ...Array.from({ length: cleared }, () => Array(WIDTH).fill(0)),
      ...remaining,
    ];
    this.spawn();
  }
}

export function render(game, columns = 80) {
  columns = Number.isFinite(columns) ? Math.max(1, Math.floor(columns)) : 80;
  // A ten-cell board plus borders needs twelve columns even with single-cell blocks.
  // Keep the display bounded on smaller terminals rather than allowing it to wrap.
  if (columns < WIDTH + 2) {
    return ['Resize terminal', 'to 12+ columns', game.over ? 'GAME OVER' : 'Tetris', 'Q quit']
      .map(line => line.slice(0, columns)).join('\n');
  }
  const cells = game.board.map(row => [...row]);
  if (!game.over) game.piece.forEach((row, dy) => row.forEach((cell, dx) => {
    if (cell) cells[game.y + dy][game.x + dx] = 1;
  }));
  const wideCells = columns >= WIDTH * 2 + 2;
  const border = `+${'-'.repeat(WIDTH * (wideCells ? 2 : 1))}+`;
  const status = `${game.over ? 'GAME OVER' : 'Tetris'} | Score: ${game.score} | Lines: ${game.lines}`;
  const controls = columns >= 45
    ? '←→/AD move ↑/W rotate ↓/S down Space drop Q quit'
    : columns >= 40 ? 'AD move W rotate S down Space drop Q quit'
    : columns >= 34 ? 'AD:move W:turn S:down Sp:drop Q:quit'
    : 'AD W S Sp Q';
  return [
    border,
    ...cells.map(row => `|${row.map(cell => wideCells ? (cell ? '[]' : '  ') : (cell ? '#' : ' ')).join('')}|`),
    border,
    status.length <= columns ? status : `${game.over ? 'GAME OVER' : 'Tetris'} S:${game.score}`,
    controls,
  ].map(line => line.slice(0, columns)).join('\n');
}
