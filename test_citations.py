#!/usr/bin/env python3
"""Test script to debug citation validation issues."""

import csv

def normalize_whitespace(text):
    """Normalize whitespace for comparison (same as in generator.py)."""
    return ' '.join(text.split())

def test_citation_validation(csv_file):
    """Test citation validation on actual output."""
    print(f"Analyzing citations in: {csv_file}\n")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        invalid_count = 0
        total_count = 0

        for row in reader:
            total_count += 1
            citation_valid = row['citation_valid'] == 'True'

            if not citation_valid:
                invalid_count += 1
                print(f"=" * 80)
                print(f"INVALID CITATION #{invalid_count}")
                print(f"=" * 80)
                print(f"\nQuestion: {row['question']}")
                print(f"\nAnswer: {row['answer']}")
                print(f"\nCitation (from LLM):")
                print(f"{row['citation'][:500]}..." if len(row['citation']) > 500 else row['citation'])
                print(f"\nCitation length: {len(row['citation'])} characters")

                # Try to find similar text
                citation_normalized = normalize_whitespace(row['citation'])
                print(f"\nNormalized citation (first 200 chars):")
                print(citation_normalized[:200])
                print()

    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total triples: {total_count}")
    print(f"Invalid citations: {invalid_count}")
    print(f"Validity rate: {((total_count - invalid_count) / total_count * 100):.1f}%")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_citation_validation(sys.argv[1])
    else:
        test_citation_validation("output/How People Use ChatGPT_20251016_110518.csv")
