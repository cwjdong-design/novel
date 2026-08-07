#!/usr/bin/env python3
"""Run Claude Code with stream events and inactivity-based supervision."""

import argparse
import hashlib
import json
import os
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time


def _file_state(path):
    if not path or not os.path.exists(path):
        return None
    stat = os.stat(path)
    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    return {"mtime": stat.st_mtime, "size": stat.st_size, "sha256": digest}


def _is_modified(before, after):
    return before != after


def _atomic_write(path, data):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".claude_runner_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _safe_close(stream):
    if stream is not None:
        try:
            stream.close()
        except Exception:
            pass


def run_claude(
    prompt=None,
    prompt_file=None,
    model="sonnet",
    max_turns=None,
    allowed_tools=None,
    idle_timeout=120,
    exit_timeout=10,
    output_file=None,
    events_file=None,
    target_file=None,
    claude_bin="claude",
    _runner_command=None,
):
    """Run Claude and return a JSON-serialisable supervision result."""
    if (prompt is None) == (prompt_file is None):
        raise ValueError("Exactly one of prompt or prompt_file is required")
    if prompt_file is not None:
        with open(prompt_file, "r", encoding="utf-8") as fh:
            prompt = fh.read()

    if _runner_command is None:
        command = [
            claude_bin, "-p", prompt,
            "--model", model,
            "--output-format", "stream-json",
            "--verbose", "--no-session-persistence",
        ]
        if max_turns is not None:
            command += ["--max-turns", str(max_turns)]
        if allowed_tools:
            command += ["--allowedTools", ",".join(allowed_tools)]
    else:
        command = list(_runner_command)

    started = time.monotonic()
    target_before = _file_state(target_file)
    base = {
        "duration": 0.0,
        "target_file_modified": False,
    }

    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        base.update({
            "status": "error",
            "duration": round(time.monotonic() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
        })
        return base

    event_queue = queue.Queue()
    stderr_chunks = []
    last_activity = time.monotonic()
    result_event = None
    result_received_at = None
    invalid_json_count = 0
    process_exit_seen_at = None
    events_handle = None
    old_handlers = {}

    def stop_child():
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)

    def on_signal(_signum, _frame):
        stop_child()
        raise KeyboardInterrupt

    def read_stdout():
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                event_queue.put(("line", line, time.monotonic()))
        finally:
            event_queue.put(("stdout_eof", None, time.monotonic()))

    def read_stderr():
        assert proc.stderr is not None
        for line in proc.stderr:
            stderr_chunks.append(line)

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)

    try:
        if events_file:
            os.makedirs(os.path.dirname(events_file) or ".", exist_ok=True)
            # One events file represents one run. Retries must not inherit
            # stale events from an earlier invocation.
            events_handle = open(events_file, "w", encoding="utf-8")

        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGINT, signal.SIGTERM):
                old_handlers[sig] = signal.signal(sig, on_signal)

        stdout_thread.start()
        stderr_thread.start()

        while True:
            try:
                kind, payload, observed_at = event_queue.get(timeout=0.05)
            except queue.Empty:
                kind = None
                payload = None
                observed_at = time.monotonic()

            if kind == "line" and payload is not None:
                last_activity = observed_at
                stripped = payload.strip()
                if stripped:
                    try:
                        event = json.loads(stripped)
                    except json.JSONDecodeError:
                        event = None
                        invalid_json_count += 1
                    if event is not None:
                        if events_handle:
                            events_handle.write(stripped + "\n")
                            events_handle.flush()
                        if event.get("type") == "result":
                            result_event = event
                            if result_received_at is None:
                                result_received_at = observed_at

            now = time.monotonic()
            return_code = proc.poll()
            if return_code is not None:
                process_exit_seen_at = process_exit_seen_at or now
                # Give reader threads a moment to enqueue the final lines.
                if stdout_thread.is_alive():
                    if now - process_exit_seen_at >= exit_timeout:
                        base.update({
                            "status": "stdout_drain_timeout",
                            "duration": round(time.monotonic() - started, 3),
                            "target_file_modified": _is_modified(
                                target_before, _file_state(target_file)
                            ),
                            "invalid_json_count": invalid_json_count,
                        })
                        return base
                    stdout_thread.join(timeout=0.2)
                    continue
                while True:
                    try:
                        q_kind, q_payload, q_time = event_queue.get_nowait()
                    except queue.Empty:
                        break
                    if q_kind == "line":
                        last_activity = q_time
                        stripped = q_payload.strip()
                        try:
                            event = json.loads(stripped)
                        except (json.JSONDecodeError, AttributeError):
                            event = None
                            invalid_json_count += 1
                        if event is not None:
                            if events_handle:
                                events_handle.write(stripped + "\n")
                                events_handle.flush()
                            if event.get("type") == "result":
                                result_event = event
                                result_received_at = result_received_at or q_time
                break

            if result_received_at is not None:
                if now - result_received_at >= exit_timeout:
                    stop_child()
                    base.update({
                        "status": "exit_timeout",
                        "duration": round(time.monotonic() - started, 3),
                        "target_file_modified": _is_modified(
                            target_before, _file_state(target_file)
                        ),
                        "result_received": True,
                        "invalid_json_count": invalid_json_count,
                    })
                    return base
            elif now - last_activity >= idle_timeout:
                idle_seconds = now - last_activity
                stop_child()
                base.update({
                    "status": "stalled",
                    "idle_seconds": round(idle_seconds, 3),
                    "duration": round(time.monotonic() - started, 3),
                    "target_file_modified": _is_modified(
                        target_before, _file_state(target_file)
                    ),
                    "invalid_json_count": invalid_json_count,
                })
                return base

        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        duration = round(time.monotonic() - started, 3)
        modified = _is_modified(target_before, _file_state(target_file))
        stderr_text = "".join(stderr_chunks)

        if proc.returncode == 0 and result_event is not None:
            if output_file:
                _atomic_write(output_file, result_event)
            return {
                "status": "success",
                "duration": duration,
                "target_file_modified": modified,
                "result": result_event,
                "invalid_json_count": invalid_json_count,
            }
        if proc.returncode == 0:
            return {
                "status": "no_result",
                "duration": duration,
                "target_file_modified": modified,
                "invalid_json_count": invalid_json_count,
            }
        result = {
            "status": "error",
            "duration": duration,
            "target_file_modified": modified,
            "exit_code": proc.returncode,
            "invalid_json_count": invalid_json_count,
        }
        if stderr_text:
            result["stderr"] = stderr_text
        return result
    except KeyboardInterrupt:
        stop_child()
        raise
    except Exception:
        stop_child()
        raise
    finally:
        if events_handle:
            events_handle.close()
        for sig, previous in old_handlers.items():
            signal.signal(sig, previous)
        _safe_close(proc.stdout)
        _safe_close(proc.stderr)


