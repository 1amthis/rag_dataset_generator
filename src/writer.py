"""Output writer module supporting multiple formats."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd


class DatasetWriter:
    """Write Q/A/Citation dataset to multiple formats."""

    SUPPORTED_FORMATS = ['csv', 'json', 'jsonl']

    def __init__(self, output_dir: str = 'output'):
        """Initialize writer with output directory.

        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def flatten_triple(self, triple: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """Flatten a triple dictionary for tabular output.

        Args:
            triple: Q/A/Citation triple with metadata
            source_file: Source document file path

        Returns:
            Flattened dictionary suitable for CSV/tabular format
        """
        metadata = triple.get('metadata', {})

        return {
            'document_id': Path(source_file).stem,
            'source_file': source_file,
            'file_type': metadata.get('file_type', ''),
            'question': triple['question'],
            'answer': triple['answer'],
            'citation': triple['citation'],
            'citation_valid': triple.get('citation_valid', True),
            'total_chunks': metadata.get('total_chunks', 0),
            'included_chunks': metadata.get('included_chunks', 0),
            'timestamp': datetime.now().isoformat(),
        }

    def write_csv(
        self,
        triples: List[Dict[str, Any]],
        source_file: str,
        output_filename: str = None
    ) -> str:
        """Write triples to CSV format.

        Args:
            triples: List of Q/A/Citation triples
            source_file: Source document file path
            output_filename: Custom output filename (optional)

        Returns:
            Path to created CSV file
        """
        if not triples:
            print("Warning: No triples to write")
            return None

        # Flatten triples
        flattened = [self.flatten_triple(t, source_file) for t in triples]

        # Create DataFrame
        df = pd.DataFrame(flattened)

        # Generate filename
        if output_filename is None:
            doc_id = Path(source_file).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{doc_id}_{timestamp}.csv"

        output_path = self.output_dir / output_filename

        # Write CSV
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)

        return str(output_path)

    def write_json(
        self,
        triples: List[Dict[str, Any]],
        source_file: str,
        output_filename: str = None
    ) -> str:
        """Write triples to JSON format.

        Args:
            triples: List of Q/A/Citation triples
            source_file: Source document file path
            output_filename: Custom output filename (optional)

        Returns:
            Path to created JSON file
        """
        if not triples:
            print("Warning: No triples to write")
            return None

        # Flatten triples
        flattened = [self.flatten_triple(t, source_file) for t in triples]

        # Generate filename
        if output_filename is None:
            doc_id = Path(source_file).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{doc_id}_{timestamp}.json"

        output_path = self.output_dir / output_filename

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(flattened, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def write_jsonl(
        self,
        triples: List[Dict[str, Any]],
        source_file: str,
        output_filename: str = None
    ) -> str:
        """Write triples to JSONL format (one JSON object per line).

        Args:
            triples: List of Q/A/Citation triples
            source_file: Source document file path
            output_filename: Custom output filename (optional)

        Returns:
            Path to created JSONL file
        """
        if not triples:
            print("Warning: No triples to write")
            return None

        # Flatten triples
        flattened = [self.flatten_triple(t, source_file) for t in triples]

        # Generate filename
        if output_filename is None:
            doc_id = Path(source_file).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{doc_id}_{timestamp}.jsonl"

        output_path = self.output_dir / output_filename

        # Write JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in flattened:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        return str(output_path)

    def write(
        self,
        triples: List[Dict[str, Any]],
        source_file: str,
        format: str = 'csv',
        output_filename: str = None
    ) -> str:
        """Write triples to specified format.

        Args:
            triples: List of Q/A/Citation triples
            source_file: Source document file path
            format: Output format ('csv', 'json', or 'jsonl')
            output_filename: Custom output filename (optional)

        Returns:
            Path to created file

        Raises:
            ValueError: If format is not supported
        """
        format = format.lower()

        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        if format == 'csv':
            return self.write_csv(triples, source_file, output_filename)
        elif format == 'json':
            return self.write_json(triples, source_file, output_filename)
        elif format == 'jsonl':
            return self.write_jsonl(triples, source_file, output_filename)

    def write_multiple_formats(
        self,
        triples: List[Dict[str, Any]],
        source_file: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """Write triples to multiple formats.

        Args:
            triples: List of Q/A/Citation triples
            source_file: Source document file path
            formats: List of formats to write (default: all supported)

        Returns:
            Dictionary mapping format to output file path
        """
        if formats is None:
            formats = self.SUPPORTED_FORMATS

        output_files = {}
        for fmt in formats:
            try:
                output_path = self.write(triples, source_file, format=fmt)
                if output_path:
                    output_files[fmt] = output_path
            except Exception as e:
                print(f"Error writing {fmt} format: {e}")

        return output_files
