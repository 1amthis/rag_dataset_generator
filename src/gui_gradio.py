#!/usr/bin/env python3
"""Gradio GUI for RAG Dataset Generator - User-friendly interface for non-technical users."""

import gradio as gr
from pathlib import Path
from typing import List, Tuple
import pandas as pd

from gui_backend import DatasetGeneratorBackend


# Initialize backend
backend = DatasetGeneratorBackend()


def process_files(
    files: List[str],
    api_key: str,
    model: str,
    max_tokens: int,
    temperature: float,
    min_questions: int,
    max_questions: int,
    output_formats: List[str],
    save_key: bool,
    progress=gr.Progress()
) -> Tuple[str, pd.DataFrame, List[str]]:
    """Process uploaded files and generate Q/A dataset.

    Args:
        files: List of uploaded file paths
        api_key: OpenAI API key
        model: Model name
        max_tokens: Maximum tokens per document
        temperature: Sampling temperature
        min_questions: Minimum questions to generate
        max_questions: Maximum questions to generate
        output_formats: List of output formats
        save_key: Whether to save API key
        progress: Gradio progress tracker

    Returns:
        Tuple of (summary_text, results_dataframe, download_file_paths)
    """
    # Validate inputs
    if not files:
        return "❌ No files uploaded. Please upload at least one document.", pd.DataFrame(), []

    if not api_key:
        return "❌ OpenAI API key is required. Please enter your API key.", pd.DataFrame(), []

    # Save API key if requested
    if save_key:
        backend.save_api_key(api_key)

    # Validate files
    progress(0, desc="Validating files...")
    valid_files, invalid_files = backend.validate_files([f.name for f in files])

    if invalid_files:
        invalid_msg = "\n".join([f"  - {f}" for f in invalid_files])
        return f"❌ Some files are not supported:\n{invalid_msg}\n\nSupported formats: .md, .html, .pdf, .docx, .csv, .xlsx", pd.DataFrame(), []

    if not valid_files:
        return "❌ No valid files to process.", pd.DataFrame(), []

    # Initialize components
    progress(0.1, desc="Initializing...")
    try:
        backend.initialize_components(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            min_triples=min_questions,
            max_triples=max_questions,
            output_dir='output'
        )
    except Exception as e:
        return f"❌ Error initializing: {str(e)}", pd.DataFrame(), []

    # Process documents
    progress(0.2, desc="Processing documents...")

    def progress_callback(prog, desc):
        progress(0.2 + prog * 0.7, desc=desc)

    results = backend.process_documents(
        valid_files,
        output_formats,
        progress_callback=progress_callback
    )

    # Generate summary
    progress(0.95, desc="Generating summary...")
    summary = backend.format_results_summary(results)

    # Generate results table
    triples_data = backend.get_triples_dataframe(results)
    df = pd.DataFrame(triples_data) if triples_data else pd.DataFrame()

    # Collect all output files for download
    download_files = []
    for result in results:
        if result['success'] and result['output_files']:
            for filepath in result['output_files'].values():
                download_files.append(filepath)

    progress(1.0, desc="Complete!")

    return summary, df, download_files


def preview_parsed_text(
    files: List[str],
    api_key: str,
    model: str,
    max_tokens: int,
    show_full: bool
) -> str:
    """Preview parsed document text.

    Args:
        files: List of uploaded files
        api_key: OpenAI API key
        model: Model name
        max_tokens: Maximum tokens per document
        show_full: Whether to show full content or preview

    Returns:
        Formatted markdown with parsed text previews
    """
    if not files:
        return "⚠️ No files uploaded."

    if not api_key:
        return "⚠️ API key required for parsing."

    # Validate files
    valid_files, invalid_files = backend.validate_files([f.name for f in files])

    if not valid_files:
        return "⚠️ No valid files to preview."

    # Initialize parser
    try:
        backend.initialize_components(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
            min_triples=0,
            max_triples=10,
            output_dir='output'
        )

        previews = backend.get_parsed_previews(valid_files, show_full=show_full)

        # Format output
        if show_full:
            output = "# 📄 Full Parsed Document Content\n\n"
        else:
            output = "# 📄 Parsed Document Previews (First 2000 chars)\n\n"

        for file_name, data in previews.items():
            output += f"## {file_name}\n\n"
            output += f"**File Type:** {data['file_type']} | "
            output += f"**Tokens:** {data['tokens']:,} | "
            output += f"**Chunks:** {data['chunks']} | "
            output += f"**Content Length:** {len(data['content']):,} chars"

            if data.get('is_truncated', False):
                output += " ⚠️ *Showing preview only - check 'Show Full Content' to see all*"

            output += "\n\n"

            if data['preview']:
                if show_full:
                    output += "### Full Content:\n\n"
                else:
                    output += "### Content Preview:\n\n"
                output += "```\n"
                output += data['preview']
                output += "\n```\n\n"
            else:
                output += "*No content extracted*\n\n"

            output += "---\n\n"

        return output

    except Exception as e:
        return f"⚠️ Error parsing documents: {str(e)}"


