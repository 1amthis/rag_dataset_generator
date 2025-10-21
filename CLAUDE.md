# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG Dataset Generator - A Python tool that generates question/answer/citation triples from documents for RAG evaluation using ChunkNorris for parsing and GPT-4.1 for generation.

**Two interfaces:**
- **GUI (Gradio)**: Browser-based drag-and-drop interface for non-technical users (includes a working citation viewer with alert-style popups)
- **CLI**: Command-line interface for automation and advanced use

**Repository diagnostic files:**
- `ALTERNATIVES.md` - Analysis of Citation Viewer issues and potential solutions
- `diagnose_issue.py` - Diagnostic script for testing HTML generation
- `test_gradio_html.py` - Test script for Gradio HTML component compatibility
- `diagnostic_output.html` - Sample HTML output for debugging

## Development Setup

```bash
# Setup environment (first time)
./setup.sh

# Or manually
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
```

## Running the Tool

### GUI (for non-technical users)
```bash
# Launch browser-based interface
./run_gui.sh         # Mac/Linux
run_gui.bat          # Windows

# Opens at http://127.0.0.1:7860
```

### CLI (for developers/automation)
```bash
# Basic usage
source venv/bin/activate
python3 src/main.py path/to/document.pdf

# With options
python3 src/main.py document.pdf --verbose
python3 src/main.py document.pdf --format all
python3 src/main.py documents/ --recursive --estimate-cost
```

## Architecture & Data Flow

The system follows a three-stage pipeline:

### 1. Document Parsing (parser.py)
- **ChunkNorris Integration**: Uses ChunkNorris library for multi-format parsing
- **Format Support**: .md, .html, .pdf, .docx, .csv, .xlsx
- **Token Management**: Truncates to 10k tokens (configurable) at chunk boundaries
- **Key Detail**: PDF parsing uses `use_ocr="never"` by default (line 66) to avoid OCR dependencies
- **Chunk Extraction**: Tries multiple attributes (`content`, `text`, or `str()`) to handle different ChunkNorris versions

**Critical Flow**:
```
get_parser(file_path) → parser_class(use_ocr="never" for PDFs)
  ↓
BasePipeline(parser, chunker) → chunk_file()
  ↓
truncate_to_token_limit(chunks) → stops at 10k tokens on chunk boundaries
  ↓
Returns: {content, metadata, chunks, total_tokens, source_file}
```

### 2. Q/A/Citation Generation (generator.py)
- **LLM Integration**: OpenAI API with configurable model (default: gpt-4.1)
- **Adaptive Generation**: Generates 0-10 triples based on document content
- **Citation Validation**: Verifies citations exist verbatim in source (whitespace-normalized)
- **Prompt Strategy**: Instructs LLM to generate "naive user" questions with exact citations

**Critical Flow**:
```
create_prompt(document_content) → structured JSON request
  ↓
OpenAI API call → temperature=0.7, system role enforces JSON output
  ↓
parse_llm_response() → extracts JSON (handles markdown wrapping)
  ↓
validate_citation() → checks exact match with whitespace normalization
  ↓
Returns: [{question, answer, citation, citation_valid, metadata}]
```

### 3. Output Writing (writer.py)
- **Multi-format Support**: CSV, JSON, JSONL
- **Flattening**: Converts nested triple structure to tabular format
- **Filename Convention**: `{document_id}_{timestamp}.{format}`
- **Output Schema**: document_id, source_file, file_type, question, answer, citation, citation_valid, total_chunks, included_chunks, timestamp

## Key Configuration

All settings in `.env`:
- `OPENAI_API_KEY`: Required for LLM calls
- `MODEL_NAME`: Default gpt-4.1
- `MAX_TOKENS`: Default 10000 (controls document truncation)
- `MIN_TRIPLES` / `MAX_TRIPLES`: Generation bounds (0-10)
- `TEMPERATURE`: LLM sampling (0.7)

## Important Implementation Details

### ChunkNorris Parser Compatibility
- **Parser names are case-sensitive**: Use `HTMLParser` not `HtmlParser`
- **Chunk object structure varies**: Code defensively checks for `.content`, `.text`, or falls back to `str()`
- **PDF OCR disabled by default**: Avoids Tesseract dependency unless user needs OCR

