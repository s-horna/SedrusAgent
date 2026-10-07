"""Ingest pipeline: fingerprint -> extract -> resolve -> commit.

Extraction (the slow LLM call) runs concurrently across documents. Resolution
and commit stay sequential, in sorted path order, so the resulting state is
the same as ingesting the documents one at a time.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

from ledgerline import state as st
from ledgerline.extract import ExtractionResult, Extractor
from ledgerline.resolve import apply_extraction

SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".md"}
DEFAULT_WORKERS = 8


@dataclass
class IngestReport:
    path: Path
    outcome: Literal["ingested", "skipped", "failed"]
    detail: str = ""
    questions: list[str] = field(default_factory=list)


def iter_documents(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(
        p for p in path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES and not p.name.startswith(".")
    )


def ingest(
    path: Path,
    state_path: Path,
    extractor: Extractor,
    on_report: Callable[[IngestReport], None] | None = None,
    workers: int = DEFAULT_WORKERS,
) -> list[IngestReport]:
    """Ingest each document under path; on_report is called as each one finishes."""
    reports: list[IngestReport] = []

    def report(r: IngestReport) -> None:
        reports.append(r)
        if on_report:
            on_report(r)

    state = st.load(state_path)
    pending: list[tuple[Path, str, str]] = []  # (path, digest, doc_id)
    queued: set[str] = set()
    for doc_path in iter_documents(path):
        digest = st.file_sha256(doc_path)
        doc_id = f"doc_{digest[:16]}"
        if doc_id in state.documents or doc_id in queued:
            report(IngestReport(doc_path, "skipped", "already ingested"))
            continue
        queued.add(doc_id)
        pending.append((doc_path, digest, doc_id))

    if not pending:
        return reports

    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(pending)))) as pool:
        futures: list[Future[ExtractionResult]] = [
            pool.submit(extractor.extract, doc_path) for doc_path, _, _ in pending
        ]
        # Apply in submission order so resolution is deterministic.
        for (doc_path, digest, doc_id), future in zip(pending, futures):
            try:
                result = future.result()
            except Exception as exc:  # not recorded, so a retry will re-attempt it
                report(IngestReport(doc_path, "failed", f"{type(exc).__name__}: {exc}"))
                continue

            questions = apply_extraction(state, doc_id, result)
            state.documents[doc_id] = st.Document(
                id=doc_id,
                filename=doc_path.name,
                sha256=digest,
                doc_type=result.doc_type,
                doc_date=result.doc_date,
                ingested_at=datetime.now(timezone.utc),
                extraction_model=extractor.model,
                status="needs_review" if questions else "processed",
            )
            st.save(state, state_path)  # commit per document so progress survives a crash
            report(IngestReport(doc_path, "ingested", result.doc_type, questions))
    return reports
