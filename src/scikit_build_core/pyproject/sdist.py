from __future__ import annotations

import contextlib
import io
import os
import tarfile
from pathlib import Path

import pathspec
from pyproject_metadata import StandardMetadata

from .._compat import tomllib

__all__: list[str] = ["build_sdist"]


def __dir__() -> list[str]:
    return __all__


def build_sdist(
    sdist_directory: str,
    # pylint: disable-next=unused-argument
    config_settings: dict[str, list[str] | str] | None = None,
) -> str:
    sdist_dir = Path(sdist_directory)

    with Path("pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)

    metadata = StandardMetadata.from_pyproject(pyproject)
    pkg_info = metadata.as_rfc822()

    srcdirname = f"{metadata.name}-{metadata.version}"
    filename = f"{srcdirname}.tar.gz"

    exclude_spec: pathspec.PathSpec | None = None
    with contextlib.suppress(FileNotFoundError), open(
        ".gitignore", encoding="utf-8"
    ) as f:
        exclude_spec = pathspec.GitIgnoreSpec.from_lines(f.readlines())

    with tarfile.open(sdist_dir / filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for dirpath, _dirnames, filenames in os.walk("."):
            paths = (Path(dirpath) / fn for fn in filenames)
            if exclude_spec is not None:
                paths = (p for p in paths if not exclude_spec.match_file(p))
            for filepath in paths:
                tar.add(filepath, arcname=srcdirname / filepath)

        fileobj = io.BytesIO(bytes(pkg_info))
        fileobj.seek(0)
        tarinfo = tarfile.TarInfo(name=f"{srcdirname}/PKG-INFO")
        tarinfo.size = len(fileobj.getvalue())
        tar.addfile(tarinfo, fileobj)

    return filename