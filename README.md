<div align="center">

# `clickr`

### natural-language CLI for ClickHouse

Ask in English. Get SQL, results, charts. No syntax to memorize.

![tests](https://img.shields.io/badge/tests-46%20passing-yellow)

[![pypi](https://img.shields.io/pypi/v/clickr.svg)](https://pypi.org/project/clickr/)
[![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](#requirements)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

</div>

```text
$ clickr
clickr · connected to events.prod.clickhouse:9000

❯ which 10 users had the most activity last week?

  generated SQL ────────────────────────────────────────────
  SELECT user_id, count() AS events
  FROM events
  WHERE event_time >= now() - INTERVAL 7 DAY
  GROUP BY user_id
  ORDER BY events DESC
  LIMIT 10

  results ──────────────────────────────────────────────────
  user_id          events
  ──────────────   ──────
  u_4f3a91         18,422
  u_8c1e02         12,805
  ...

  84 ms · 12 GB scanned · cached
```

`clickr` is a CLI for ClickHouse® that translates plain English into SQL, runs it, and shows you the answer. Works with **local LLMs** (Ollama, llama.cpp, the bundled small model) and **cloud LLMs** (OpenAI, Anthropic). Your queries and schema never leave the machine on the local path.

## ✦ Install

```bash
pipx install clickr        # recommended — keeps deps isolated
pip  install clickr        # if you don't have pipx
curl -fsSL https://clickr.dev/install.sh | sh    # one-liner (downloads the standalone binary)
```

First run drops you into an interactive setup: ClickHouse connection, model choice, optional API keys.

## ✦ What it does

| Want to | Run |
|---|---|
| Ask a one-shot question | `clickr query "top 10 users by activity"` |
| Pull up a table summary | `clickr analyze users` |
| Drop into an interactive REPL | `clickr` |
| Bulk-load a CSV | `clickr load-data users.csv users` |
| Render a chart from a query | `clickr query "..." --chart bar` |

`clickr --help` for the full surface. Every subcommand emits the SQL it generated and the timing — no black box.

## ✦ How it works

```text
your question
     ↓
[ schema introspection ]   reads CREATE TABLE, top values, row counts
     ↓
[ LLM (local or cloud) ]   prompts include the schema + few-shot SQL
     ↓
[ generated SQL ]          shown to you before execution
     ↓
[ ClickHouse ]             clickhouse-connect over TCP/HTTP
     ↓
[ formatted results ]      table, chart, or JSON
```

The LLM only sees your schema and the question, never your data rows. Local-only mode (`--provider ollama` or the bundled engine) keeps the whole loop on the machine.

## ✦ Requirements

- Python 3.8 or newer
- A reachable ClickHouse instance (local or cloud)
- One of: Ollama / llama.cpp running locally, an OpenAI API key, or an Anthropic API key
- ~3.5 GB free for the bundled local model (first run only)

## ✦ Configuration

Lives in `~/.config/clickr/clickr-config.json`. Contains the ClickHouse DSN, the active model provider, and any API tokens. Edit by hand or rerun `clickr login` for the wizard.

Provider matrix:

| Provider | Latency | Cost | Privacy |
|---|---|---|---|
| Local (Ollama / llama.cpp / bundled) | medium | free | data never leaves the machine |
| OpenAI | fast | per-token | schema sent to OpenAI |
| Anthropic | fast | per-token | schema sent to Anthropic |

## ✦ Develop

```bash
git clone https://github.com/erphq/clickr.git
cd clickr
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python main.py
```

Build standalone binaries (PyInstaller, signed on macOS):

```bash
./build_installers.sh
```

Outputs land in `builds/` for macOS Intel / Apple Silicon, Linux x64, Windows x64.

## ✦ Roadmap

- Multi-engine support (DuckDB, BigQuery, Snowflake) behind the same NL interface
- Query-cost preview before execution (cardinality + bytes-scanned estimate)
- Saved-query namespace with shareable URLs
- Chart-in-terminal via `kitty +icat` and Sixel
- Web companion (read-only) for sharing the same query history

Open an issue with a use case if you want one of these prioritized.

## ✦ Trademark notice

This project is not affiliated with, endorsed by, or sponsored by ClickHouse, Inc. **ClickHouse®** is a registered trademark of ClickHouse, Inc. The name appears here descriptively ("a CLI **for** ClickHouse") under their [trademark policy](https://clickhouse.com/legal/trademark-policy).

## ✦ License

MIT. See [LICENSE](./LICENSE).
