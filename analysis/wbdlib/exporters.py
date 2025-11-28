"""Helpers that export plot source data to Excel workbooks."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence, Tuple

import pandas as pd

from .formatting import slugify_filename
from .io import safe_write_excel

SheetLike = Mapping[str, pd.DataFrame] | Iterable[Tuple[str, pd.DataFrame]]


class PlotDataExporter:
    """Write per-plot datasets to Excel using consistent naming rules."""

    def __init__(
        self,
        base_path: str | Path,
        *,
        notebook_name: str | None = None,
        default_folder_parts: Sequence[str] | None = None,
        static_metadata: Mapping[str, object] | None = None,
    ) -> None:
        root = Path(base_path)
        if notebook_name:
            root = root / slugify_filename(
                notebook_name, placeholder="notebook"
            )
        self.base_path = root
        self.default_folder_parts = list(default_folder_parts or [])
        self.static_metadata: MutableMapping[str, object] = dict(
            static_metadata or {}
        )
        self.last_path: Path | None = None

    def _resolve_folder(self, folder_parts: Sequence[str] | None) -> Path:
        path = self.base_path
        combined: list[str] = list(self.default_folder_parts)
        if folder_parts:
            combined.extend(folder_parts)
        for part in combined:
            path = path / slugify_filename(part, placeholder="section")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _compose_metadata(
        self,
        *,
        title: str,
        part: str,
        section: str | None,
        extra: Mapping[str, object] | None,
    ) -> Mapping[str, object]:
        payload: MutableMapping[str, object] = dict(self.static_metadata)
        payload.update({"title": title, "part": part})
        if section:
            payload["section"] = section
        if extra:
            payload.update(extra)
        return payload

    def __call__(
        self,
        *,
        title: str,
        part: str,
        data_frames: SheetLike,
        section: str | None = None,
        filename_suffix: str | None = None,
        metadata: Mapping[str, object] | None = None,
        folder_parts: Sequence[str] | None = None,
    ) -> Path:
        """Export ``data_frames`` to a workbook named after ``title``."""

        export_dir = self._resolve_folder(folder_parts)
        filename = slugify_filename(title, suffix=filename_suffix)
        workbook_path = export_dir / f"{filename}.xlsx"
        merged_metadata = self._compose_metadata(
            title=title,
            part=part,
            section=section,
            extra=metadata,
        )
        self.last_path = safe_write_excel(
            data_frames,
            workbook_path,
            metadata=merged_metadata,
        )
        return self.last_path


__all__ = ["PlotDataExporter"]
