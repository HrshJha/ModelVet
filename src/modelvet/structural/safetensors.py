"""Header-only subset inspection from the safetensors format specification."""

from modelvet.core.bytes import open_snapshot_file
from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.classify import FileClassification, FileFormat
from modelvet.inventory.identity import ArtifactFile
from modelvet.structural.base import Inspection

_WIDTHS = {
    "BOOL": 1,
    "U8": 1,
    "I8": 1,
    "F8_E4M3": 1,
    "F8_E5M2": 1,
    "I16": 2,
    "U16": 2,
    "F16": 2,
    "BF16": 2,
    "I32": 4,
    "U32": 4,
    "F32": 4,
    "I64": 8,
    "U64": 8,
    "F64": 8,
}


class SafetensorsInspector:
    check_id = "structural:safetensors"

    def applies_to(self, classification: FileClassification) -> bool:
        return classification.format_class == FileFormat.SAFETENSORS

    def inspect(self, file: ArtifactFile, snapshot: Snapshot) -> Inspection:
        limitation = ("Header/offset checks only; tensor values and loader behavior not tested.",)
        try:
            with open_snapshot_file(snapshot, file) as stream:
                prefix = stream.read(8)
                if len(prefix) != 8:
                    raise InvalidInput("Truncated length prefix.")
                size = int.from_bytes(prefix, "little")
                if not 1 <= size <= min(snapshot.source.limits.max_metadata_bytes, file.size - 8):
                    raise InvalidInput("Invalid or oversized safetensors header.")
                raw = stream.read(size)
            if len(raw) != size or not raw.startswith(b"{"):
                raise InvalidInput("Invalid header encoding.")
            header = strict_json(raw, snapshot.source.limits.max_metadata_bytes)
            if not isinstance(header, dict):
                raise InvalidInput("Header must be an object.")
            metadata = header.pop("__metadata__", {})
            if not isinstance(metadata, dict) or any(
                not isinstance(v, str) for v in metadata.values()
            ):
                raise InvalidInput("Metadata must contain string claims only.")
            data_size = file.size - 8 - size
            spans: list[tuple[int, int]] = []
            for tensor in header.values():
                if not isinstance(tensor, dict) or set(tensor) != {
                    "dtype",
                    "shape",
                    "data_offsets",
                }:
                    raise InvalidInput("Malformed tensor description.")
                dtype, shape, offsets = tensor["dtype"], tensor["shape"], tensor["data_offsets"]
                if not isinstance(dtype, str) or dtype not in _WIDTHS:
                    return Inspection(
                        self.check_id, "UNSUPPORTED", "Unsupported dtype.", limitations=limitation
                    )
                if (
                    not isinstance(shape, list)
                    or len(shape) > 64
                    or any(type(d) is not int or not 0 <= d <= 2**63 - 1 for d in shape)
                ):
                    raise InvalidInput("Invalid or over-limit tensor shape.")
                if (
                    not isinstance(offsets, list)
                    or len(offsets) != 2
                    or any(type(d) is not int for d in offsets)
                ):
                    raise InvalidInput("Invalid tensor offsets.")
                start, end = offsets
                if not 0 <= start <= end <= data_size:
                    raise InvalidInput("Tensor offsets outside the file buffer.")
                count = 1
                for dimension in shape:
                    count *= dimension
                if count * _WIDTHS[dtype] != end - start:
                    raise InvalidInput("Tensor byte length disagrees with shape/dtype.")
                spans.append((start, end))
            cursor = 0
            for start, end in sorted(spans):
                if start != cursor:
                    raise InvalidInput("Tensor buffer contains a hole or overlapping span.")
                cursor = end
            if cursor != data_size:
                raise InvalidInput("Tensor buffer is not entirely indexed.")
            return Inspection(
                self.check_id,
                "COMPLETE",
                details={"tensor_count": len(header)},
                limitations=limitation,
            )
        except InvalidInput:
            return Inspection(
                self.check_id,
                "FAILED",
                "Malformed, changed or over-limit header.",
                limitations=limitation,
            )
