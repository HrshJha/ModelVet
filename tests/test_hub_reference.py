"""T-HF-URL-01 / T-HF-AUTH-01: strict public references and explicit local auth."""

import pytest

from modelvet.core.errors import InvalidInput
from modelvet.hub.reference import HubReference, selected_token


@pytest.mark.parametrize(
    "value,revision",
    [
        ("https://huggingface.co/Owner/model", None),
        ("https://HUGGINGFACE.CO/Owner/model/", None),
        ("https://huggingface.co/Owner/model/tree/main", "main"),
    ],
)
def test_valid_reference(value, revision):
    ref = HubReference.parse(value)
    assert ref.repo_id == "Owner/model" and ref.revision == revision
    assert ref.url == "https://huggingface.co/Owner/model"


@pytest.mark.parametrize(
    "value",
    [
        "http://huggingface.co/a/b",
        "https://huggingface.co.evil/a/b",
        "https://user:secret@huggingface.co/a/b",
        "https://huggingface.co:443/a/b",
        "https://huggingface.co/datasets/a",
        "https://huggingface.co/spaces/a/b",
        "https://huggingface.co/a/b?token=secret",
        "https://huggingface.co/a/b#token",
        "https://huggingface.co/a/b?",
        "https://huggingface.co/a/b#",
        "https://huggingface.co/a/b/resolve/main/file",
        "https://huggingface.co/a//b",
        "https://huggingface.co/a/b%2fmain",
        "https://huggingface.co/a/b//",
        " https://huggingface.co/a/b",
        "https://huggingface.co/a/..",
        "https://huggingface.co/a/b.git",
        "https://huggingface.co/a/b\\c",
    ],
)
def test_rejected_reference_never_echoes_input(value):
    with pytest.raises(InvalidInput) as exc:
        HubReference.parse(value)
    assert "secret" not in str(exc.value)


def test_revision_conflict_and_pr_revision():
    assert HubReference.parse("https://huggingface.co/a/b", "refs/pr/1").revision == "refs/pr/1"
    assert HubReference.parse("https://huggingface.co/a/b/tree/main", "main").revision == "main"
    with pytest.raises(InvalidInput):
        HubReference.parse("https://huggingface.co/a/b/tree/main", "other")


def test_auth_is_explicit_and_missing_token_is_controlled(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_PRIVATE1234")
    assert selected_token(False) is None
    assert selected_token(True) == "hf_PRIVATE1234"
    monkeypatch.delenv("HF_TOKEN")
    with pytest.raises(InvalidInput, match="HF_TOKEN is missing"):
        selected_token(True)
