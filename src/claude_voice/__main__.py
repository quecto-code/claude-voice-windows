"""``python -m claude_voice`` のエントリポイント。"""

from __future__ import annotations

from . import server


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
