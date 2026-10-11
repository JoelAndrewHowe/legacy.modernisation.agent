import { TetrisApplication } from './application.js';

try {
  new TetrisApplication().start();
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