def load_saved_api_key() -> str:
    """Load saved API key from config."""
    return backend.config.get('api_key', '')


def refresh_dataset_files() -> gr.Dropdown:
    """Refresh list of available dataset files."""
    files = backend.list_output_files()
    if not files:
        return gr.Dropdown(choices=[], value=None)

    # Format choices to show just filename
    choices = [str(Path(f).name) for f in files]
    file_map = {Path(f).name: f for f in files}

    return gr.Dropdown(choices=choices, value=choices[0] if choices else None)


def load_and_display_dataset(
    dataset_file: str,
    api_key: str,
    model: str,
    max_tokens: int
) -> Tuple[str, str, pd.DataFrame]:
    """Load dataset and create interactive visualization.

    Args:
        dataset_file: Selected dataset filename
        api_key: OpenAI API key
        model: Model name
        max_tokens: Max tokens for parsing

    Returns:
        Tuple of (dataset_info_markdown, html_viewer, qa_dataframe)
    """
    if not dataset_file:
        return "⚠️ No dataset selected.", "<div style='padding: 40px; text-align: center; color: #666;'>No dataset loaded</div>", pd.DataFrame()

    if not api_key:
        return "⚠️ API key required to parse source document.", "<div style='padding: 40px; text-align: center; color: #666;'>API key required</div>", pd.DataFrame()

    try:
        # Find full path
        output_dir = Path('output')
        dataset_path = output_dir / dataset_file

        if not dataset_path.exists():
            return f"⚠️ File not found: {dataset_file}", "<div>File not found</div>", pd.DataFrame()

        # Load dataset
        triples, source_doc = backend.load_dataset(str(dataset_path))

        if not triples:
            return "⚠️ No data found in dataset.", "<div>No data found</div>", pd.DataFrame()

        # Initialize parser
        backend.initialize_components(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,
            min_triples=0,
            max_triples=10,
            output_dir='output'
        )

        # Get source document content
        try:
            doc_content = backend.get_source_document_content(source_doc)
        except (FileNotFoundError, ValueError) as e:
            return f"⚠️ Could not load source document: {str(e)}", "<div>Source document not found</div>", pd.DataFrame()

        # Create highlighted HTML
        html_output = backend.create_highlighted_html(doc_content, triples, hide_invalid=True)

        # Create dataset info
        valid_count = sum(1 for t in triples if t.get('citation_valid', True))
        invalid_count = len(triples) - valid_count

        info = f"""
### Dataset Information

- **Source Document:** {source_doc}
- **Total Q/A Pairs:** {len(triples)}
- **Valid Citations:** {valid_count}
- **Invalid Citations:** {invalid_count} (hidden from view)
- **Dataset File:** {dataset_file}
"""

        # Create Q/A dataframe
        qa_data = []
        for idx, triple in enumerate(triples):
            if triple.get('citation_valid', True):  # Only show valid ones
                qa_data.append({
                    '#': idx + 1,
                    'Question': triple['question'],
                    'Answer': triple['answer'],
                    'Citation Preview': triple['citation'][:100] + '...' if len(triple['citation']) > 100 else triple['citation']
                })

        df = pd.DataFrame(qa_data) if qa_data else pd.DataFrame()

        return info, html_output, df

    except Exception as e:
        error_msg = f"⚠️ Error loading dataset: {str(e)}"
        return error_msg, f"<div style='padding: 20px; color: red;'>{error_msg}</div>", pd.DataFrame()


