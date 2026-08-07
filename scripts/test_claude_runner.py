#!/usr/bin/env python3
"""Behavior tests for scripts.claude_runner (TDD RED first)."""
import io
import json
import os
import signal as signal_module
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scripts.claude_runner import run_claude


def _script(source):
    fd, path = tempfile.mkstemp(suffix='.py', prefix='fake_claude_')
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(source)
    return path


def _run(mode, idle=0.25, output_file=None, target_file=None):
    sources = {
        'steady': """import json,time
for i in range(15):
 print(json.dumps({'type':'stream_event','i':i}),flush=True);time.sleep(.04)
print(json.dumps({'type':'result','result':'ok'}),flush=True)
""",
        'silent': """import json,time
print(json.dumps({'type':'stream_event'}),flush=True)
time.sleep(2)
""",
        'no_result': """import json
print(json.dumps({'type':'stream_event'}),flush=True)
""",
        'error': """import json,sys
print(json.dumps({'type':'stream_event'}),flush=True)
sys.exit(3)
""",
        'result': """import json
print(json.dumps({'type':'stream_event'}),flush=True)
print(json.dumps({'type':'result','result':'success output'}),flush=True)
""",
        'target': """import json,sys,time
p=sys.argv[1]
open(p,'w',encoding='utf-8').write('第一版')
for i in range(8):
 print(json.dumps({'type':'stream_event','i':i}),flush=True);time.sleep(.04)
open(p,'a',encoding='utf-8').write('第二版')
for i in range(8,16):
 print(json.dumps({'type':'stream_event','i':i}),flush=True);time.sleep(.04)
print(json.dumps({'type':'result','result':'done'}),flush=True)
""",
    }
    path = _script(sources[mode])
    command = [sys.executable, path] + ([target_file] if mode == 'target' else [])
    try:
        return run_claude(
            prompt='test', model='sonnet', max_turns=5,
            allowed_tools=['Read', 'Write'], idle_timeout=idle,
            output_file=output_file, target_file=target_file,
            _runner_command=command,
        )
    finally:
        os.unlink(path)


