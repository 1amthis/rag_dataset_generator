# Citation Viewer Alternatives

## Current State

The citation viewer now works by generating fully escaped inline `alert(...)` handlers inside the highlighted HTML. This avoids injecting `<script>` tags and keeps the experience reliable across Gradio deployments. Users click a highlight and see the question/answer pair in a native browser dialog.

This implementation solves the earlier JavaScript escaping errors but still leaves room for UX enhancements. The alternatives below describe possible follow-up improvements if you want a richer experience than alerts.

## Improving the Experience

## Alternative Approaches

### Option 1: Keep Alerts, Polish Matching (Current Implementation)
**Status:** Already implemented — highlights trigger native alerts

Pros:
- Minimal surface area; works within existing Gradio app
- No custom JavaScript injection required
- Reliable across local and hosted Gradio sessions

Cons:
- Alerts interrupt the flow and feel basic
- Still limited by `gr.HTML` (no custom modal styling)
- Matching is best-effort; heavy paraphrasing still fails

Potential refinements:
- Expose a toggle to include invalid/unmatched citations for debugging.
- Normalize punctuation or smart quotes before matching to capture more cases.


### Option 2: Use Gradio Events (Recommended for Gradio)
**Replace onclick with Gradio's click events**

Instead of:
- HTML with onclick handlers
- JavaScript alerts

Do:
- Clickable dataframe/table showing citations
- Gradio click event handlers
- Display Q&A in separate Gradio components

Pros:
- Pure Python - no JavaScript
- Works reliably with Gradio
- Better UX than alert() popups
- More maintainable

Cons:
- Can't highlight text inline
- Less visually integrated
- Requires redesign of the viewer

Implementation sketch:
```python
with gr.Row():
    with gr.Column():
        # Dataframe with citations
        citations_df = gr.Dataframe(
            headers=["#", "Citation Preview"],
            interactive=True
        )
    with gr.Column():
        # Q&A display
        question_display = gr.Textbox(label="Question")
        answer_display = gr.Textbox(label="Answer")
        citation_display = gr.Textbox(label="Full Citation")

# When row clicked, show details
citations_df.select(
    fn=show_citation_details,
    inputs=[citations_df],
    outputs=[question_display, answer_display, citation_display]
)
```

### Option 3: Separate Static HTML Export
**Keep GUI simple, export rich HTML separately**

In GUI:
- Show basic results table
- Export button creates standalone HTML

Standalone HTML:
- Fully interactive with proper JavaScript
- No Gradio limitations
- User opens in browser

Pros:
- Best of both worlds
- Rich interactivity in HTML
- Simple Gradio interface
- No JavaScript conflicts

Cons:
- Extra file to manage
- Not inline in Gradio

Implementation:
```python
def export_interactive_html(dataset_file):
    """Create standalone HTML file with citations."""
    # Generate full HTML with proper JavaScript
    # Save to file
    # Return file path for download
    return html_file_path

export_btn = gr.Button("Export Interactive Viewer")
export_btn.click(
    fn=export_interactive_html,
    inputs=[dataset_dropdown],
    outputs=[gr.File()]
)
```

### Option 4: Different Framework
**Replace Gradio with Flask/Streamlit/Dash**

If citation viewer is core to the app:
- **Streamlit**: Good balance, some HTML support
- **Flask**: Full control, more code needed
- **Dash**: Designed for interactive dashboards

Pros:
- Full control over JavaScript
- Better for complex interactions
- Professional deployment options

Cons:
- Major rewrite
- More complexity
- Needs web server knowledge

## Recommendation

With Option 1 now live, the viewer is functional and reliable. If you want a more polished experience, focus on:

1. **Option 3 (Standalone HTML export)** – create a shareable, fully interactive report without Gradio constraints.
2. **Option 2 (Gradio-native components)** – build a richer in-app viewer using dataframes/panels if you prefer to keep everything inside the GUI.

Either path can be pursued incrementally while retaining the current alert-based viewer as a safe default.
