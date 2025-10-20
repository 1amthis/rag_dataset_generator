# RAG Dataset Generator

A Python tool for generating question/answer/citation triples from documents for RAG (Retrieval Augmented Generation) evaluation. Uses ChunkNorris for document parsing and GPT-4.1 for generating high-quality training data.

**🎨 Now with User-Friendly GUI!** Perfect for non-technical users - see [GUI Quick Start](#gui-for-non-technical-users)

## Features

- **Multi-format Document Support**: Parse `.md`, `.html`, `.pdf`, `.docx`, `.csv`, `.xlsx`
- **User-Friendly GUI**: Drag-and-drop interface for non-technical users (NEW!)
- **Smart Token Management**: Automatically truncate documents to 10k tokens max to control costs
- **Intelligent Generation**: GPT-4.1 generates 0-10 Q/A/Citation triples per document based on content
- **Citation Validation**: Ensures citations are exact text snippets from source documents
- **Multiple Output Formats**: Export to CSV, JSON, or JSONL
- **Cost Estimation**: Preview estimated API costs before processing
- **Batch Processing**: Process single files or entire directories

## Installation

1. Clone or download this repository

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Configuration

Edit `.env` file with your settings:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (defaults shown)
MODEL_NAME=gpt-4.1
MAX_TOKENS=10000
TEMPERATURE=0.7
MIN_TRIPLES=0
MAX_TRIPLES=10
OUTPUT_FORMAT=csv
OUTPUT_DIR=output
```

## Usage

### GUI for Non-Technical Users

**Easiest way to get started!** The GUI provides a browser-based interface with drag-and-drop file upload.

**Launch the GUI:**

**Windows:**
```bash
run_gui.bat
```

**Mac/Linux:**
```bash
./run_gui.sh
```

The GUI will open automatically in your browser. See [GUI_QUICKSTART.md](GUI_QUICKSTART.md) for detailed instructions.

**GUI Features:**
- 📁 Drag & drop document upload
- 🔑 API key configuration (saved locally)
- ⚙️ Visual sliders for all settings
- 💰 Cost estimation before processing
- 📊 Live results preview
- ⬇️ One-click download

---

### Command Line Interface (CLI)

For advanced users and automation. See [QUICKSTART.md](QUICKSTART.md) for CLI guide.

**Basic Usage:**

Process a single document:
```bash
python3 src/main.py path/to/document.pdf
```

Process all documents in a directory:
```bash
python3 src/main.py path/to/documents/
```

Process recursively:
```bash
python3 src/main.py path/to/documents/ --recursive
```

### Advanced Options

**Multiple output formats:**
```bash
python3 src/main.py document.pdf --format csv json jsonl
# Or use 'all' for all formats
python3 src/main.py document.pdf --format all
```

**Custom output directory:**
```bash
python3 src/main.py document.pdf --output-dir my_datasets
```

**Override token limit:**
```bash
python3 src/main.py document.pdf --max-tokens 5000
```

**Estimate costs before processing:**
```bash
python3 src/main.py documents/ --estimate-cost
```

**Verbose output:**
```bash
python3 src/main.py document.pdf --verbose
```

**Use different model:**
```bash
python3 src/main.py document.pdf --model gpt-4-turbo
```

### Full CLI Reference

```
usage: main.py [-h] [-r] [-f {csv,json,jsonl,all} [{csv,json,jsonl,all} ...]]
               [-o OUTPUT_DIR] [--max-tokens MAX_TOKENS] [--model MODEL]
               [--api-key API_KEY] [--estimate-cost] [-v]
               input

positional arguments:
  input                 Input file or directory path

optional arguments:
  -h, --help            show this help message and exit
  -r, --recursive       Process directories recursively
  -f, --format          Output format(s) (default: csv)
  -o, --output-dir      Output directory (default: from .env or "output")
  --max-tokens          Maximum tokens per document (default: from .env or 10000)
  --model               OpenAI model name (default: from .env or "gpt-4.1")
  --api-key             OpenAI API key (default: from .env)
  --estimate-cost       Estimate cost before processing
  -v, --verbose         Verbose output
```

## Output Format

### CSV Output

The CSV output includes the following columns:

- `document_id`: Unique identifier from filename
- `source_file`: Path to source document
- `file_type`: Document file extension
- `question`: Generated question
- `answer`: Generated answer
- `citation`: Exact text snippet from document
- `citation_valid`: Whether citation exists verbatim in source
- `total_chunks`: Total chunks in original document
- `included_chunks`: Chunks included within token limit
- `timestamp`: Generation timestamp

### JSON/JSONL Output

Same fields as CSV, formatted as JSON array (JSON) or newline-delimited JSON objects (JSONL).

## How It Works

1. **Document Parsing**: ChunkNorris parses documents into structured chunks
2. **Token Truncation**: Content is truncated to stay within 10k token limit
3. **Q/A Generation**: GPT-4.1 generates contextual questions a naive user might ask
4. **Citation Extraction**: Each answer includes an exact text snippet from the source
5. **Validation**: Citations are verified to exist verbatim in the document
6. **Export**: Results are saved in your chosen format(s)

## Question Generation Strategy

The tool generates questions that:
- Are natural and conversational
- Could be asked by someone unfamiliar with the topic (naive user)
- Vary in complexity and topic coverage
- Are answerable from the document content
- Range from 0-10 questions depending on document length and richness

## Cost Management

- Documents are automatically truncated to 10,000 tokens max
- Use `--estimate-cost` to preview API costs before processing
- Costs are based on GPT-4.1 pricing (check OpenAI's current rates)
- Shorter documents generate fewer questions, reducing costs

## Examples

See `examples/` directory for sample output files.

## Troubleshooting

**API Key Error:**
```
Error: OPENAI_API_KEY not found
```
Solution: Set your API key in `.env` file or use `--api-key` argument

**Unsupported File Format:**
```
Warning: Unsupported file format: .txt
```
Solution: Only `.md`, `.html`, `.pdf`, `.docx`, `.csv`, `.xlsx` are supported

**Invalid Citations:**
```
Warning: X invalid citations detected
```
Solution: This is informational. Invalid citations are marked in output with `citation_valid=False`

## Development

### Project Structure

```
dataset_generator/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── parser.py            # Document parsing & token management
│   ├── generator.py         # LLM-based Q/A/Citation generation
│   ├── writer.py            # Multi-format output writer
│   ├── main.py              # CLI interface
│   ├── gui_gradio.py        # Gradio GUI interface (NEW!)
│   └── gui_backend.py       # GUI backend logic (NEW!)
├── examples/                 # Sample outputs
├── requirements.txt          # Python dependencies
├── .env.example             # Configuration template
├── run_gui.sh / .bat        # GUI launch scripts (NEW!)
├── GUI_QUICKSTART.md        # GUI user guide (NEW!)
├── QUICKSTART.md            # CLI quick start guide
└── README.md                # This file
```

### Dependencies

- **chunknorris**: Document parsing
- **openai**: GPT-4.1 API
- **tiktoken**: Token counting
- **pandas**: Data manipulation
- **python-dotenv**: Environment configuration
- **tqdm**: Progress bars
- **gradio**: Web-based GUI (optional, for GUI only)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review ChunkNorris documentation: https://wikit-ai.github.io/chunknorris/
3. Open an issue on the repository
# rag_dataset_generator
