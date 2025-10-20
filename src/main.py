#!/usr/bin/env python3
"""Main CLI for RAG dataset generator."""

import argparse
import os
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from tqdm import tqdm

from parser import DocumentParser
from generator import QACitationGenerator
from writer import DatasetWriter


def load_config():
    """Load configuration from .env file."""
    load_dotenv()

    config = {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'model': os.getenv('MODEL_NAME', 'gpt-4.1'),
        'max_tokens': int(os.getenv('MAX_TOKENS', 10000)),
        'temperature': float(os.getenv('TEMPERATURE', 0.7)),
        'min_triples': int(os.getenv('MIN_TRIPLES', 0)),
        'max_triples': int(os.getenv('MAX_TRIPLES', 10)),
        'output_format': os.getenv('OUTPUT_FORMAT', 'csv'),
        'output_dir': os.getenv('OUTPUT_DIR', 'output'),
    }

    return config


def find_documents(input_path: str, recursive: bool = False) -> List[str]:
    """Find all supported documents in path.

    Args:
        input_path: File or directory path
        recursive: Whether to search recursively in directories

    Returns:
        List of document file paths
    """
    path = Path(input_path)
    supported_extensions = {'.md', '.html', '.pdf', '.docx', '.csv', '.xlsx'}

    if path.is_file():
        if path.suffix.lower() in supported_extensions:
            return [str(path)]
        else:
            print(f"Warning: Unsupported file format: {path.suffix}")
            return []

    elif path.is_dir():
        documents = []
        pattern = '**/*' if recursive else '*'

        for ext in supported_extensions:
            documents.extend(str(p) for p in path.glob(f'{pattern}{ext}'))

        return sorted(documents)

    else:
        print(f"Error: Path not found: {input_path}")
        return []


def process_document(
    file_path: str,
    parser: DocumentParser,
    generator: QACitationGenerator,
    writer: DatasetWriter,
    output_formats: List[str],
    verbose: bool = False
) -> dict:
    """Process a single document.

    Args:
        file_path: Path to document
        parser: DocumentParser instance
        generator: QACitationGenerator instance
        writer: DatasetWriter instance
        output_formats: List of output formats
        verbose: Whether to print verbose output

    Returns:
        Dictionary with processing results
    """
    try:
        if verbose:
            print(f"\nProcessing: {file_path}")

        # Parse document
        parsed = parser.parse_document(file_path)

        if verbose:
            print(f"  Tokens: {parsed['total_tokens']}")
            print(f"  Chunks: {parsed['metadata']['included_chunks']}/{parsed['metadata']['total_chunks']}")

        # Generate triples
        triples = generator.generate_triples(
            parsed['content'],
            parsed['metadata']
        )

        if verbose:
            print(f"  Generated {len(triples)} Q/A/Citation triples")

        # Validate citations
        invalid_citations = sum(1 for t in triples if not t.get('citation_valid', True))
        if invalid_citations > 0 and verbose:
            print(f"  Warning: {invalid_citations} invalid citations detected")

        # Write output
        output_files = writer.write_multiple_formats(
            triples,
            file_path,
            formats=output_formats
        )

        if verbose:
            for fmt, path in output_files.items():
                print(f"  Wrote {fmt}: {path}")

        return {
            'success': True,
            'file': file_path,
            'triples_count': len(triples),
            'invalid_citations': invalid_citations,
            'output_files': output_files,
        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return {
            'success': False,
            'file': file_path,
            'error': str(e),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate Q/A/Citation dataset for RAG evaluation'
    )

    parser.add_argument(
        'input',
        help='Input file or directory path'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process directories recursively'
    )

    parser.add_argument(
        '-f', '--format',
        nargs='+',
        choices=['csv', 'json', 'jsonl', 'all'],
        default=['csv'],
        help='Output format(s) (default: csv)'
    )

    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory (default: from .env or "output")'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        help='Maximum tokens per document (default: from .env or 10000)'
    )

    parser.add_argument(
        '--model',
        help='OpenAI model name (default: from .env or "gpt-4.1")'
    )

    parser.add_argument(
        '--api-key',
        help='OpenAI API key (default: from .env)'
    )

    parser.add_argument(
        '--estimate-cost',
        action='store_true',
        help='Estimate cost before processing'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Load config
    config = load_config()

    # Override config with command-line arguments
    if args.api_key:
        config['api_key'] = args.api_key
    if args.model:
        config['model'] = args.model
    if args.max_tokens:
        config['max_tokens'] = args.max_tokens
    if args.output_dir:
        config['output_dir'] = args.output_dir

    # Validate API key
    if not config['api_key']:
        print("Error: OPENAI_API_KEY not found. Set it in .env file or use --api-key")
        sys.exit(1)

    # Handle 'all' format option
    if 'all' in args.format:
        output_formats = ['csv', 'json', 'jsonl']
    else:
        output_formats = args.format

    # Find documents
    documents = find_documents(args.input, args.recursive)

    if not documents:
        print("No documents found to process")
        sys.exit(1)

    print(f"Found {len(documents)} document(s)")

    # Initialize components
    doc_parser = DocumentParser(
        max_tokens=config['max_tokens'],
        model=config['model']
    )

    qa_generator = QACitationGenerator(
        api_key=config['api_key'],
        model=config['model'],
        temperature=config['temperature'],
        min_triples=config['min_triples'],
        max_triples=config['max_triples'],
    )

    dataset_writer = DatasetWriter(output_dir=config['output_dir'])

    # Estimate cost if requested
    if args.estimate_cost:
        total_tokens = 0
        for doc_path in documents:
            try:
                parsed = doc_parser.parse_document(doc_path)
                total_tokens += parsed['total_tokens']
            except Exception as e:
                print(f"Warning: Could not estimate tokens for {doc_path}: {e}")

        estimated_cost = qa_generator.estimate_cost(total_tokens)
        print(f"\nEstimated cost: ${estimated_cost:.4f}")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted")
            sys.exit(0)

    # Process documents
    results = []
    for doc_path in tqdm(documents, desc="Processing documents", disable=args.verbose):
        result = process_document(
            doc_path,
            doc_parser,
            qa_generator,
            dataset_writer,
            output_formats,
            verbose=args.verbose
        )
        results.append(result)

    # Summary
    successful = sum(1 for r in results if r['success'])
    total_triples = sum(r.get('triples_count', 0) for r in results if r['success'])

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total documents: {len(documents)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(documents) - successful}")
    print(f"  Total Q/A/Citation triples: {total_triples}")
    print(f"  Output directory: {config['output_dir']}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
