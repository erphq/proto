# clickr — natural-language CLI for ClickHouse

> Ask questions, generate SQL, get insights. Without writing SQL.

`clickr` is a CLI agent that lets you interact with ClickHouse® databases in plain English. It analyzes your tables, generates the right SQL, runs it, and shows you the answer. Works with local LLMs (Ollama, llama.cpp) or cloud ones (OpenAI, Anthropic).

## Features

- 🤖 **AI-Powered**: Natural language interface powered by local or cloud AI models
- 📊 **Smart Analysis**: Automatic table analysis and data insights
- 🔍 **Query Generation**: Convert questions to optimized SQL queries
- 📈 **Data Visualization**: Generate charts and visualizations from your data
- ⚡ **Fast Setup**: One-command installation, no Python knowledge required
- 🔒 **Privacy-First**: Option to run completely locally with local AI models
- 🚀 **Cross-Platform**: Works on macOS (Intel/Apple Silicon), Linux, and Windows
- 📦 **Easy Installation**: Install via pipx, pip, or one-liner script

## Quick Start

### Install Proto

```bash
curl -fsSL https://clickr.dev/install.sh | sh
```

### Start Using Proto

```bash
clickr
```

Follow the interactive onboarding to configure your ClickHouse connection and AI provider.

## Installation Options

### Using pipx (Recommended)
```bash
pipx install clickr
```

### Using pip
```bash
pip install clickr
```

### One-liner (Legacy)
```bash
curl -fsSL https://clickr.dev/install.sh | sh
```

## Usage Examples

```bash
# Start interactive chat
clickr

# Execute a single query
clickr query "Show me the top 10 users by activity"

# Analyze a specific table
clickr analyze users

# Load data from a file
clickr load-data users.csv users
```

## Configuration

Proto supports multiple AI providers:

- **Local LLM**: Run completely offline with local models
- **Local LLM**: Built-in ClickHouse AI model (no API keys needed)
- **OpenAI**: Direct OpenAI API integration

Configuration is stored in `~/.config/clickr/clickr-config.json`.

## System Requirements

- macOS 10.15+ or Linux
- ClickHouse database (local or cloud)
- AI provider (Local LLM built-in)
- ~3.5GB free space for AI model (first run)

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/erphq/clickr.git
cd clickr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Proto
python main.py
```

### Building Standalone Binaries

```bash
./build_installers.sh
```

This creates platform-specific binaries in the `builds/` directory.

## Architecture

```
clickr/
├── agent/           # Core AI agent logic
├── config/          # Configuration management
├── providers/       # AI provider integrations
├── tools/           # Database and data tools
├── ui/              # User interface components
├── utils/           # Utility functions
└── main.py          # Entry point
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://clickr.dev)
- 🐛 [Report Issues](https://github.com/erphq/clickr/issues)
- 💬 [Discussions](https://github.com/erphq/clickr/discussions)

## Roadmap

- [ ] Web interface
- [ ] More AI providers
- [ ] Advanced data visualization
- [ ] Query optimization suggestions
- [ ] Multi-database support

## Trademark notice

This project is not affiliated with, endorsed by, or sponsored by ClickHouse, Inc. **ClickHouse®** is a registered trademark of ClickHouse, Inc. The use of the name in this project's description and documentation is purely descriptive ("a CLI **for** ClickHouse") under their [trademark policy](https://clickhouse.com/legal/trademark-policy).
