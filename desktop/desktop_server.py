"""Eigenständiger, mit Python gebündelter Server der macOS-App."""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import shutil
import signal
import socket
import sys
from pathlib import Path

import tornado.httpclient
import tornado.httpserver


def free_port(preferred: int = 0) -> int:
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", preferred))
        except OSError:
            probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def source_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "application"
    return Path(__file__).resolve().parents[1]


def run_worker(arguments: list[str]) -> None:
    from streamlit.web import cli

    sys.argv = ["streamlit", "run", *arguments]
    raise SystemExit(cli.main())


async def serve(args: argparse.Namespace) -> None:
    home = Path(args.app_home).resolve()
    runtime = home / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    # Quellcode unverändert in einen beschreibbaren Laufzeitordner kopieren.
    # Gespeicherte Projekte werden dabei nicht überschrieben.
    shutil.copytree(source_root(), runtime, dirs_exist_ok=True)
    data = home / "data"
    data.mkdir(exist_ok=True)
    os.environ["LAB_ASSISTANT_DATA_DIR"] = str(data)
    os.chdir(runtime)
    sys.path.insert(0, str(runtime))
    import pwa_server

    pwa_server.STATIC = runtime / ".streamlit" / "static"
    gateway_port = free_port(18882)
    backend_port = free_port()
    base = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, str(Path(__file__).resolve())]
    command = [*base, "--streamlit-worker", str(runtime / "pwa_entrypoint.py"),
               "--server.port", str(backend_port), "--server.address", "127.0.0.1",
               "--server.headless", "true", "--browser.gatherUsageStats", "false",
               "--server.fileWatcherType", "none", "--global.developmentMode", "false"]
    process = await asyncio.create_subprocess_exec(*command, cwd=runtime, env=os.environ.copy())
    stopped = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(sig, stopped.set)
    server = None
    ready = Path(args.ready_file)
    try:
        backend = f"http://127.0.0.1:{backend_port}"
        for _ in range(240):
            if process.returncode is not None:
                raise RuntimeError(f"Streamlit wurde beendet ({process.returncode}).")
            if stopped.is_set():
                return
            try:
                await tornado.httpclient.AsyncHTTPClient().fetch(backend + "/_stcore/health")
                break
            except (OSError, tornado.httpclient.HTTPClientError):
                await asyncio.sleep(0.25)
        else:
            raise RuntimeError("Der lokale Server wurde nicht bereit.")
        server = tornado.httpserver.HTTPServer(pwa_server.make_app(backend), max_buffer_size=210 * 1024 * 1024)
        server.listen(gateway_port, address="127.0.0.1")
        payload = {"url": f"http://127.0.0.1:{gateway_port}", "pid": os.getpid(), "data": str(data)}
        temporary = ready.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload))
        temporary.replace(ready)
        while not stopped.is_set():
            if process.returncode is not None:
                raise RuntimeError("Der lokale Server wurde unerwartet beendet.")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stopped.wait(), timeout=1)
    finally:
        if server:
            server.stop()
        with contextlib.suppress(FileNotFoundError):
            ready.unlink()
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=8)
            except TimeoutError:
                process.kill()
                await process.wait()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--streamlit-worker":
        run_worker(sys.argv[2:])
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-home", required=True)
    parser.add_argument("--ready-file", required=True)
    asyncio.run(serve(parser.parse_args()))


if __name__ == "__main__":
    main()
