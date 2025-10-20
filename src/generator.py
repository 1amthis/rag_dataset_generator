"""LLM-based Q/A/Citation generator using OpenAI GPT-4.1."""

import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI


class QACitationGenerator:
    """Generate question/answer/citation triples using LLM."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1",
        temperature: float = 0.7,
        min_triples: int = 0,
        max_triples: int = 10,
    ):
        """Initialize generator with OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4.1)
            temperature: Sampling temperature (default: 0.7)
            min_triples: Minimum number of Q/A/Citation triples to generate
            max_triples: Maximum number of Q/A/Citation triples to generate
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.min_triples = min_triples
        self.max_triples = max_triples

    def create_prompt(self, document_content: str) -> str:
        """Create prompt for LLM to generate Q/A/Citation triples.

        Args:
            document_content: The document text to generate questions from

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are tasked with generating question-answer-citation triples from a document for RAG evaluation.

Generate between {self.min_triples} and {self.max_triples} question/answer/citation triples based on the content below. The questions should be natural questions that a naive user (someone unfamiliar with the topic) might ask.

IMPORTANT RULES:
1. Questions should be clear and specific
2. Answers should be accurate and based solely on the document
3. Citations MUST be EXACT text snippets from the document (word-for-word, no paraphrasing, same formatting)
4. Each citation should be a continuous passage from the document
5. The citation should support the answer directly
6. Generate only as many triples as make sense for the document (minimum {self.min_triples}, maximum {self.max_triples})
7. For short documents with limited content, generate fewer triples
8. Questions should vary in complexity and topic

Return your response as a JSON array with this exact structure:
[
  {{
    "question": "What is...?",
    "answer": "The answer based on the document...",
    "citation": "Exact text snippet from the document that supports this answer"
  }}
]

DOCUMENT:
{document_content}

Generate the Q/A/Citation triples in JSON format:"""

        return prompt

    def validate_citation(self, citation: str, document_content: str) -> bool:
        """Validate that citation exists verbatim in document.

        Handles cases where LLM includes ellipsis (...) to indicate omitted text.
        Will validate each part of the citation separated by ellipsis.
        Case-insensitive matching to handle capitalization variations.

        Args:
            citation: The citation text to validate
            document_content: The full document content

        Returns:
            True if citation exists exactly in document, False otherwise
        """
        # Normalize whitespace and case for comparison
        normalized_doc = ' '.join(document_content.split()).lower()
        normalized_citation = ' '.join(citation.split()).lower()

        # First try exact match (fastest)
        if normalized_citation in normalized_doc:
            return True

        # Handle ellipsis patterns: "...", "…", "[...]"
        # Split citation by various ellipsis patterns
        ellipsis_patterns = [
            r'\s*\.\.\.\s*',      # Standard three dots with optional spaces
            r'\s*…\s*',            # Unicode ellipsis
            r'\s*\[\.\.\.\]\s*',  # Bracketed ellipsis
            r'\s*\[…\]\s*',        # Bracketed unicode ellipsis
        ]

        for pattern in ellipsis_patterns:
            parts = re.split(pattern, normalized_citation)

            # If we found ellipsis, validate each part exists in order
            if len(parts) > 1:
                # Remove empty parts
                parts = [p.strip() for p in parts if p.strip()]

                if not parts:
                    return False

                # Check if all parts exist in the document in order
                last_pos = -1
                all_found = True

                for part in parts:
                    # Each part must exist in the document
                    pos = normalized_doc.find(part, last_pos + 1)
                    if pos == -1:
                        all_found = False
                        break
                    last_pos = pos

                if all_found:
                    return True

        return False

    def parse_llm_response(self, response_text: str) -> List[Dict[str, str]]:
        """Parse LLM response to extract Q/A/Citation triples.

        Args:
            response_text: Raw response text from LLM

        Returns:
            List of dictionaries with 'question', 'answer', 'citation' keys
        """
        try:
            # Try to find JSON in the response
            # Sometimes LLMs wrap JSON in markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for JSON array pattern
                json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text

            triples = json.loads(json_str)

            # Validate structure
            if not isinstance(triples, list):
                raise ValueError("Response is not a list")

            validated_triples = []
            for triple in triples:
                if all(key in triple for key in ['question', 'answer', 'citation']):
                    validated_triples.append({
                        'question': triple['question'].strip(),
                        'answer': triple['answer'].strip(),
                        'citation': triple['citation'].strip(),
                    })

            return validated_triples

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to parse LLM response: {e}")
            return []

    def generate_triples(
        self,
        document_content: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate Q/A/Citation triples for a document.

        Args:
            document_content: The processed document text
            document_metadata: Optional metadata about the document

        Returns:
            List of Q/A/Citation triples with validation info
        """
        # Create prompt
        prompt = self.create_prompt(document_content)

        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates training data for RAG systems. You always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Parse response
            triples = self.parse_llm_response(response_text)

            # Validate citations
            validated_triples = []
            for triple in triples:
                is_valid = self.validate_citation(triple['citation'], document_content)
                validated_triples.append({
                    **triple,
                    'citation_valid': is_valid,
                    'metadata': document_metadata or {}
                })

            return validated_triples

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return []

    def estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost for processing given token count.

        Args:
            total_tokens: Number of input tokens

        Returns:
            Estimated cost in USD
        """
        # GPT-4 pricing (approximate, check current pricing)
        # Input: ~$0.03 per 1K tokens
        # Output: ~$0.06 per 1K tokens
        # Assume output is roughly 2x input for Q/A generation

        input_cost = (total_tokens / 1000) * 0.03
        estimated_output_tokens = total_tokens * 2
        output_cost = (estimated_output_tokens / 1000) * 0.06

        return input_cost + output_cost
