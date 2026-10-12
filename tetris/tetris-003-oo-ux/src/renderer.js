// Terminal layout consumes a detached domain snapshot, never the live game.
export function renderGame({ width, board, piece, score, gameOver }) {
  const activeCells = gameOver ? [] : piece.shape.flatMap((row, y) =>
    row.flatMap((cell, x) => cell ? [[piece.x + x, piece.y + y]] : []));
  const border = `+${'-'.repeat(width * 2)}+`;
  const rows = board.map((row, y) => {
    const cells = row.map((occupied, x) => {
      const active = activeCells.some(([px, py]) => px === x && py === y);
      return occupied || active ? '[]' : '  ';
    });
    return `|${cells.join('')}|`;
  });
  const displayScore = score > 99999 ? score.toExponential(0) : score;
  const title = gameOver ? `GAME OVER Score:${displayScore}` : `TETRIS  Score: ${displayScore}`;
  const help = gameOver ? 'Q / Ctrl-C: quit' : '←→ ↑ ↓ Space Q/^C';
  return [title, border, ...rows, border, help].join('\n');
}
