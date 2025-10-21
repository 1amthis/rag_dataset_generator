"""Backend logic for GUI interface - extracted from main.py."""

import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv, set_key

from parser import DocumentParser
from generator import QACitationGenerator
from writer import DatasetWriter


class DatasetGeneratorBackend:
    """Backend for processing documents and generating Q/A/Citation datasets."""

    SUPPORTED_EXTENSIONS = {'.md', '.html', '.pdf', '.docx', '.csv', '.xlsx'}

    def __init__(self):
        """Initialize backend."""
        self.config = self.load_config()
        self.parser = None
        self.generator = None
        self.writer = None

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from .env file."""
        load_dotenv()

        config = {
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'model': os.getenv('MODEL_NAME', 'gpt-4.1'),
            'max_tokens': int(os.getenv('MAX_TOKENS', 10000)),
            'temperature': float(os.getenv('TEMPERATURE', 0.7)),
            'min_triples': int(os.getenv('MIN_TRIPLES', 0)),
            'max_triples': int(os.getenv('MAX_TRIPLES', 10)),
            'output_format': os.getenv('OUTPUT_FORMAT', 'csv'),
            'output_dir': os.getenv('OUTPUT_DIR', 'output'),
        }

        return config

    def save_api_key(self, api_key: str) -> None:
        """Save API key to .env file.

        Args:
            api_key: OpenAI API key
        """
        env_path = Path('.env')

        # Create .env if it doesn't exist
        if not env_path.exists():
            env_path.write_text('# OpenAI Configuration\n')

        # Update API key
        set_key(str(env_path), 'OPENAI_API_KEY', api_key)
        self.config['api_key'] = api_key

    def initialize_components(
        self,
        api_key: str,
        model: str,
        max_tokens: int,
        temperature: float,
        min_triples: int,
        max_triples: int,
        output_dir: str
    ) -> None:
        """Initialize processing components with config.

        Args:
            api_key: OpenAI API key
            model: Model name
            max_tokens: Maximum tokens per document
            temperature: Sampling temperature
            min_triples: Minimum Q/A triples
            max_triples: Maximum Q/A triples
            output_dir: Output directory
        """
        self.parser = DocumentParser(
            max_tokens=max_tokens,
            model=model
        )

        self.generator = QACitationGenerator(
            api_key=api_key,
            model=model,
            temperature=temperature,
            min_triples=min_triples,
            max_triples=max_triples,
        )

        self.writer = DatasetWriter(output_dir=output_dir)

    def validate_files(self, file_paths: List[str]) -> Tuple[List[str], List[str]]:
        """Validate uploaded files.

        Args:
            file_paths: List of file paths

        Returns:
            Tuple of (valid_files, invalid_files)
        """
        valid_files = []
        invalid_files = []

        for file_path in file_paths:
            path = Path(file_path)
            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                valid_files.append(file_path)
            else:
                invalid_files.append(f"{path.name} (unsupported format)")

        return valid_files, invalid_files

    def get_parsed_previews(self, file_paths: List[str], show_full: bool = False) -> Dict[str, Dict[str, Any]]:
        """Get parsed text previews for multiple documents.

        Args:
            file_paths: List of document paths
            show_full: If True, return full content; if False, return preview (default)

        Returns:
            Dictionary mapping file names to parsed data with preview
        """
        if not self.parser:
            raise ValueError("Parser not initialized")

        previews = {}
        for file_path in file_paths:
            try:
                parsed = self.parser.parse_document(file_path)
                file_name = Path(file_path).name

                # Create preview or use full content
                if show_full:
                    content_preview = parsed['content']
                else:
                    content_preview = parsed['content'][:2000]
                    if len(parsed['content']) > 2000:
                        content_preview += "\n\n... (truncated for display)"

                previews[file_name] = {
                    'content': parsed['content'],
                    'preview': content_preview,
                    'tokens': parsed['total_tokens'],
                    'chunks': len(parsed.get('chunks', [])),
                    'file_type': parsed['metadata'].get('file_type', 'unknown'),
                    'is_truncated': not show_full and len(parsed['content']) > 2000
                }
            except Exception as e:
                previews[Path(file_path).name] = {
                    'content': '',
                    'preview': f"Error parsing: {str(e)}",
                    'tokens': 0,
                    'chunks': 0,
                    'file_type': 'error',
                    'is_truncated': False
                }

        return previews

    def process_document(
        self,
        file_path: str,
        output_formats: List[str]
    ) -> Dict[str, Any]:
        """Process a single document.

        Args:
            file_path: Path to document
            output_formats: List of output formats

        Returns:
            Dictionary with processing results
        """
        if not self.parser or not self.generator or not self.writer:
            raise ValueError("Components not initialized")

        try:
            # Parse document
            parsed = self.parser.parse_document(file_path)

            # Generate triples
            triples = self.generator.generate_triples(
                parsed['content'],
                parsed['metadata']
            )

            # Validate citations
            invalid_citations = sum(1 for t in triples if not t.get('citation_valid', True))

            # Write output
            output_files = self.writer.write_multiple_formats(
                triples,
                file_path,
                formats=output_formats
            )

            return {
                'success': True,
                'file': Path(file_path).name,
                'tokens': parsed['total_tokens'],
                'triples_count': len(triples),
                'invalid_citations': invalid_citations,
                'output_files': output_files,
                'triples': triples,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'file': Path(file_path).name,
                'tokens': 0,
                'triples_count': 0,
                'invalid_citations': 0,
                'output_files': {},
                'triples': [],
                'error': str(e)
            }

    def process_documents(
        self,
        file_paths: List[str],
        output_formats: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple documents.

        Args:
            file_paths: List of document paths
            output_formats: List of output formats
            progress_callback: Optional callback for progress updates

        Returns:
            List of processing results
        """
        results = []

        for i, file_path in enumerate(file_paths):
            result = self.process_document(file_path, output_formats)
            results.append(result)

            if progress_callback:
                progress = (i + 1) / len(file_paths)
                progress_callback(progress, f"Processed {i + 1}/{len(file_paths)}")

        return results

    def format_results_summary(self, results: List[Dict[str, Any]]) -> str:
        """Format processing results as summary text.

        Args:
            results: List of processing results

        Returns:
            Formatted summary string
        """
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        total_triples = sum(r.get('triples_count', 0) for r in results if r['success'])
        total_tokens = sum(r.get('tokens', 0) for r in results if r['success'])

        summary = f"""
## Processing Summary

- **Total Documents:** {len(results)}
- **Successful:** {successful}
- **Failed:** {failed}
- **Total Q/A Triples:** {total_triples}
- **Total Tokens Processed:** {total_tokens:,}

### Details:
"""

        for result in results:
            status = "✓" if result['success'] else "✗"
            summary += f"\n{status} **{result['file']}**"

            if result['success']:
                summary += f" - {result['triples_count']} questions, {result['tokens']} tokens"
                if result['invalid_citations'] > 0:
                    summary += f" ({result['invalid_citations']} invalid citations)"
            else:
                summary += f" - Error: {result['error']}"

        return summary

    def get_triples_dataframe(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Convert results to list of dicts for display.

        Args:
            results: List of processing results

        Returns:
            List of flattened triple dictionaries
        """
        display_data = []

        for result in results:
            if result['success']:
                for triple in result['triples']:
                    display_data.append({
                        'Document': result['file'],
                        'Question': triple['question'],
                        'Answer': triple['answer'],
                        'Citation': triple['citation'][:100] + '...' if len(triple['citation']) > 100 else triple['citation'],
                        'Valid': '✓' if triple.get('citation_valid', True) else '✗'
                    })

        return display_data

    def list_output_files(self, output_dir: str = 'output') -> List[str]:
        """List all dataset output files.

        Args:
            output_dir: Output directory to search

        Returns:
            List of output file paths
        """
        output_path = Path(output_dir)
        if not output_path.exists():
            return []

        files = []
        for ext in ['.csv', '.json', '.jsonl']:
            files.extend([str(f) for f in output_path.glob(f'*{ext}')])

        return sorted(files, reverse=True)  # Most recent first

    def load_dataset(self, file_path: str) -> Tuple[List[Dict[str, Any]], str]:
        """Load a dataset file and return triples.

        Args:
            file_path: Path to dataset file

        Returns:
            Tuple of (triples_list, source_document_name)
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        triples = []
        source_doc = ""

        if extension == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not source_doc and row.get('source_file'):
                        source_doc = row['source_file']

                    triples.append({
                        'question': row.get('question', ''),
                        'answer': row.get('answer', ''),
                        'citation': row.get('citation', ''),
                        'citation_valid': row.get('citation_valid', 'true').lower() == 'true'
                    })

        elif extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    triples = data
                    if triples and 'metadata' in triples[0]:
                        source_doc = triples[0]['metadata'].get('source_file', '')

        elif extension == '.jsonl':
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    triple = json.loads(line)
                    triples.append(triple)
                    if not source_doc and 'metadata' in triple:
                        source_doc = triple['metadata'].get('source_file', '')

        return triples, source_doc

    def get_citation_colors(self, num_citations: int) -> List[str]:
        """Generate color palette for citations.

        Args:
            num_citations: Number of unique colors needed

        Returns:
            List of color codes (hex or rgba)
        """
        # Predefined color palette with good contrast
        base_colors = [
            'rgba(255, 235, 59, 0.4)',   # Yellow
            'rgba(156, 39, 176, 0.3)',   # Purple
            'rgba(0, 188, 212, 0.3)',    # Cyan
            'rgba(255, 152, 0, 0.3)',    # Orange
            'rgba(76, 175, 80, 0.3)',    # Green
            'rgba(244, 67, 54, 0.3)',    # Red
            'rgba(63, 81, 181, 0.3)',    # Indigo
            'rgba(233, 30, 99, 0.3)',    # Pink
            'rgba(0, 150, 136, 0.3)',    # Teal
            'rgba(255, 193, 7, 0.3)',    # Amber
            'rgba(121, 85, 72, 0.3)',    # Brown
            'rgba(96, 125, 139, 0.3)',   # Blue Grey
        ]

        # Repeat colors if needed
        colors = []
        for i in range(num_citations):
            colors.append(base_colors[i % len(base_colors)])

        return colors

    def create_highlighted_html(
        self,
        document_content: str,
        triples: List[Dict[str, Any]],
        hide_invalid: bool = True
    ) -> str:
        """Create HTML with highlighted citations.

        Args:
            document_content: Full document text
            triples: List of Q/A/Citation triples
            hide_invalid: If True, only highlight valid citations

        Returns:
            HTML string with highlighted citations
        """
        # Filter triples if hiding invalid
        if hide_invalid:
            valid_triples = [t for t in triples if t.get('citation_valid', True)]
        else:
            valid_triples = triples

        if not valid_triples:
            return "<div style='padding: 20px;'>No valid citations found in dataset.</div>"

        # Get colors for citations
        colors = self.get_citation_colors(len(valid_triples))

        # Normalize text for matching
        def normalize(text):
            return ' '.join(text.split())

        # Find citation positions in original text
        highlights = []  # List of dicts with position info

        # Pre-compute normalized document for approximate matching
        normalized_doc = normalize(document_content)

        for idx, triple in enumerate(valid_triples):
            citation = triple['citation']

            # Try direct match first (fast path)
            pos = document_content.find(citation)

            if pos != -1:
                # Found exact match
                highlights.append({
                    'start': pos,
                    'end': pos + len(citation),
                    'id': idx,
                    'color': colors[idx],
                    'question': triple['question'],
                    'answer': triple['answer'],
                    'citation': citation
                })
                continue

            # Try whitespace-flexible matching using regex
            citation_escaped = re.escape(citation)
            citation_pattern = re.sub(r'\\\s+', r'\\s+', citation_escaped)
            match = re.search(citation_pattern, document_content)

            if match:
                highlights.append({
                    'start': match.start(),
                    'end': match.end(),
                    'id': idx,
                    'color': colors[idx],
                    'question': triple['question'],
                    'answer': triple['answer'],
                    'citation': citation
                })
                continue

            # Fallback: approximate matching using normalized text and word counts
            normalized_citation = normalize(citation)
            if not normalized_citation:
                continue

            norm_pos = normalized_doc.find(normalized_citation)
            if norm_pos == -1:
                continue

            words_before = normalized_doc[:norm_pos].split()
            target_word_count = len(words_before)

            word_count = 0
            char_pos = 0
            for i, char in enumerate(document_content):
                if char.isspace() and i > 0 and not document_content[i - 1].isspace():
                    word_count += 1
                    if word_count >= target_word_count:
                        char_pos = i
                        break

            citation_word_count = len(normalized_citation.split())
            end_word_count = 0
            end_pos = char_pos

            for i in range(char_pos, len(document_content)):
                if (document_content[i].isspace() and i > char_pos
                        and not document_content[i - 1].isspace()):
                    end_word_count += 1
                    if end_word_count >= citation_word_count:
                        end_pos = i
                        break

            if end_pos == char_pos:
                end_pos = min(char_pos + len(citation), len(document_content))

            highlights.append({
                'start': char_pos,
                'end': end_pos,
                'id': idx,
                'color': colors[idx],
                'question': triple['question'],
                'answer': triple['answer'],
                'citation': citation
            })

        # Sort highlights by position
        highlights.sort(key=lambda x: x['start'])

        # Build HTML sections (CSS only; no embedded script for compatibility)
        html = """
        <style>
            .citation-viewer {
                font-family: Georgia, serif;
                line-height: 1.8;
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .citation-mark {
                cursor: pointer;
                padding: 2px 4px;
                border-radius: 3px;
                transition: all 0.2s;
                position: relative;
                border: 1px solid rgba(0,0,0,0.1);
            }
            .citation-mark:hover {
                opacity: 0.8;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                transform: scale(1.02);
            }
            .citation-number {
                font-size: 0.75em;
                font-weight: bold;
                vertical-align: super;
                margin-left: 2px;
                color: #333;
            }
            .legend {
                margin-bottom: 20px;
                padding: 15px;
                background: #f5f5f5;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
            .legend-item {
                display: inline-block;
                margin: 5px 10px;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 0.9em;
                border: 1px solid rgba(0,0,0,0.1);
            }
            .document-content {
                white-space: pre-wrap;
                word-wrap: break-word;
            }
        </style>
        <div class="citation-viewer">
        """

        # Create set of found citation IDs
        found_ids = {h['id'] for h in highlights}

        # Add legend - only show citations that were found
        html += '<div class="legend"><strong>📌 Citations:</strong> Click on highlighted text to view the question and answer<br><br>'
        if found_ids:
            for idx, triple in enumerate(valid_triples):
                if idx in found_ids:
                    color = colors[idx]
                    q_preview = triple['question'][:50] + '...' if len(triple['question']) > 50 else triple['question']
                    # Escape for HTML attributes
                    question_escaped = self._escape_html(triple['question'])
                    q_preview_escaped = self._escape_html(q_preview)
                    html += f'<span class="legend-item" style="background: {color};" title="{question_escaped}">[{idx + 1}] {q_preview_escaped}</span>'
        else:
            html += '<em style="color: #666;">No citations found in document</em>'
        html += '</div>'

        # Build document with highlighted sections
        html += '<div class="document-content">'

        # Insert highlights
        result = []
        last_pos = 0

        for highlight in highlights:
            # Add text before highlight
            result.append(self._escape_html(document_content[last_pos:highlight['start']]))

            # Add highlighted citation
            citation_text = self._escape_html(document_content[highlight['start']:highlight['end']])

            message = (
                f"Question #{highlight['id'] + 1}:\n\n"
                f"{highlight['question']}\n\n"
                f"Answer:\n\n"
                f"{highlight['answer']}"
            )
            message_js = json.dumps(message)
            message_attr = self._escape_html(message_js)

            result.append(
                f'<mark class="citation-mark" style="background: {highlight["color"]};" '
                f'onclick="alert({message_attr})" title="Click to view Q&A">'
                f'{citation_text}<span class="citation-number">[{highlight["id"] + 1}]</span></mark>'
            )

            last_pos = highlight['end']

        # Add remaining text
        result.append(self._escape_html(document_content[last_pos:]))

        html += ''.join(result)
        html += '</div></div>'

        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def get_source_document_content(self, source_file: str) -> str:
        """Get the parsed content of the source document.

        Args:
            source_file: Original source document filename

        Returns:
            Parsed document content
        """
        if not self.parser:
            raise ValueError("Parser not initialized. Please configure API key first.")

        # Try to find the source file
        # Check current directory and common locations
        search_paths = [
            Path(source_file),
            Path.cwd() / source_file,
            Path.cwd() / Path(source_file).name,
        ]

        for path in search_paths:
            if path.exists():
                try:
                    parsed = self.parser.parse_document(str(path))
                    return parsed['content']
                except Exception as e:
                    raise ValueError(f"Error parsing document: {str(e)}")

        raise FileNotFoundError(f"Source document not found: {source_file}")
