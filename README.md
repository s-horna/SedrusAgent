# Ledgerline

An agent that ingests household records (trust agreements, statements, tax returns) into a structured state file. The LLM only reads each document and writes claims against a fixed schema. Deterministic code then applies those claims to the state. When a claim conflicts with the state or is ambiguous, the code opens a question for a human to resolve instead of writing it.

Supported inputs: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.txt`, `.md`.

## Setup

Requires Python 3.10+.

```powershell
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

Set your OpenRouter key in the shell. The CLI reads it from the environment and does not load `.env` on its own:

```powershell
$env:OPENROUTER_API_KEY = "sk-or-..."   # bash: export OPENROUTER_API_KEY=sk-or-...
```

Optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `LEDGERLINE_MODEL` | `google/gemini-3.8-flash` | OpenRouter model ID used for extraction |
| `LEDGERLINE_STATE` | `ledgerline_state.json` | Path to the state file |

## Commands

```powershell
# Ingest a single document or a folder of documents
ledgerline ingest <file-or-folder>

# Print people, trusts, companies, accounts, roles, sources, and open questions
ledgerline entities

# Print the raw state as JSON
ledgerline entities --json
```

Options for `ingest`:

- `--state PATH`: the state file to update (also accepted by `entities`)
- `--model ID`: override the model
- `--workers N` / `-w N`: number of documents extracted at once (default 8)

`ingest` exits with code 1 if any document fails.

## Examples

Synthetic test set (see `testdocs/README.md`). Point it at `docs/core`, not at `testdocs/` itself, because the folder's README would be ingested too:

```powershell
ledgerline ingest testdocs/docs/core --state testdocs_state.json
ledgerline entities --state testdocs_state.json
```

Real data, ingested batch by batch into one state file:

```powershell
ledgerline ingest SedrusDocs/batch1 --state SedrusDocs/state.json
ledgerline ingest SedrusDocs/batch2 --state SedrusDocs/state.json
ledgerline ingest SedrusDocs/batch3 --state SedrusDocs/state.json
ledgerline entities --state SedrusDocs/state.json
```

Snapshots of the state after each batch are saved in `SedrusDocs/`:

- `SedrusDocs/state_after_batch1.json`
- `SedrusDocs/state_after_batch2.json`
- `SedrusDocs/state_after_batch3.json`

`SedrusDocs/state.json` is the current state. It is identical to `state_after_batch3.json`.

## How it was built

To build this agent, I first prompted Claude Code (Opus 5.5 medium) with the problem and the deliverable and my initial thoughts on the kind of pipeline this should be, which was a simple agentic OCR that called tools to save/read the state. It pushed back right there noting that having an agent write the state itself was dangerous, and that the architecture should have the agent write claims based on each document in a defined schema and have a deterministic code act on this claim, either writing state or writing a 'question' for a human to resolve. Then I had it build an initial skeleton of the pipeline. At the same time, I had another agent going on building another set of docs that mimicked the initial docs that I was given to use for testing. With it I got the documents in testdocs as well as generator scripts which is nice for reproducibility. Then I tested with these generated docs and iterated until satisfied. The last test was with the real data.

## Questions for Ledgerline

What I would ask Ledgerline (as an engineer asking for requirements): To me this is more of a system of record for a human to have quick information, but it is not the source of truth (at least at this stage of development). I would ask if the end goal is to really make this the source of truth and if so we would need many more guardrails around security, injection, LLM going rogue, etc... I would ask what actions they feel comfortable delegating to an LLM and which they wouldn't. Right now this pipeline adds and ends roles in the state which can affect people's access to their money. I would ask if they feel comfortable sending these documents to an LLM-provider even if we have agreements not to use our data. If not we could self-host open source models. In an actual system of record, I wouldn't let an agent assign any roles to any trusts/accounts without human intervention (which can be as easy as confirming or declining what the agent found based on the document and quote).