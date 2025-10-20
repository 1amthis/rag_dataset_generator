# Quick Start Guide

Get started with the RAG Dataset Generator in 5 minutes!

## 1. Setup (One-time)

Run the setup script:
```bash
./setup.sh
```

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Configure

Edit `.env` and add your OpenAI API key:
```bash
nano .env
```

Set at minimum:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

## 3. Run

Activate the virtual environment:
```bash
source venv/bin/activate
```

Process a document:
```bash
python3 src/main.py path/to/your/document.pdf
```

The output will be saved in the `output/` directory as CSV by default.

## Common Use Cases

### Process a single PDF
```bash
python3 src/main.py research_paper.pdf
```

### Process all documents in a folder
```bash
python3 src/main.py documents/
```

### Process with multiple output formats
```bash
python3 src/main.py document.pdf --format csv json jsonl
```

### Estimate cost first
```bash
python3 src/main.py large_document.pdf --estimate-cost
```

### Verbose output to see progress
```bash
python3 src/main.py document.pdf --verbose
```

### Process with custom token limit (reduce costs)
```bash
python3 src/main.py document.pdf --max-tokens 5000
```

## Output

The tool generates datasets with:
- **question**: Natural questions a naive user might ask
- **answer**: Accurate answers from the document
- **citation**: Exact text snippets supporting the answer

See `examples/` for sample output files.

## Troubleshooting

**"OPENAI_API_KEY not found"**
- Make sure you've set your API key in `.env`

**"Unsupported file format"**
- Only `.md`, `.html`, `.pdf`, `.docx`, `.csv`, `.xlsx` are supported

**Import errors**
- Make sure you've activated the virtual environment: `source venv/bin/activate`

## Next Steps

- See [README.md](README.md) for full documentation
- Check [examples/](examples/) for sample outputs
- Adjust settings in `.env` for your use case
