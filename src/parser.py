"""Document parser module using ChunkNorris."""

import os
from pathlib import Path
from typing import List, Dict, Any
import tiktoken

from chunknorris.parsers import (
    MarkdownParser,
    HTMLParser,
    PdfParser,
    DocxParser,
    CSVParser,
    ExcelParser,
)
from chunknorris.chunkers import MarkdownChunker
from chunknorris.pipelines import BasePipeline


class DocumentParser:
    """Parse documents and manage token limits."""

    SUPPORTED_FORMATS = {
        '.md': MarkdownParser,
        '.html': HTMLParser,
        '.pdf': PdfParser,
        '.docx': DocxParser,
        '.csv': CSVParser,
        '.xlsx': ExcelParser,
    }

    def __init__(self, max_tokens: int = 10000, model: str = "gpt-4"):
        """Initialize parser with token limit.

        Args:
            max_tokens: Maximum tokens to include from document
            model: Model name for tokenizer (default: gpt-4)
        """
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model(model)
        self.chunker = MarkdownChunker()

    def get_parser(self, file_path: str) -> Any:
        """Get appropriate parser for file type.

        Args:
            file_path: Path to document file

        Returns:
            Parser instance for the file type

        Raises:
            ValueError: If file format is not supported
        """
        ext = Path(file_path).suffix.lower()
        parser_class = self.SUPPORTED_FORMATS.get(ext)

        if parser_class is None:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: {list(self.SUPPORTED_FORMATS.keys())}"
            )

        # Special handling for PDF to disable OCR by default
        if ext == '.pdf':
            return parser_class(use_ocr="never")

        return parser_class()

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def _extract_chunk_text(self, chunk: Any) -> str:
        """Extract text from a ChunkNorris chunk object.

        ChunkNorris Chunk objects have a get_text() method that properly
        converts the internal MarkdownLine list to a readable string.

        Args:
            chunk: Chunk object from ChunkNorris

        Returns:
            Extracted text as string
        """
        # ChunkNorris Chunk objects have a get_text() method
        if hasattr(chunk, 'get_text'):
            return chunk.get_text()

        # If it's a list (of MarkdownLine objects), extract text from each
        if isinstance(chunk, list):
            lines = []
            for item in chunk:
                if hasattr(item, 'text'):
                    lines.append(item.text)
                else:
                    lines.append(str(item))
            return '\n'.join(lines)

        # If it has a content attribute that is a list
        if hasattr(chunk, 'content') and isinstance(chunk.content, list):
            lines = []
            for item in chunk.content:
                if hasattr(item, 'text'):
                    lines.append(item.text)
                else:
                    lines.append(str(item))
            return '\n'.join(lines)

        # If content is already a string
        if hasattr(chunk, 'content'):
            return str(chunk.content)

        # If it has a text attribute
        if hasattr(chunk, 'text'):
            return str(chunk.text)

        # Last resort: convert to string
        return str(chunk)

    def truncate_to_token_limit(self, chunks: List[Any]) -> tuple[str, List[Dict], int]:
        """Truncate chunks to stay within token limit.

        Args:
            chunks: List of chunk objects from ChunkNorris

        Returns:
            Tuple of (combined_text, chunk_metadata, total_tokens)
        """
        combined_text = ""
        chunk_metadata = []
        total_tokens = 0

        for i, chunk in enumerate(chunks):
            # Extract text from chunk - ChunkNorris returns different types
            chunk_text = self._extract_chunk_text(chunk)

            chunk_tokens = self.count_tokens(chunk_text)

            # Check if adding this chunk would exceed limit
            if total_tokens + chunk_tokens > self.max_tokens:
                # Try to add partial chunk if we have room
                remaining_tokens = self.max_tokens - total_tokens
                if remaining_tokens > 100:  # Only add if we have meaningful space
                    # Truncate the chunk text
                    tokens = self.encoding.encode(chunk_text)
                    truncated_tokens = tokens[:remaining_tokens]
                    truncated_text = self.encoding.decode(truncated_tokens)

                    combined_text += truncated_text + "\n\n"
                    chunk_metadata.append({
                        'chunk_id': i,
                        'tokens': remaining_tokens,
                        'truncated': True
                    })
                    total_tokens += remaining_tokens
                break

            combined_text += chunk_text + "\n\n"
            chunk_metadata.append({
                'chunk_id': i,
                'tokens': chunk_tokens,
                'truncated': False
            })
            total_tokens += chunk_tokens

        return combined_text.strip(), chunk_metadata, total_tokens

    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """Parse document and return processed content.

        Args:
            file_path: Path to document file

        Returns:
            Dictionary containing:
                - content: Processed text (truncated to token limit)
                - metadata: Document metadata
                - chunks: Chunk metadata
                - total_tokens: Total tokens in processed content
                - source_file: Original file path
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get appropriate parser
        parser = self.get_parser(file_path)

        # Create pipeline
        pipeline = BasePipeline(parser=parser, chunker=self.chunker)

        # Parse and chunk document
        chunks = pipeline.chunk_file(filepath=file_path)

        # Truncate to token limit
        content, chunk_metadata, total_tokens = self.truncate_to_token_limit(chunks)

        return {
            'content': content,
            'metadata': {
                'file_name': Path(file_path).name,
                'file_type': Path(file_path).suffix,
                'total_chunks': len(chunks),
                'included_chunks': len(chunk_metadata),
            },
            'chunks': chunk_metadata,
            'total_tokens': total_tokens,
            'source_file': file_path,
        }
