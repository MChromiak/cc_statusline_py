from __future__ import annotations

import sys


def main() -> None:
    if not sys.stdin.isatty():
        _piped_mode()
    else:
        _interactive_mode()


def _piped_mode() -> None:
    from ccstatusline.config import Config
    from ccstatusline.data import StatusData
    from ccstatusline.renderer import render_statusline

    try:
        raw = sys.stdin.read()
        data = StatusData.model_validate_json(raw)
    except Exception as e:
        print(f"ccstatusline: failed to parse input: {e}", file=sys.stderr)
        print("", end="")
        return

    config = Config.load()

    try:
        output = render_statusline(config, data)
        print(output, end="")
    except Exception as e:
        print(f"ccstatusline: render error: {e}", file=sys.stderr)
        print("", end="")


def _interactive_mode() -> None:
    from ccstatusline.config import Config
    from ccstatusline.tui.app import CCStatuslineApp

    config = Config.load()
    app = CCStatuslineApp(config)
    app.run()


if __name__ == "__main__":
    main()
