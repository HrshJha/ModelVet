"""Bounded classic ZIP index inspection, without extraction or decompression."""

import stat
import struct

from modelvet.core.bytes import open_snapshot_file
from modelvet.core.errors import InvalidInput
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.classify import FileClassification, FileFormat
from modelvet.inventory.discover import validate_relpath
from modelvet.inventory.identity import ArtifactFile
from modelvet.structural.base import Inspection

_CENTRAL = struct.Struct("<4s6H3I5H2I")
_LOCAL = struct.Struct("<4s5H3I2H")
_END = struct.Struct("<4s4H2IH")


class UnsupportedZip(Exception):
    pass


def _extras(data: bytes) -> None:
    cursor = 0
    while cursor < len(data):
        if cursor + 4 > len(data):
            raise InvalidInput("Truncated ZIP extra field.")
        tag, size = struct.unpack_from("<HH", data, cursor)
        cursor += 4 + size
        if cursor > len(data):
            raise InvalidInput("Truncated ZIP extra data.")
        if tag in {1, 0x7075}:
            raise UnsupportedZip("ZIP64 or alternate Unicode paths are unsupported.")


class ZipIndexInspector:
    check_id = "structural:zip"

    def applies_to(self, classification: FileClassification) -> bool:
        return classification.format_class in {FileFormat.PYTORCH_ZIP, FileFormat.ZIP_OTHER}

    def inspect(self, file: ArtifactFile, snapshot: Snapshot) -> Inspection:
        limitations = (
            "Index/header consistency only; CRC, payload and loader semantics not tested.",
            "ZIP64, descriptors, encryption and multi-disk ZIP are unsupported.",
        )
        try:
            cap = snapshot.source.limits.max_metadata_bytes
            with open_snapshot_file(snapshot, file) as stream:
                tail_size = min(file.size, 65557, cap)
                stream.seek(file.size - tail_size)
                tail = stream.read(tail_size)
                at = tail.rfind(b"PK\x05\x06")
                if at < 0 or at + _END.size > len(tail):
                    raise InvalidInput("Missing ZIP end record.")
                _, disk, directory_disk, disk_count, count, size, offset, comment = (
                    _END.unpack_from(tail, at)
                )
                if disk or directory_disk or disk_count != count:
                    raise UnsupportedZip("Multi-disk ZIP is unsupported.")
                if count == 0xFFFF or size == 0xFFFFFFFF or offset == 0xFFFFFFFF:
                    raise UnsupportedZip("ZIP64 is unsupported.")
                end_position = file.size - tail_size + at
                if at + _END.size + comment != len(tail) or offset + size != end_position:
                    raise InvalidInput("Inconsistent ZIP directory bounds.")
                if count > snapshot.source.limits.max_files or size + tail_size > cap:
                    raise InvalidInput("ZIP index budget exceeded.")
                stream.seek(offset)
                directory = stream.read(size)
                if len(directory) != size:
                    raise InvalidInput("Truncated ZIP central directory.")
                cursor = total = 0
                used = size + tail_size
                seen: set[str] = set()
                spans: list[tuple[int, int]] = []
                members: list[dict[str, str | int]] = []
                for _ in range(count):
                    if cursor + _CENTRAL.size > size:
                        raise InvalidInput("Truncated ZIP entry.")
                    entry = _CENTRAL.unpack_from(directory, cursor)
                    (
                        sig,
                        made,
                        needed,
                        flags,
                        method,
                        _,
                        _,
                        crc,
                        compressed,
                        uncompressed,
                        namesize,
                        extra,
                        note,
                        startdisk,
                        _,
                        attributes,
                        local,
                    ) = entry
                    if sig != b"PK\x01\x02":
                        raise InvalidInput("Invalid ZIP central signature.")
                    if needed > 20 or startdisk or flags & ~0x806 or method not in {0, 8}:
                        raise UnsupportedZip("Unsupported ZIP feature or streaming descriptor.")
                    if compressed == 0xFFFFFFFF or uncompressed == 0xFFFFFFFF:
                        raise UnsupportedZip("ZIP64 entry is unsupported.")
                    stop = cursor + _CENTRAL.size + namesize + extra + note
                    if stop > size:
                        raise InvalidInput("ZIP entry extends outside index.")
                    raw_name = directory[cursor + _CENTRAL.size : cursor + _CENTRAL.size + namesize]
                    name = raw_name.decode("utf-8" if flags & 0x800 else "cp437")
                    path = validate_relpath(name[:-1] if name.endswith("/") else name)
                    if ":" in path.split("/")[0] or path.casefold() in seen:
                        raise InvalidInput("Unsafe or duplicate ZIP member name.")
                    seen.add(path.casefold())
                    mode = attributes >> 16 if made >> 8 == 3 else 0
                    if stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}:
                        raise InvalidInput("Special ZIP member type.")
                    total += uncompressed
                    if (
                        uncompressed > snapshot.source.limits.max_file_bytes
                        or total > snapshot.source.limits.max_total_bytes
                        or uncompressed > max(compressed, 1) * 100
                    ):
                        raise InvalidInput("ZIP declared size or ratio budget exceeded.")
                    _extras(directory[cursor + _CENTRAL.size + namesize : stop - note])
                    if local + _LOCAL.size > offset:
                        raise InvalidInput("ZIP local header outside data region.")
                    stream.seek(local)
                    raw_local = stream.read(_LOCAL.size)
                    if len(raw_local) != _LOCAL.size:
                        raise InvalidInput("Truncated local header.")
                    values = _LOCAL.unpack(raw_local)
                    lsig, version, lflags, lmethod, _, _, lcrc, lcsize, lusize, lname, lextra = (
                        values
                    )
                    used += _LOCAL.size + lname + lextra
                    if used > cap:
                        raise InvalidInput("ZIP local metadata budget exceeded.")
                    if lsig != b"PK\x03\x04" or (
                        version,
                        lflags,
                        lmethod,
                        lcrc,
                        lcsize,
                        lusize,
                    ) != (needed, flags, method, crc, compressed, uncompressed):
                        raise InvalidInput("Local and central ZIP headers disagree.")
                    local_name = stream.read(lname)
                    local_extra = stream.read(lextra)
                    if local_name != raw_name or len(local_extra) != lextra:
                        raise InvalidInput("Local and central ZIP names disagree.")
                    _extras(local_extra)
                    end = local + _LOCAL.size + lname + lextra + compressed
                    if end > offset:
                        raise InvalidInput("ZIP member data outside file region.")
                    spans.append((local, end))
                    members.append(
                        {
                            "name": name,
                            "compressed_size": compressed,
                            "uncompressed_size": uncompressed,
                        }
                    )
                    cursor = stop
                if cursor != size:
                    raise InvalidInput("ZIP entry count disagrees with directory size.")
                previous = 0
                for start, stop in sorted(spans):
                    if start < previous:
                        raise InvalidInput("Overlapping ZIP members.")
                    previous = stop
            return Inspection(
                self.check_id, "COMPLETE", details={"members": members}, limitations=limitations
            )
        except UnsupportedZip:
            return Inspection(
                self.check_id, "UNSUPPORTED", "Unsupported ZIP feature.", limitations=limitations
            )
        except (InvalidInput, UnicodeError, struct.error):
            return Inspection(
                self.check_id,
                "FAILED",
                "Malformed, unsafe or over-limit ZIP index.",
                limitations=limitations,
            )
