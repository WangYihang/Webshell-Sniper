"""JSP/Tomcat command-shell benchmark target (see docker/docker-compose.yml).

Java has no eval(), so this target is a *command-only* shell — the validation
case for the upcoming command-shell Backend (LANG-2). For now this just proves
the benchmark target itself executes commands. Skips when the stack is down.
"""

from __future__ import annotations

import time

import pytest
import requests

pytestmark = pytest.mark.benchmark

JSP = "http://127.0.0.1:8081/cmd.jsp"


@pytest.fixture(scope="module")
def jsp_ready() -> None:
    deadline = time.time() + 25
    while time.time() < deadline:
        try:
            if "uid=" in requests.get(JSP, params={"c": "id"}, timeout=2).text:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    pytest.skip("JSP target not up — run `docker compose -f docker/docker-compose.yml up -d jsp`")


def test_jsp_command_execution(jsp_ready: None):
    body = requests.get(JSP, params={"c": "echo SNIPER && id"}, timeout=5).text
    assert "SNIPER" in body
    assert "uid=" in body


def test_jsp_stderr_merges_with_2gt1(jsp_ready: None):
    body = requests.get(JSP, params={"c": "ls /nope-nope 2>&1"}, timeout=5).text
    assert "No such file" in body or "cannot access" in body
