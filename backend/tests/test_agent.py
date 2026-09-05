import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.configuration.settings import settings
from app.integrations.agent.client import AgentClient, AgentResult
from app.integrations.agent.runner import invoke


def test_missing_entrypoint(monkeypatch):
    monkeypatch.setattr(settings, 'agent_entrypoint', '')
    with pytest.raises(ValueError):
        AgentClient().research({})


@pytest.mark.parametrize('payload', [{}, {'answer': ''}, {'answer': '   '},
    {'answer': 'ok', 'sources': [{'url': 'javascript:alert(1)'}]}])
def test_invalid_results(payload):
    with pytest.raises(ValidationError):
        AgentResult.model_validate(payload)


def test_local_contract(monkeypatch):
    monkeypatch.setattr(settings, 'agent_entrypoint', 'research:research')
    with patch('app.integrations.agent.client.subprocess.run') as run:
        run.return_value.stdout = '{"answer":"Result","sources":[]}'
        assert AgentClient().research({'university': 'Example'}).answer == 'Result'
        assert run.call_args.args[0][0] == sys.executable
        assert run.call_args.kwargs['timeout'] == settings.agent_timeout_seconds
        assert 'Example' in run.call_args.kwargs['input']


@pytest.mark.parametrize('error', [subprocess.TimeoutExpired('agent', 1),
                                  subprocess.CalledProcessError(1, 'agent')])
def test_execution_errors_propagate(monkeypatch, error):
    monkeypatch.setattr(settings, 'agent_entrypoint', 'research:research')
    with patch('app.integrations.agent.client.subprocess.run', side_effect=error):
        with pytest.raises(type(error)):
            AgentClient().research({})


@pytest.mark.parametrize('entry', ['', 'module', ':func', 'module:', 'mod:a:b'])
def test_invalid_entrypoint(entry):
    with pytest.raises(ValueError):
        invoke(entry, {})


def test_sync_and_async_functions(monkeypatch):
    async def async_research(payload):
        return {'answer': payload['question']}
    module = SimpleNamespace(sync=lambda p: {'answer': p['question']},
                             async_research=async_research, invalid=42)
    monkeypatch.setitem(sys.modules, 'test_local_agent', module)
    for name in ['sync', 'async_research']:
        assert invoke('test_local_agent:'+name, {'question': 'Fees'}).answer == 'Fees'
    with pytest.raises(TypeError):
        invoke('test_local_agent:invalid', {})
    with pytest.raises(AttributeError):
        invoke('test_local_agent:missing', {})


def test_runner_protocol(monkeypatch, capsys):
    import io

    from app.integrations.agent.runner import main
    def research(payload):
        print('tool output')
        return {'answer': 'Answer'}
    monkeypatch.setitem(sys.modules, 'test_local_agent', SimpleNamespace(research=research))
    monkeypatch.setattr(sys, 'stdin', io.StringIO(
        '{"entrypoint":"test_local_agent:research","python_path":"","payload":{}}'))
    main()
    captured = capsys.readouterr()
    assert AgentResult.model_validate_json(captured.out).answer == 'Answer'
    assert 'tool output' in captured.err


def test_real_local_process(monkeypatch, tmp_path):
    (tmp_path / "fixture_agent.py").write_text(
        "def research(payload):\n"
        "    print('debug output')\n"
        "    return {'answer': payload['question'], 'sources': []}\n"
    )
    monkeypatch.setattr(settings, "agent_entrypoint", "fixture_agent:research")
    monkeypatch.setattr(settings, "agent_python_path", str(tmp_path))
    assert AgentClient().research({"question": "Fees"}).answer == "Fees"


def test_builtin_research_contract(monkeypatch):
    import json

    from app.integrations.agent import agent_graph

    calls = []

    def run(request):
        calls.append(request)
        return {'structured_response': {
            'answer': 'Verified tuition',
            'sources': [{'title': 'Tuition', 'url': 'https://example.edu/tuition'}],
        }}

    monkeypatch.setattr(agent_graph, 'build_agent', lambda: SimpleNamespace(invoke=run))
    payload = {'university': 'Example', 'country': 'US', 'major': 'CS', 'question': 'Tuition?'}
    result = invoke('app.integrations.agent.agent_graph:research', payload)
    assert result.answer == 'Verified tuition'
    assert str(result.sources[0].url) == 'https://example.edu/tuition'
    assert json.loads(calls[0]['messages'][0]['content']) == payload