# Build Gradio interface
def build_interface():
    """Build and return Gradio interface."""

    with gr.Blocks(
        title="RAG Dataset Generator",
        theme=gr.themes.Soft(),
        css="""
        .main-header {text-align: center; margin-bottom: 30px;}
        .section-header {margin-top: 20px; margin-bottom: 10px; font-weight: bold;}
        """
    ) as app:

        gr.Markdown(
            """
            # 🤖 RAG Dataset Generator
            ### Generate Question/Answer/Citation datasets from your documents
            Upload your documents and let AI generate evaluation questions for your RAG applications.
            """,
            elem_classes="main-header"
        )

        with gr.Tabs():
            # Main Processing Tab
            with gr.Tab("📄 Generate Questions"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 1️⃣ Upload Documents", elem_classes="section-header")

                        files_input = gr.File(
                            label="Drag & Drop Your Documents Here",
                            file_count="multiple",
                            file_types=[".pdf", ".docx", ".html", ".md", ".csv", ".xlsx"],
                            type="filepath"
                        )

                        gr.Markdown("**Supported formats:** PDF, Word, HTML, Markdown, CSV, Excel")

                        gr.Markdown("### 2️⃣ OpenAI Configuration", elem_classes="section-header")

                        api_key_input = gr.Textbox(
                            label="OpenAI API Key",
                            type="password",
                            placeholder="sk-...",
                            value=load_saved_api_key()
                        )

                        save_key_checkbox = gr.Checkbox(
                            label="Save API key for future sessions",
                            value=True
                        )

                        gr.Markdown("### 3️⃣ Settings", elem_classes="section-header")

                        with gr.Accordion("Advanced Settings (Optional)", open=False):
                            model_input = gr.Dropdown(
                                choices=["gpt-4.1", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                                value="gpt-4.1",
                                label="Model"
                            )

                            max_tokens_slider = gr.Slider(
                                minimum=1000,
                                maximum=20000,
                                value=10000,
                                step=1000,
                                label="Max Tokens per Document",
                                info="Higher = more content, higher cost"
                            )

                            temperature_slider = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.7,
                                step=0.1,
                                label="Temperature",
                                info="Higher = more creative questions"
                            )

                            min_questions_slider = gr.Slider(
                                minimum=0,
                                maximum=5,
                                value=0,
                                step=1,
                                label="Minimum Questions per Document"
                            )

                            max_questions_slider = gr.Slider(
                                minimum=1,
                                maximum=20,
                                value=10,
                                step=1,
                                label="Maximum Questions per Document"
                            )

                        gr.Markdown("### 4️⃣ Output Format", elem_classes="section-header")

                        output_format_checkboxes = gr.CheckboxGroup(
                            choices=["csv", "json", "jsonl"],
                            value=["csv"],
                            label="Select Output Format(s)"
                        )

                    with gr.Column(scale=1):
                        gr.Markdown("### 📊 Results", elem_classes="section-header")

                        with gr.Row():
                            preview_btn = gr.Button("👁️ Preview Parsed Text", variant="secondary", scale=1)
                            show_full_checkbox = gr.Checkbox(
                                label="Show Full Content",
                                value=False,
                                scale=1,
                                info="Warning: May be very long"
                            )

                        with gr.Accordion("📄 Parsed Document Content", open=False):
                            parsed_text_output = gr.Markdown(
                                value="Upload files and click 'Preview Parsed Text' above to see how documents are parsed."
                            )

                        process_btn = gr.Button("🚀 Generate Questions", variant="primary", size="lg")

                        summary_output = gr.Markdown()
                        results_table = gr.Dataframe(
                            headers=["Document", "Question", "Answer", "Citation", "Valid"],
                            label="Generated Questions Preview"
                        )

                        gr.Markdown("### 📥 Download Results")
                        gr.Markdown("*Click on any filename below to download*")
                        download_output = gr.File(
                            label="",
                            file_count="multiple",
                            type="filepath",
                            interactive=False,
                            show_label=False
                        )

            # Citation Viewer Tab
            with gr.Tab("🔍 Citation Viewer"):
                gr.Markdown("""
                ## Interactive Citation Explorer
                Load a previously generated dataset and explore the document with highlighted citations.
                Click on highlighted citations to see their associated questions and answers.
                """)

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 1️⃣ Load Dataset", elem_classes="section-header")

                        dataset_file_dropdown = gr.Dropdown(
                            label="Select Dataset File",
                            choices=[],
                            interactive=True,
                            info="Choose from previously generated datasets"
                        )

                        refresh_files_btn = gr.Button("🔄 Refresh File List", variant="secondary")

                        load_dataset_btn = gr.Button("📂 Load Dataset", variant="primary")

                        gr.Markdown("### ⚙️ Configuration", elem_classes="section-header")

                        viewer_api_key = gr.Textbox(
                            label="OpenAI API Key (for parsing)",
                            type="password",
                            placeholder="sk-...",
                            value=load_saved_api_key(),
                            info="Required to re-parse source document"
                        )

                        viewer_model = gr.Dropdown(
                            choices=["gpt-4.1", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                            value="gpt-4.1",
                            label="Model (for parsing)",
                            visible=False  # Hidden by default
                        )

                        viewer_max_tokens = gr.Slider(
                            minimum=1000,
                            maximum=20000,
                            value=10000,
                            step=1000,
                            label="Max Tokens",
                            visible=False  # Hidden by default
                        )

                        dataset_info_md = gr.Markdown("Load a dataset to see information here.")

                    with gr.Column(scale=2):
                        gr.Markdown("### 📄 Interactive Document View", elem_classes="section-header")

                        with gr.Row():
                            gr.Markdown("*Citations are color-coded. Click on highlighted text to view Q&A.*")

                        citation_html = gr.HTML(
                            value="<div style='padding: 40px; text-align: center; color: #666;'>Load a dataset to view interactive citations</div>"
                        )

                        gr.Markdown("### 📋 Questions & Answers", elem_classes="section-header")

                        qa_display = gr.Dataframe(
                            headers=["#", "Question", "Answer", "Citation Preview"],
                            label="All Q/A Pairs from Dataset",
                            wrap=True
                        )

                        gr.Markdown("""
                        **How to use:**
                        1. Select a dataset file from the dropdown
                        2. Click "Load Dataset"
                        3. View the document with highlighted citations above
                        4. Click any highlighted citation to see its Q&A in a popup
                        5. Browse all Q&A pairs in the table below
                        """)

            # Help Tab
            with gr.Tab("❓ Help"):
                gr.Markdown("""
                ## How to Use

                ### Step 1: Upload Documents
                - Drag and drop your documents into the upload area
                - Supported formats: PDF, Word, HTML, Markdown, CSV, Excel
                - You can upload multiple documents at once

                ### Step 2: Configure OpenAI
                - Enter your OpenAI API key (get one at platform.openai.com)
                - Check "Save API key" to remember it for next time
                - Your key is stored locally in `.env` file

                ### Step 3: Adjust Settings (Optional)
                - **Model**: Choose which OpenAI model to use
                - **Max Tokens**: Limit how much of each document to process (higher = more expensive)
                - **Temperature**: Control creativity (0 = focused, 1 = creative)
                - **Questions Range**: Set minimum and maximum questions per document

                ### Step 4: Generate
                - Click "Generate Questions" to start processing
                - Wait for processing to complete
                - Download results in your chosen format(s)

                ## Tips for Best Results

                ✅ **Do:**
                - Use clear, well-formatted documents
                - Start with a few documents to test
                - Review invalid citations (marked with ✗)

                ⚠️ **Avoid:**
                - Very large documents (>50 pages) - they'll be truncated
                - Scanned PDFs without text (enable OCR separately if needed)
                - Documents with mostly images or diagrams

                ## Output Files

                Generated files are saved in the `output/` directory with:
                - **CSV**: Spreadsheet format (open in Excel)
                - **JSON**: Structured data format
                - **JSONL**: One JSON object per line

                Each row contains:
                - Document name
                - Generated question
                - Answer from document
                - Exact citation (text snippet)
                - Validation status

                ## Citation Viewer

                The Citation Viewer tab lets you interactively explore generated datasets:

                ### How to Use Citation Viewer
                1. Go to the "Citation Viewer" tab
                2. Click "Refresh File List" to see all generated datasets
                3. Select a dataset file from the dropdown
                4. Enter your API key (needed to re-parse the source document)
                5. Click "Load Dataset"
                6. Explore:
                   - **Document view**: Citations are color-coded and clickable
                   - **Click any highlighted citation** to see its Q&A in a popup
                   - **Legend**: Shows which color = which question
                   - **Table below**: Browse all Q&A pairs

                ### Features
                - Color-coded citations for easy identification
                - Click citations to instantly view questions and answers
                - Only shows valid citations (invalid ones are hidden)
                - Legend shows question previews for each citation
                - Full Q&A table for reference

                ## Troubleshooting

                **"API key not found"**
                → Enter your OpenAI API key in the configuration section

                **"Unsupported format"**
                → Use PDF, Word, HTML, Markdown, CSV, or Excel files only

                **"Invalid citations detected"**
                → Normal - some citations may have minor formatting differences

                **"Source document not found" in Citation Viewer**
                → Make sure the original document is in the same location as when you generated the dataset
                """)

        # Wire up event handlers
        preview_btn.click(
            fn=preview_parsed_text,
            inputs=[files_input, api_key_input, model_input, max_tokens_slider, show_full_checkbox],
            outputs=[parsed_text_output]
        )

        process_btn.click(
            fn=process_files,
            inputs=[
                files_input,
                api_key_input,
                model_input,
                max_tokens_slider,
                temperature_slider,
                min_questions_slider,
                max_questions_slider,
                output_format_checkboxes,
                save_key_checkbox
            ],
            outputs=[summary_output, results_table, download_output]
        )

        # Citation Viewer event handlers
        refresh_files_btn.click(
            fn=refresh_dataset_files,
            inputs=[],
            outputs=[dataset_file_dropdown]
        )

        load_dataset_btn.click(
            fn=load_and_display_dataset,
            inputs=[dataset_file_dropdown, viewer_api_key, viewer_model, viewer_max_tokens],
            outputs=[dataset_info_md, citation_html, qa_display]
        )

        # Auto-populate dropdown on tab load
        app.load(
            fn=refresh_dataset_files,
            inputs=[],
            outputs=[dataset_file_dropdown]
        )

    return app


if __name__ == "__main__":
    app = build_interface()
    app.launch(
        share=True,  # Set to True to create public URL
        inbrowser=True,  # Automatically open in browser
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True
    )
