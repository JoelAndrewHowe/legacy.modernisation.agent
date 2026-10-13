"""Optional real-PTY verification: python3 test/verify-terminal.py (POSIX)."""
import errno
import fcntl
import os
from pathlib import Path
import re
import select
import signal
import struct
import subprocess
import termios
import time

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = '< > move | Up spin | Down drop | Space slam | R new | Q quit'
LEAVE = b'\x1b[?25h\x1b[?1049l'


class Session:
    def __init__(self):
        self.master, self.slave = os.openpty()
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 60, 0, 0))
        self.original = termios.tcgetattr(self.slave)
        self.output = b''
        self.process = subprocess.Popen(
            ['npm', 'start'], cwd=ROOT, stdin=self.slave,
            stdout=self.slave, stderr=self.slave, start_new_session=True)

    def pump(self):
        if select.select([self.master], [], [], 0.05)[0]:
            try:
                self.output += os.read(self.master, 65536)
            except OSError as error:
                if error.errno != errno.EIO:
                    raise

    def wait(self, predicate, description, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.pump()
            if predicate():
                return
        raise AssertionError(f'Timed out: {description}; output={self.output[-200:]!r}')

    def frames(self):
        text = self.output.decode('utf-8', errors='replace')
        frames = []
        for chunk in text.split('\x1b[H\x1b[2J')[1:]:
            if CONTROLS not in chunk:
                continue
            chunk = chunk[:chunk.index(CONTROLS) + len(CONTROLS)]
            plain = re.sub(r'\x1b\[[0-9;]*m', '', chunk)
            # The PTY's ONLCR flag can expand the adapter's CRLF to CRCRLF.
            rows = plain.replace('\r', '').split('\n')
            assert len(rows) == 24, len(rows)
            assert all(len(row) <= 60 for row in rows), rows
            assert rows[1] == rows[22] == '+--------------------+'
            assert all(len(row) == 22 for row in rows[2:22])
            frames.append(rows)
        return frames

    def key(self, data):
        count = len(self.frames())
        os.write(self.master, data)
        self.wait(lambda: len(self.frames()) > count, f'redraw after {data!r}')
        return self.frames()[-1]

    def close(self):
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGKILL)
        self.process.wait(timeout=5)
        os.close(self.master)
        os.close(self.slave)


def verify(exit_method, gameplay=False):
    session = Session()
    try:
        session.wait(lambda: bool(session.frames()), 'npm start interactive frame')
        assert b'\x1b[?1049h\x1b[?25l' in session.output
        assert not termios.tcgetattr(session.slave)[3] & termios.ICANON
        if gameplay:
            initial = session.frames()[-1]
            left = session.key(b'\x1b[D')
            assert left[2:22] != initial[2:22]
            right = session.key(b'\x1b[C')
            assert right[2:22] == initial[2:22]
            session.key(b'\x1b[A')  # O rotation may legitimately be unchanged.
            down = session.key(b'\x1b[B')
            assert 'Score:1 ' in down[0]
            count = len(session.frames())
            session.wait(lambda: len(session.frames()) > count, 'real gravity timeout')
            assert session.frames()[-1][2:22] != down[2:22]
            dropped = session.key(b' ')
            assert 'Score:1 ' not in dropped[0]
            assert '██' in dropped[21]
            restarted = session.key(b'r')
            assert 'Score:0 Lines:0 ' in restarted[0]
            for _ in range(100):
                if 'GAME OVER' in session.key(b' ')[0]:
                    break
            else:
                raise AssertionError('Repeated hard drops did not reach game over')
            assert 'R:new Q:quit' in session.frames()[-1][0]
            restarted = session.key(b'r')
            assert restarted[0].startswith('Tetris Score:0 Lines:0 ')
        if exit_method == 'SIGTERM':
            os.killpg(session.process.pid, signal.SIGTERM)
        else:
            os.write(session.master, b'q' if exit_method == 'q' else b'\x03')
        session.wait(lambda: LEAVE in session.output, f'{exit_method} screen cleanup')
        session.wait(lambda: session.process.poll() is not None, f'{exit_method} process exit')
        assert termios.tcgetattr(session.slave) == session.original, 'TTY attributes not restored'
        if exit_method != 'SIGTERM':
            assert session.process.returncode == 0, session.process.returncode
        print(f'PASS npm start PTY: {exit_method}; {len(session.frames())} bounded frames; TTY restored')
    finally:
        session.close()


if __name__ == '__main__':
    verify('q', gameplay=True)
    verify('Ctrl-C')
    verify('SIGTERM')
