"""The generator's one end-to-end test, and what it cannot establish.

THIS TEST TALKS TO A LIVE MODEL. It is the only one in the suite that does.
Ollama is local and free, so nothing here is spending, but the call is still
real: the suite's result depends on which model this machine has pulled.

A SKIP IS NOT A PASS. When Ollama is not answering, or is answering without the
model this project asks for, the test says so by name and skips. That is the
"nobody could look" answer, and it is a different claim from "the generator
works" -- read the skip reason rather than the green summary.
"""

import pytest

from looksatwords.generator import GnewsGenerator
from looksatwords.llm import HOST, MODEL


def _installed_models() -> list[str] | None:
    """The models this machine has pulled, or None when nobody answered."""
    import httpx

    try:
        r = httpx.get(f"{HOST}/api/tags", timeout=5.0)
        r.raise_for_status()
    except Exception:
        return None
    return [m["name"] for m in r.json().get("models", [])]


@pytest.mark.llm
def test_generator():
    installed = _installed_models()
    if installed is None:
        pytest.skip(
            f"Ollama is not answering on {HOST}. Start it with `ollama serve`. "
            "This test did not run; it did not pass."
        )
    if MODEL not in installed and not any(m.split(":")[0] == MODEL for m in installed):
        pytest.skip(
            f"Ollama is answering on {HOST} but has not pulled {MODEL!r} "
            f"(it holds {installed}). Either `ollama pull {MODEL}` or point this "
            "run at what is here with LOOKSATWORDS_OLLAMA_MODEL. "
            "This test did not run; it did not pass."
        )

    gnews_generator = GnewsGenerator()
    gnews_generator.generate()
    df = gnews_generator.validate()
    assert not df.empty, (
        f"{MODEL} answered but produced no rows -- a real failure, not an "
        "environment one."
    )