### Token Counting
- Uses `tiktoken` with model-specific encoding
- Token counting model must match OpenAI model for accuracy
- Truncation preserves complete chunks when possible (lines 110-126 in parser.py)

### Citation Validation
- Normalizes whitespace before comparison: `' '.join(text.split())`
- Marks as invalid if LLM paraphrases instead of exact quote
- Invalid citations are flagged in output but not rejected

### Error Handling
- Parser errors: Returns empty/error in process_document (main.py:134-140)
- LLM errors: Returns empty list, prints warning (generator.py:186-188)
- Missing files: Raises FileNotFoundError (parser.py:152-153)

## Data Flow Summary

```
Input Document
    ↓
[DocumentParser]
    → ChunkNorris parses & chunks
    → Truncate to 10k tokens at boundaries
    → Return: {content, metadata, chunks}
    ↓
[QACitationGenerator]
    → Build prompt for "naive user" questions
    → OpenAI API generates Q/A/Citation triples
    → Validate citations against source
    → Return: [{question, answer, citation, citation_valid}]
    ↓
[DatasetWriter]
    → Flatten triples with metadata
    → Write to CSV/JSON/JSONL
    → Return: output file paths
```

## GUI Architecture

The GUI is built with Gradio and separated into:

### gui_gradio.py (UI Layer)
- Gradio interface definition with multiple tabs
- Event handlers for buttons/inputs
- Visual components (sliders, file upload, tables)
- Document preview functionality
- Help tab with documentation
- Runs on port 7860 by default

**Main tabs:**
- **Generate Dataset**: File upload and processing controls
- **Document Preview**: Preview parsed text before processing
- **Citation Viewer**: Highlights citations in the source document and shows the related Q/A pairs in a browser alert when clicked
- **Help**: Usage documentation

### gui_backend.py (Business Logic)
- `DatasetGeneratorBackend` class encapsulates all processing
- Reuses parser.py, generator.py, writer.py
- Handles config loading/saving (API keys → .env)
- File validation before processing
- Progress callbacks for UI updates
- Result formatting for display

**Key methods:**
- `initialize_components()` - setup parser/generator/writer
- `process_documents()` - batch processing with progress
- `validate_files()` - check file formats
- `format_results_summary()` - generate summary text
- `get_triples_dataframe()` - format for table display
- `get_parsed_previews()` - preview parsed document text before processing
- `load_dataset()` - load existing dataset files from output directory
- `list_output_files()` - list all generated dataset files
- `get_source_document_content()` - parse source documents for citation viewer
- `create_highlighted_html()` - generate HTML with citation highlights and inline Q/A popups
- `get_citation_colors()` - generate color palette for citation highlighting
- `_escape_html()` - HTML escaping utility

**Note on estimate_cost():**
This method is located in `generator.py` (line 233), not in gui_backend.py. It estimates API costs based on token count.

## Testing Without API Key

To test parsing without LLM costs:

**CLI:**
1. Comment out generator call in main.py (lines 102-105)
2. Run with `--verbose` to see parsed content and token counts
3. Use `--estimate-cost` to preview costs before processing

**GUI:**
1. Upload files and use "Estimate Cost" button (requires API key for initialization)
2. Or modify gui_backend.py to skip generator initialization for testing

## Known Limitations

### Citation Viewer Interactions

**Status:** Functional with lightweight pop-up alerts

**Behavior:**
- Citations are highlighted inline and clicking a highlight opens a native `alert()` with the related question and answer.
- The viewer intentionally skips citations that cannot be matched back to the source text after whitespace normalization, so a dataset containing only invalid citations will render the "No valid citations found" message.

**Trade-offs:**
1. Alerts interrupt the browsing flow; they are the simplest interaction that works reliably inside `gr.HTML`.
2. There is no side-panel or rich modal today—enhancements would require more complex component wiring or exporting to standalone HTML.
3. Matching is tolerant of whitespace differences but still sensitive to heavy paraphrasing or punctuation changes.

**Future Improvements:**
- Replace alerts with a custom Gradio component (e.g., side panel) that shows the Q/A when a citation is clicked.
- Offer an "Include invalid citations" toggle for debugging datasets.
- Export a standalone HTML report with richer interactivity when needed.
