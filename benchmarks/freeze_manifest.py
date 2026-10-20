"""Freeze development recipe identities. Never manufactures independent review or holdout."""

import hashlib
from pathlib import Path

from modelvet.benchmarks import corpus

cases = []
for recipe in corpus.RECIPES:
    values = corpus.fixture_bytes(recipe)
    cases.append(
        corpus.CorpusCase(
            fixture_id=recipe,
            recipe=recipe,
            stratum="S2" if recipe.startswith(("zip-", "pickle-")) else "S1",
            label=corpus.static_oracle(recipe, values),
            artifact_digest=corpus.fixture_identity(values),
            files=tuple(
                corpus.FixtureFile(
                    relpath=name, sha256=hashlib.sha256(raw).hexdigest(), size=len(raw)
                )
                for name, raw in sorted(values.items())
            ),
            baseline_eligibility="STANDALONE_PICKLE"
            if recipe.startswith("pickle-")
            else "NOT_APPLICABLE",
        )
    )
manifest = corpus.CorpusManifest(
    corpus_id="modelvet-synthetic-development-v1",
    generator_sha256=hashlib.sha256(Path(corpus.__file__).read_bytes()).hexdigest(),
    cases=tuple(cases),
)
target = Path(__file__).with_name("manifest.json")
with target.open("x") as stream:
    stream.write(manifest.model_dump_json(indent=2) + "\n")
