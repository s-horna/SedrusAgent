"""CLI: `ledgerline ingest <file-or-folder>` and `ledgerline entities`."""

from __future__ import annotations

from pathlib import Path

import typer

from ledgerline import state as st
from ledgerline.extract import OpenRouterExtractor
from ledgerline.ingest import DEFAULT_WORKERS, IngestReport, ingest as run_ingest

app = typer.Typer(no_args_is_help=True, add_completion=False)

StateOpt = typer.Option(
    Path("ledgerline_state.json"), "--state", envvar="LEDGERLINE_STATE", help="State JSON file."
)


@app.command()
def ingest(
    path: Path = typer.Argument(..., exists=True, help="Document or folder of documents."),
    state_path: Path = StateOpt,
    model: str = typer.Option(None, "--model", help="OpenRouter model ID."),
    workers: int = typer.Option(
        DEFAULT_WORKERS, "--workers", "-w", min=1, help="Documents to extract concurrently."
    ),
) -> None:
    """Read documents and update the household records."""
    try:
        extractor = OpenRouterExtractor(model=model)
    except RuntimeError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1)

    def show(r: IngestReport) -> None:
        color = {"ingested": "green", "skipped": "yellow", "failed": "red"}[r.outcome]
        line = f"{r.outcome:<9} {r.path.name}  {r.detail}"
        if r.questions:
            line += f"  ({len(r.questions)} question(s) raised)"
        typer.secho(line, fg=color)

    reports = run_ingest(path, state_path, extractor, on_report=show, workers=workers)
    if any(r.outcome == "failed" for r in reports):
        raise typer.Exit(1)


@app.command()
def entities(
    state_path: Path = StateOpt,
    as_json: bool = typer.Option(False, "--json", help="Print the raw state JSON."),
) -> None:
    """Print current records, their roles and sources, and open questions."""
    state = st.load(state_path)
    if as_json:
        typer.echo(state.model_dump_json(indent=2))
        return
    typer.echo(render(state))


def _sources(state: st.State, claim_ids: list[str]) -> str:
    names = []
    for cid in claim_ids:
        claim = state.claims.get(cid)
        doc = state.documents.get(claim.document) if claim else None
        label = doc.filename if doc else cid
        if claim and claim.page:
            label += f" p.{claim.page}"
        if label not in names:
            names.append(label)
    return ", ".join(names) or "-"


def _role_label(role: str) -> str:
    label = role.replace("_", " ")
    return label if label.endswith(" of") else f"{label} of"


def _role_suffix(state: st.State, r: st.Role) -> str:
    flag = "" if r.status == "active" else f" [{r.status.upper()}]"
    quals = "".join(f" {k}={v}" for k, v in r.qualifiers.items())
    dates = ""
    if r.effective_from or r.effective_to:
        dates = f" ({r.effective_from or '?'} to {r.effective_to or 'present'})"
    return f"{quals}{dates}{flag}  <- {_sources(state, r.sources)}"


def render(state: st.State) -> str:
    out: list[str] = []
    roles = sorted(state.roles.values(), key=lambda r: (r.status != "active", r.role))
    name = lambda eid: state.entities[eid].name if eid in state.entities else eid  # noqa: E731

    for kind, title in [("person", "PEOPLE"), ("trust", "TRUSTS"),
                        ("company", "COMPANIES"), ("account", "ACCOUNTS")]:
        ents = sorted((e for e in state.entities.values() if e.kind == kind), key=lambda e: e.name)
        out.append(f"\n== {title} ({len(ents)}) ==")
        for e in ents:
            ids = ", ".join(f"{k}={v}" for k, v in sorted(e.identifiers.items()))
            out.append(f"{e.id}  {e.name}" + (f"  [{ids}]" if ids else ""))
            if e.aliases:
                out.append(f"    aka: {', '.join(e.aliases)}")
            out.append(f"    source: {_sources(state, e.sources)}")
            for r in roles:
                if r.subject == e.id:
                    out.append(f"    -> {_role_label(r.role)} {name(r.object)}{_role_suffix(state, r)}")
            for r in roles:
                if r.object == e.id and kind != "person":
                    out.append(f"    <- {r.role.replace('_', ' ')}: {name(r.subject)}{_role_suffix(state, r)}")

    open_qs = [q for q in state.questions.values() if q.status == "open"]
    out.append(f"\n== WAITING ON A HUMAN ({len(open_qs)}) ==")
    for q in open_qs:
        doc = state.documents.get(q.raised_by)
        out.append(f"{q.id}  [{q.kind}] {q.summary}")
        out.append(f"    raised by: {doc.filename if doc else q.raised_by}"
                   f"; holds {len(q.blocking_claims)} claim(s)")
        for cid in q.blocking_claims:
            c = state.claims[cid]
            out.append(f'      - "{c.quote}"' + (f" (p.{c.page})" if c.page else ""))
    return "\n".join(out).lstrip("\n")


if __name__ == "__main__":
    app()
