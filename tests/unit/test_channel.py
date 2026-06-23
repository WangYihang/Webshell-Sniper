"""The Channel protocol: Transport satisfies it, and custom channels plug in."""

from webshell_sniper.config import Config
from webshell_sniper.core.channel import Channel
from webshell_sniper.core.executor import Executor
from webshell_sniper.core.transport import Transport


def test_transport_is_a_channel():
    assert isinstance(Transport("http://x/c.php", "POST", "c", Config()), Channel)


def test_plain_object_without_send_is_not_a_channel():
    assert not isinstance(object(), Channel)


def test_custom_channel_drives_the_executor():
    """A non-HTTP channel (here: an in-memory echo) works with no other change."""

    class EchoChannel:
        def __init__(self) -> None:
            self.sent: list[str] = []

        def send(self, payload: str) -> str:
            self.sent.append(payload)
            # Behave like a PHP shell: decode + run the eval payload's sentinels.
            import base64
            import re

            inner = base64.b64decode(
                re.fullmatch(r"eval\(base64_decode\('([^']*)'\)\);", payload).group(1)
            ).decode()
            token = inner.split("'", 2)[1]
            return f"{token}DONE{token}"

    ch = EchoChannel()
    assert isinstance(ch, Channel)
    ex = Executor(ch)
    assert ex.run_php("echo 1") == "DONE"
    assert ch.sent  # the payload actually went through our channel