def _main():
    parser = argparse.ArgumentParser(
        description="Run Claude Code with stream events and inactivity supervision."
    )
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--max-turns", type=int)
    parser.add_argument("--allowed-tools")
    parser.add_argument("--idle-timeout", type=float, default=120)
    parser.add_argument("--exit-timeout", type=float, default=10)
    parser.add_argument("--output-file")
    parser.add_argument("--events-file")
    parser.add_argument("--target-file")
    args = parser.parse_args()

    if args.prompt_file == "-":
        prompt = sys.stdin.read()
    else:
        with open(args.prompt_file, "r", encoding="utf-8") as fh:
            prompt = fh.read()
    tools = None
    if args.allowed_tools:
        tools = [x.strip() for x in args.allowed_tools.split(",") if x.strip()]

    result = run_claude(
        prompt=prompt,
        model=args.model,
        max_turns=args.max_turns,
        allowed_tools=tools,
        idle_timeout=args.idle_timeout,
        exit_timeout=args.exit_timeout,
        output_file=args.output_file,
        events_file=args.events_file,
        target_file=args.target_file,
    )
    print(json.dumps(result, ensure_ascii=False))
    if result["status"] == "success":
        raise SystemExit(0)
    if result["status"] == "stalled":
        raise SystemExit(2)
    if result["status"] == "exit_timeout":
        raise SystemExit(4)
    raise SystemExit(3)


if __name__ == "__main__":
    _main()
