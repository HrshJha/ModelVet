# External ModelScan environment

ModelScan 0.8.8 has a separate hash-pinned environment because its Rich/TOML constraints conflict with the core package. No scanner package is imported into ModelVet. Python 3.12 and uv 0.13.3 were used for the macOS smoke check.

```sh
uv venv --python 3.12 .scanner-venv
uv pip sync --python .scanner-venv/bin/python --require-hashes --only-binary :all: tools/modelscan/requirements.lock
.scanner-venv/bin/modelscan --version
```

The CLI adapter checks exact version and entry-point hash; the executable must be outside the assessed artifact. Scanner availability is not admission approval. Optional TensorFlow/h5py extras are not installed or supported by this lock. The local environment/binaries are ignored, not redistributed in the core wheel. Package and bundled notices/advisory review: `docs/verification/MV-010/`.

On this macOS host, memory limit APIs fail; the adapter records that gap. Required resource coverage must stay unresolved until an enforceable platform contract is established. CPU, file/descriptor/output and wall limits are checked. This is a subprocess boundary with residual parser exploitation and network risk, not a sandbox.
