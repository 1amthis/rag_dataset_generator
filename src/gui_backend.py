"""Backend logic for GUI interface - extracted from main.py."""

import os
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
