# File operations
import csv
import hashlib
import json
import mimetypes
import os
import shutil
import stat
import zipfile
import tarfile
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class FileType(Enum):
    """Types of files."""

    TEXT = "text"
    BINARY = "binary"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    XML = "xml"
    MARKDOWN = "markdown"


@dataclass
class FileInfo:
    """Information about a file."""

    path: str
    name: str
    extension: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    is_directory: bool
    file_type: FileType
    permissions: str


class FileHandler:
    """File operations tool."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._base_path: Optional[Path] = None
        self._allowed_extensions: List[str] = []

    # ==================== Private Helpers ====================

    def _resolve(self, path: str) -> Path:
        """Resolve path relative to base_path if set.

        When a base_path is configured it is treated as a sandbox root: both
        absolute paths and `..` traversal are rejected if the resolved path
        would land outside of it, so callers can't escape the intended
        directory by passing an absolute path or `../../`.
        """
        p = Path(path)
        if self._base_path is None:
            return p

        candidate = p if p.is_absolute() else self._base_path / p
        resolved = candidate.resolve()
        base_resolved = self._base_path.resolve()
        if resolved != base_resolved and base_resolved not in resolved.parents:
            raise PermissionError(
                f"Path '{path}' resolves outside of the allowed base path '{base_resolved}'"
            )
        return resolved

    def _check_allowed(self, path: Path) -> None:
        """Raise if extension is not in allowlist."""
        if not self._allowed_extensions:
            return
        ext = path.suffix.lower()
        if ext not in self._allowed_extensions:
            raise PermissionError(
                f"Extension '{ext}' not in allowed list: {self._allowed_extensions}"
            )

    # ==================== Configuration ====================

    def set_base_path(self, path: str) -> None:
        """Set base path for relative operations."""
        self._base_path = Path(path)

    def get_base_path(self) -> Optional[str]:
        """Get base path."""
        return str(self._base_path) if self._base_path else None

    def set_allowed_extensions(self, extensions: List[str]) -> None:
        """Set allowed file extensions."""
        self._allowed_extensions = [e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions]

    def add_allowed_extension(self, extension: str) -> None:
        """Add allowed extension."""
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        if ext not in self._allowed_extensions:
            self._allowed_extensions.append(ext)

    # ==================== Read Operations ====================

    def read(self, path: str, encoding: str = "utf-8") -> str:
        """Read file as text."""
        p = self._resolve(path)
        self._check_allowed(p)
        return p.read_text(encoding=encoding)

    def read_binary(self, path: str) -> bytes:
        """Read file as binary."""
        p = self._resolve(path)
        return p.read_bytes()

    def read_lines(self, path: str, encoding: str = "utf-8") -> List[str]:
        """Read file lines."""
        return self.read(path, encoding).splitlines()

    def read_json(self, path: str) -> Dict[str, Any]:
        """Read JSON file."""
        return json.loads(self.read(path))

    def read_yaml(self, path: str) -> Dict[str, Any]:
        """Read YAML file."""
        import yaml  # optional dependency
        p = self._resolve(path)
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def read_csv(self, path: str, delimiter: str = ",") -> List[Dict[str, Any]]:
        """Read CSV file as list of dicts."""
        p = self._resolve(path)
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return [dict(row) for row in reader]

    def read_chunk(self, path: str, start: int, size: int) -> bytes:
        """Read chunk of file."""
        p = self._resolve(path)
        with p.open("rb") as f:
            f.seek(start)
            return f.read(size)

    def stream_read(self, path: str, chunk_size: int = 8192) -> Generator[bytes, None, None]:  # type: ignore[override]
        """Stream read large file."""
        p = self._resolve(path)
        with p.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    # ==================== Write Operations ====================

    def write(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """Write text to file."""
        p = self._resolve(path)
        self._check_allowed(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
        return True

    def write_binary(self, path: str, content: bytes) -> bool:
        """Write binary to file."""
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return True

    def write_lines(self, path: str, lines: List[str], encoding: str = "utf-8") -> bool:
        """Write lines to file."""
        return self.write(path, "\n".join(lines), encoding)

    def write_json(self, path: str, data: Dict[str, Any], indent: int = 2) -> bool:
        """Write JSON to file."""
        return self.write(path, json.dumps(data, indent=indent, default=str))

    def write_yaml(self, path: str, data: Dict[str, Any]) -> bool:
        """Write YAML to file."""
        import yaml
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True

    def write_csv(
        self, path: str, data: List[Dict[str, Any]], delimiter: str = ","
    ) -> bool:
        """Write CSV file."""
        if not data:
            return self.write(path, "")
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()), delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
        return True

    def append(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """Append to file."""
        p = self._resolve(path)
        self._check_allowed(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding=encoding) as f:
            f.write(content)
        return True

    def append_lines(
        self, path: str, lines: List[str], encoding: str = "utf-8"
    ) -> bool:
        """Append lines to file."""
        return self.append(path, "\n".join(lines) + "\n", encoding)

    # ==================== File Management ====================

    def create(self, path: str) -> bool:
        """Create empty file."""
        p = self._resolve(path)
        self._check_allowed(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch(exist_ok=True)
        return True

    def delete(self, path: str) -> bool:
        """Delete file."""
        p = self._resolve(path)
        self._check_allowed(p)
        if p.exists() and p.is_file():
            p.unlink()
            return True
        return False

    def copy(self, source: str, destination: str) -> bool:
        """Copy file."""
        src = self._resolve(source)
        dst = self._resolve(destination)
        self._check_allowed(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        return True

    def move(self, source: str, destination: str) -> bool:
        """Move file."""
        src = self._resolve(source)
        dst = self._resolve(destination)
        self._check_allowed(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True

    def rename(self, path: str, new_name: str) -> bool:
        """Rename file."""
        p = self._resolve(path)
        new_path = p.parent / new_name
        self._check_allowed(new_path)
        p.rename(new_path)
        return True

    def exists(self, path: str) -> bool:
        """Check if file exists."""
        return self._resolve(path).exists()

    def get_info(self, path: str) -> FileInfo:
        """Get file information."""
        p = self._resolve(path)
        s = p.stat()
        return FileInfo(
            path=str(p),
            name=p.name,
            extension=p.suffix,
            size_bytes=s.st_size,
            created_at=datetime.fromtimestamp(s.st_ctime),
            modified_at=datetime.fromtimestamp(s.st_mtime),
            is_directory=p.is_dir(),
            file_type=self.detect_file_type(path),
            permissions=oct(s.st_mode)[-3:],
        )

    def get_size(self, path: str) -> int:
        """Get file size in bytes."""
        return self._resolve(path).stat().st_size

    def get_checksum(self, path: str, algorithm: str = "md5") -> str:
        """Calculate file checksum."""
        h = hashlib.new(algorithm)
        p = self._resolve(path)
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    # ==================== Directory Operations ====================

    def create_directory(self, path: str) -> bool:
        """Create directory."""
        self._resolve(path).mkdir(parents=True, exist_ok=True)
        return True

    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete directory."""
        p = self._resolve(path)
        if not p.is_dir():
            return False
        if recursive:
            shutil.rmtree(str(p))
        else:
            p.rmdir()
        return True

    def list_directory(self, path: str) -> List[FileInfo]:
        """List directory contents."""
        p = self._resolve(path)
        return [self.get_info(str(child)) for child in sorted(p.iterdir())]

    def list_files(
        self, path: str, pattern: str = "*", recursive: bool = False
    ) -> List[str]:
        """List files matching pattern."""
        p = self._resolve(path)
        if recursive:
            matches = p.rglob(pattern)
        else:
            matches = p.glob(pattern)
        return [str(f) for f in matches if f.is_file()]

    def walk_directory(self, path: str) -> List[tuple]:
        """Walk directory tree."""
        p = self._resolve(path)
        return list(os.walk(str(p)))

    def directory_exists(self, path: str) -> bool:
        """Check if directory exists."""
        p = self._resolve(path)
        return p.exists() and p.is_dir()

    def get_directory_size(self, path: str) -> int:
        """Get total directory size."""
        total = 0
        for dirpath, _, filenames in self.walk_directory(path):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total

    # ==================== Search Operations ====================

    def search(self, path: str, pattern: str, recursive: bool = True) -> List[str]:
        """Search for files by pattern."""
        return self.list_files(path, pattern, recursive=recursive)

    def search_content(
        self, path: str, text: str, file_pattern: str = "*"
    ) -> List[Dict[str, Any]]:
        """Search file contents."""
        results: List[Dict[str, Any]] = []
        for fpath in self.list_files(path, file_pattern, recursive=True):
            try:
                content = Path(fpath).read_text(encoding="utf-8", errors="ignore")
                matches = []
                for lineno, line in enumerate(content.splitlines(), 1):
                    if text in line:
                        matches.append({"line": lineno, "text": line.strip()})
                if matches:
                    results.append({"file": fpath, "matches": matches})
            except Exception:
                pass
        return results

    def find_by_extension(
        self, path: str, extension: str, recursive: bool = True
    ) -> List[str]:
        """Find files by extension."""
        ext = extension if extension.startswith(".") else f".{extension}"
        return self.list_files(path, f"*{ext}", recursive=recursive)

    def find_by_size(
        self, path: str, min_bytes: int = 0, max_bytes: Optional[int] = None
    ) -> List[str]:
        """Find files by size range."""
        results = []
        for fpath in self.list_files(path, recursive=True):
            size = os.path.getsize(fpath)
            if size >= min_bytes and (max_bytes is None or size <= max_bytes):
                results.append(fpath)
        return results

    def find_by_date(
        self,
        path: str,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
    ) -> List[str]:
        """Find files by date range."""
        results = []
        for fpath in self.list_files(path, recursive=True):
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if after and mtime < after:
                continue
            if before and mtime > before:
                continue
            results.append(fpath)
        return results

    # ==================== Permissions ====================

    def get_permissions(self, path: str) -> str:
        """Get file permissions."""
        p = self._resolve(path)
        return oct(p.stat().st_mode)[-3:]

    def set_permissions(self, path: str, permissions: str) -> bool:
        """Set file permissions."""
        p = self._resolve(path)
        os.chmod(str(p), int(permissions, 8))
        return True

    def is_readable(self, path: str) -> bool:
        """Check if file is readable."""
        return os.access(str(self._resolve(path)), os.R_OK)

    def is_writable(self, path: str) -> bool:
        """Check if file is writable."""
        return os.access(str(self._resolve(path)), os.W_OK)

    # ==================== Utility ====================

    def detect_encoding(self, path: str) -> str:
        """Detect file encoding."""
        try:
            import chardet
            p = self._resolve(path)
            raw = p.read_bytes()
            result = chardet.detect(raw)
            return result.get("encoding") or "utf-8"
        except ImportError:
            return "utf-8"

    _EXTENSION_MAP: Dict[str, FileType] = {
        ".txt": FileType.TEXT,
        ".md": FileType.MARKDOWN,
        ".json": FileType.JSON,
        ".yaml": FileType.YAML,
        ".yml": FileType.YAML,
        ".csv": FileType.CSV,
        ".xml": FileType.XML,
        ".html": FileType.TEXT,
        ".htm": FileType.TEXT,
        ".py": FileType.TEXT,
        ".js": FileType.TEXT,
        ".ts": FileType.TEXT,
    }

    def detect_file_type(self, path: str) -> FileType:
        """Detect file type."""
        p = self._resolve(path)
        return self._EXTENSION_MAP.get(p.suffix.lower(), FileType.BINARY)

    def get_mime_type(self, path: str) -> str:
        """Get file MIME type."""
        p = self._resolve(path)
        mime, _ = mimetypes.guess_type(str(p))
        return mime or "application/octet-stream"

    def compress(self, paths: List[str], output: str, format: str = "zip") -> bool:
        """Compress files."""
        out_path = self._resolve(output)
        if format == "zip":
            with zipfile.ZipFile(str(out_path), "w", zipfile.ZIP_DEFLATED) as zf:
                for fpath in paths:
                    p = self._resolve(fpath)
                    zf.write(str(p), p.name)
        elif format in ("tar", "tar.gz", "tgz"):
            mode = "w:gz" if format in ("tar.gz", "tgz") else "w"
            with tarfile.open(str(out_path), mode) as tf:
                for fpath in paths:
                    p = self._resolve(fpath)
                    tf.add(str(p), arcname=p.name)
        else:
            raise ValueError(f"Unsupported format: {format}")
        return True

    def _assert_member_within(self, out_dir: Path, member_name: str) -> None:
        """Guard against Zip Slip: reject archive members that would extract
        outside of the destination directory (e.g. `../../etc/cron.d/evil`)."""
        target = (out_dir / member_name).resolve()
        if target != out_dir and out_dir not in target.parents:
            raise ValueError(
                f"Archive member '{member_name}' would extract outside of '{out_dir}' (zip slip)"
            )

    def decompress(self, path: str, output_dir: str) -> bool:
        """Decompress archive."""
        p = self._resolve(path)
        out = self._resolve(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        out_resolved = out.resolve()

        if zipfile.is_zipfile(str(p)):
            with zipfile.ZipFile(str(p), "r") as zf:
                for member in zf.namelist():
                    self._assert_member_within(out_resolved, member)
                zf.extractall(str(out_resolved))
        elif tarfile.is_tarfile(str(p)):
            with tarfile.open(str(p), "r:*") as tf:
                for member in tf.getmembers():
                    self._assert_member_within(out_resolved, member.name)
                tf.extractall(str(out_resolved))
        else:
            raise ValueError(f"Unknown archive format: {p}")
        return True