class ClaudeRunnerTests(unittest.TestCase):
    def test_continuous_events_outlive_idle_window(self):
        result = _run('steady')
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['duration'], 0.5)

    def test_silence_returns_stalled_without_fake_result(self):
        result = _run('silent')
        self.assertEqual(result['status'], 'stalled')
        self.assertGreaterEqual(result['idle_seconds'], 0.25)
        self.assertNotIn('result', result)

    def test_target_file_changes_are_progress_not_early_completion(self):
        fd, target = tempfile.mkstemp(); os.close(fd)
        try:
            result = _run('target', target_file=target)
            self.assertEqual(result['status'], 'success')
            with open(target, encoding='utf-8') as fh:
                self.assertEqual(fh.read(), '第一版第二版')
            self.assertTrue(result['target_file_modified'])
            self.assertGreater(result['duration'], 0.5)
        finally:
            os.unlink(target)

    def test_final_result_is_atomically_written(self):
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, 'result.json')
            with patch('os.replace', wraps=os.replace) as replace:
                result = _run('result', output_file=output)
            self.assertEqual(result['status'], 'success')
            with open(output, encoding='utf-8') as fh:
                self.assertEqual(json.load(fh)['result'], 'success output')
            self.assertTrue(any(args[0][1] == output for args in replace.call_args_list))

    def test_zero_exit_without_result_is_not_success(self):
        self.assertEqual(_run('no_result')['status'], 'no_result')

    def test_nonzero_exit_is_error(self):
        result = _run('error')
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['exit_code'], 3)

    def test_command_uses_stream_json_and_required_flags(self):
        with patch('subprocess.Popen') as popen:
            proc = MagicMock()
            proc.stdout = io.StringIO(json.dumps({'type':'result','result':'ok'})+'\n')
            proc.poll.return_value = 0; proc.returncode = 0; proc.wait.return_value = 0
            popen.return_value = proc
            run_claude(prompt='x', model='sonnet', max_turns=7, allowed_tools=['Read','Edit'])
        cmd = popen.call_args[0][0]
        for flag in ['-p','--output-format','--verbose','--max-turns','--model','--allowedTools']:
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[cmd.index('--output-format')+1], 'stream-json')
        self.assertEqual(cmd[cmd.index('--max-turns')+1], '7')

    def test_prompt_file_reads_utf8(self):
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False) as fh:
            fh.write('中文「引号」'); prompt_file = fh.name
        try:
            with patch('subprocess.Popen') as popen:
                proc = MagicMock()
                proc.stdout = io.StringIO(json.dumps({'type':'result','result':'ok'})+'\n')
                proc.poll.return_value = 0; proc.returncode = 0; proc.wait.return_value = 0
                popen.return_value = proc
                result = run_claude(prompt_file=prompt_file, model='sonnet', max_turns=2, allowed_tools=['Read'])
            self.assertEqual(result['status'], 'success')
            self.assertIn('中文「引号」', popen.call_args[0][0])
        finally:
            os.unlink(prompt_file)

    def test_prompt_and_prompt_file_are_exclusive(self):
        with tempfile.NamedTemporaryFile('w', delete=False) as fh: path=fh.name
        try:
            with self.assertRaises(ValueError):
                run_claude(prompt='x', prompt_file=path)
        finally:
            os.unlink(path)

    def test_result_is_json_serializable(self):
        json.dumps(_run('result'))


    def test_events_file_is_truncated_per_run(self):
        with tempfile.TemporaryDirectory() as td:
            events = os.path.join(td, 'events.jsonl')
            with open(events, 'w', encoding='utf-8') as fh:
                fh.write('{"type":"result","result":"stale"}\n')
            child = _script(
                "import json; print(json.dumps({'type':'result','result':'fresh'}),flush=True)"
            )
            try:
                result = run_claude(
                    prompt='test', model='sonnet', max_turns=2,
                    allowed_tools=['Read'], events_file=events,
                    _runner_command=[sys.executable, child],
                )
            finally:
                os.unlink(child)
            self.assertEqual(result['status'], 'success')
            with open(events, encoding='utf-8') as fh:
                rows = [json.loads(x) for x in fh]
            self.assertEqual([x['result'] for x in rows if x.get('type') == 'result'], ['fresh'])

    def test_invalid_json_is_counted_not_success(self):
        path = _script("print('not-json',flush=True)")
        try:
            result = run_claude(
                prompt='test', model='sonnet', max_turns=2,
                allowed_tools=['Read'], _runner_command=[sys.executable, path],
            )
        finally:
            os.unlink(path)
        self.assertEqual(result['status'], 'no_result')
        self.assertEqual(result['invalid_json_count'], 1)

    # ── Issue 1: ResourceWarning ────────────────────────────────────────

    def test_stdout_stderr_closed_after_run(self):
        """proc.stdout and proc.stderr must be explicitly closed."""
        with patch('subprocess.Popen') as popen:
            proc = MagicMock()
            mock_stdout = MagicMock()
            mock_stdout.__iter__.return_value = iter([])  # empty → thread exits immediately
            mock_stderr = MagicMock()
            mock_stderr.__iter__.return_value = iter([])
            proc.stdout = mock_stdout
            proc.stderr = mock_stderr
            proc.poll.return_value = 0
            proc.returncode = 0
            proc.wait.return_value = 0
            popen.return_value = proc
            run_claude(prompt='x', model='sonnet', max_turns=2, allowed_tools=['Read'])
        mock_stdout.close.assert_called()
        mock_stderr.close.assert_called()

    # ── Issue 2: SIGINT/SIGTERM signal handling ─────────────────────────

    def test_signal_handlers_installed_and_restored(self):
        """Main-thread handlers are installed, callable, and then restored."""
        calls = []
        originals = {
            signal_module.SIGINT: object(),
            signal_module.SIGTERM: object(),
        }

        def tracking_signal(signum, handler):
            calls.append((signum, handler))
            return originals[signum]

        with patch('signal.signal', side_effect=tracking_signal):
            with patch('subprocess.Popen') as popen:
                proc = MagicMock()
                proc.stdout = io.StringIO(json.dumps({'type': 'result', 'result': 'ok'}) + '\n')
                proc.stderr = io.StringIO('')
                proc.poll.return_value = 0
                proc.returncode = 0
                proc.wait.return_value = 0
                popen.return_value = proc
                run_claude(prompt='x', model='sonnet', max_turns=2, allowed_tools=['Read'])

        installed = {sig: handler for sig, handler in calls[:2]}
        self.assertEqual(set(installed), {signal_module.SIGINT, signal_module.SIGTERM})
        self.assertTrue(all(callable(h) for h in installed.values()))
        self.assertIn((signal_module.SIGINT, originals[signal_module.SIGINT]), calls[2:])
        self.assertIn((signal_module.SIGTERM, originals[signal_module.SIGTERM]), calls[2:])

    def test_signal_handler_leads_to_child_cleanup(self):
        """Invoking the installed handler cleans the live child first."""
        calls = []
        def tracking_signal(signum, handler):
            calls.append((signum, handler))
            return signal_module.SIG_DFL

        with patch('signal.signal', side_effect=tracking_signal):
            with patch('subprocess.Popen') as popen:
                proc = MagicMock()
                proc.stdout = io.StringIO('')
                proc.stderr = io.StringIO('')
                proc.poll.return_value = None
                proc.wait.return_value = 0
                popen.return_value = proc
                # Force the event loop to hit idle cleanup after handlers install.
                result = run_claude(
                    prompt='x', model='sonnet', max_turns=2,
                    allowed_tools=['Read'], idle_timeout=0.05,
                )
        self.assertEqual(result['status'], 'stalled')
        installed = {sig: h for sig, h in calls[:2]}
        handler = installed[signal_module.SIGINT]
        with self.assertRaises(KeyboardInterrupt):
            handler(signal_module.SIGINT, None)
        self.assertTrue(proc.terminate.called or proc.kill.called)

    # ── Issue 3: exit_timeout ───────────────────────────────────────────

    def test_exit_timeout_after_result(self):
        """After type=result, child that doesn't exit → status=exit_timeout."""
        script = """import json,time,sys
print(json.dumps({'type':'result','result':'done'}),flush=True)
time.sleep(10)
"""
        path = _script(script)
        command = [sys.executable, path]
        try:
            result = run_claude(
                prompt='test', model='sonnet', max_turns=5,
                allowed_tools=['Read'], idle_timeout=5,
                exit_timeout=0.2, _runner_command=command,
            )
        finally:
            os.unlink(path)
        self.assertEqual(result['status'], 'exit_timeout')
        self.assertTrue(result['result_received'])
        self.assertIn('duration', result)
        self.assertIn('target_file_modified', result)

    # ── Issue 4: exit_timeout priority over idle ────────────────────────

    def test_exit_timeout_prioritized_over_idle(self):
        """After result, exit_timeout triggers before idle_timeout (not stalled)."""
        script = """import json,time,sys
print(json.dumps({'type':'result','result':'done'}),flush=True)
time.sleep(10)
"""
        path = _script(script)
        command = [sys.executable, path]
        try:
            result = run_claude(
                prompt='test', model='sonnet', max_turns=5,
                allowed_tools=['Read'], idle_timeout=0.5,
                exit_timeout=0.2, _runner_command=command,
            )
        finally:
            os.unlink(path)
        self.assertEqual(result['status'], 'exit_timeout',
                         msg="exit_timeout must fire before idle_timeout, not 'stalled'")
        # Should fire well before the idle_timeout window
        self.assertLess(result['duration'], 3.0,
                        msg="exit_timeout should kill quickly, not wait for full grace")

    # ── Issue 5: CLI --exit-timeout ─────────────────────────────────────

    def test_cli_exit_timeout_flag(self):
        """--exit-timeout is parsed and passed to run_claude via _main."""
        import scripts.claude_runner as mod

        with patch('argparse.ArgumentParser.parse_args') as parse_args:
            args = MagicMock()
            args.prompt_file = '-'
            args.model = 'sonnet'
            args.max_turns = None
            args.allowed_tools = None
            args.idle_timeout = 120
            args.exit_timeout = 7.5
            args.output_file = None
            args.events_file = None
            args.target_file = None
            parse_args.return_value = args

            with patch.object(mod, 'run_claude') as mock_run:
                mock_run.return_value = {
                    'status': 'success', 'duration': 0, 'target_file_modified': False,
                }
                with patch('sys.stdin', io.StringIO('test prompt')):
                    with patch('sys.stdout', io.StringIO()):
                        with self.assertRaises(SystemExit) as exit_ctx:
                            mod._main()
                self.assertEqual(exit_ctx.exception.code, 0)

            call_kwargs = mock_run.call_args[1]
            self.assertEqual(call_kwargs['exit_timeout'], 7.5)


    def test_cli_exit_timeout_uses_distinct_exit_code_four(self):
        import scripts.claude_runner as mod
        args = MagicMock(prompt_file='-', model='sonnet', max_turns=None,
                         allowed_tools=None, idle_timeout=120, exit_timeout=1,
                         output_file=None, events_file=None, target_file=None)
        with patch('argparse.ArgumentParser.parse_args', return_value=args):
            with patch.object(mod, 'run_claude', return_value={
                'status': 'exit_timeout', 'duration': 1,
                'target_file_modified': False, 'result_received': True,
            }):
                with patch('sys.stdin', io.StringIO('x')):
                    with patch('sys.stdout', io.StringIO()):
                        with self.assertRaises(SystemExit) as ctx:
                            mod._main()
        self.assertEqual(ctx.exception.code, 4)

    def test_exited_process_with_stuck_stdout_reader_is_bounded(self):
        with patch('subprocess.Popen') as popen:
            proc = MagicMock()
            proc.stdout = MagicMock()
            proc.stdout.__iter__.side_effect = lambda: iter(())
            proc.stderr = io.StringIO('')
            proc.poll.return_value = 0
            proc.returncode = 0
            proc.wait.return_value = 0
            popen.return_value = proc
            with patch('threading.Thread') as thread_cls:
                fake_stdout = MagicMock()
                fake_stdout.is_alive.return_value = True
                fake_stderr = MagicMock()
                thread_cls.side_effect = [fake_stdout, fake_stderr]
                result = run_claude(
                    prompt='x', model='sonnet', max_turns=1,
                    allowed_tools=['Read'], exit_timeout=0.1,
                )
        self.assertEqual(result['status'], 'stdout_drain_timeout')
        self.assertLess(result['duration'], 1.0)

    # ── Issue 6: subprocess startup failure ─────────────────────────────

    def test_startup_failure_returns_error(self):
        """Non-existent claude_bin returns status=error, no unhandled exception."""
        result = run_claude(
            prompt='test', model='sonnet', max_turns=5,
            allowed_tools=['Read'], idle_timeout=120,
            claude_bin='/nonexistent/path/to/claude_binary_xyz',
        )
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        # Must be JSON-serialisable
        json.dumps(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
