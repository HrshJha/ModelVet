"""Export/check the optional local API schema without starting an HTTP listener."""

import argparse
import json
import tempfile
from pathlib import Path

from modelvet.workbench.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="modelvet-api-schema-") as directory:
        root = Path(directory).resolve()
        models = root / "models"
        models.mkdir()
        app = create_app(models, root / "workspace", "http://127.0.0.1:8765")
        try:
            raw = json.dumps(app.openapi(), sort_keys=True, indent=2) + "\n"
        finally:
            app.state.jobs.close()
            app.state.store.close()
            app.state.workspace.close()
    target = Path(__file__).parents[1] / "schemas/workbench-api-v1.json"
    if arguments.check:
        if not target.exists() or target.read_text() != raw:
            raise SystemExit("Workbench API schema is stale; regenerate it and frontend types.")
    else:
        target.write_text(raw)


if __name__ == "__main__":
    main()
