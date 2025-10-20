# GUI Quick Start Guide

## 🚀 For Non-Technical Users

This guide will help you use the RAG Dataset Generator GUI to create evaluation questions from your documents.

## What Does This Tool Do?

The RAG Dataset Generator reads your documents (PDFs, Word files, etc.) and automatically generates:
- **Questions** that users might ask about your content
- **Answers** based on what's in your documents
- **Citations** (exact quotes) that support each answer

This helps you evaluate and test your AI applications.

## First Time Setup (5 minutes)

### Step 1: Get Your OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign in or create an account
3. Go to "API Keys" section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-...`)
6. **Save it somewhere safe** - you'll need it!

### Step 2: Start the Application

**On Windows:**
1. Double-click `run_gui.bat`
2. A browser window will open automatically

**On Mac/Linux:**
1. Double-click `run_gui.sh` (or run `./run_gui.sh` in terminal)
2. A browser window will open automatically

**First time only:** The application will install required components (takes 2-3 minutes)

## Using the GUI

### 📄 Main Screen Overview

The interface has 4 simple sections:

#### 1️⃣ Upload Documents
- **Drag and drop** your files into the upload box
- Or click to browse and select files
- You can upload multiple files at once

**Supported formats:**
- PDF (`.pdf`)
- Word (`.docx`)
- HTML (`.html`)
- Markdown (`.md`)
- CSV (`.csv`)
- Excel (`.xlsx`)

#### 2️⃣ OpenAI Configuration
- **Paste your API key** in the text box
- Check **"Save API key"** so you don't have to enter it again
- Your key is saved securely on your computer

#### 3️⃣ Settings (Optional)
Click "Advanced Settings" to customize:

- **Model**: Which AI to use (default: gpt-4.1)
- **Max Tokens**: How much of each document to read (10,000 = recommended)
- **Temperature**: Question creativity (0.7 = balanced)
- **Min/Max Questions**: How many questions to generate per document

**💡 Tip:** Leave settings as default for best results!

#### 4️⃣ Output Format
Choose how you want your results:
- **CSV** ✓ - Open in Excel (recommended)
- **JSON** - For developers
- **JSONL** - For machine learning

## Step-by-Step: Generate Questions

### Step 1: Upload Your Documents
1. Drag your PDF or Word files into the upload area
2. You'll see the file names appear

### Step 2: Enter API Key
1. Paste your OpenAI API key
2. Check "Save API key for future sessions"

### Step 3: Check the Cost (Optional)
1. Click **"💰 Estimate Cost"**
2. See how much it will cost to process your documents
3. Typical cost: $0.10 - $0.50 per document

### Step 4: Generate Questions
1. Click **"🚀 Generate Questions"**
2. Wait while processing (may take 30-60 seconds per document)
3. Progress bar shows current status

### Step 5: Review & Download
1. See the **Summary** (how many questions were generated)
2. Preview questions in the **Results Table**
3. Click **Download links** to get your files
4. Files are saved in the `output/` folder

## Understanding the Results

### Results Table Shows:
- **Document**: Which file the question came from
- **Question**: Generated question
- **Answer**: Answer from the document
- **Citation**: Exact quote supporting the answer
- **Valid**: ✓ = exact match, ✗ = slight difference

### What is "Invalid Citation"?
Sometimes the AI paraphrases slightly instead of using exact quotes. This is marked with ✗ but the citation is still useful.

## Downloaded Files Contain:

Each row has:
- `document_id` - Document name
- `question` - Generated question
- `answer` - Answer from document
- `citation` - Exact text snippet
- `citation_valid` - TRUE/FALSE
- `timestamp` - When it was created

**Open in Excel:** Just double-click the CSV file!

## Common Questions

### ❓ How many questions will I get?
Between 0-10 per document, depending on content richness. Short documents = fewer questions.

### ❓ What if my PDF is scanned (no text)?
The tool works best with PDFs that have selectable text. Scanned documents (images) won't work by default.

### ❓ How much does it cost?
- Cost depends on document length
- Typical: $0.10 - $0.50 per document
- Use "Estimate Cost" button before processing
- You only pay OpenAI (not us)

### ❓ Is my data secure?
- Everything runs on YOUR computer
- Documents are processed through OpenAI's API
- API key is saved locally in `.env` file
- No data is stored on our servers

### ❓ Can I process many documents?
Yes! Upload as many as you want. Processing happens one at a time. Large batches may take several minutes.

### ❓ Where are my results saved?
All output files are saved in the `output/` folder in your project directory.

## Troubleshooting

### 🔴 "API key not found"
**Solution:** Enter your OpenAI API key in the configuration section

### 🔴 "Unsupported file format"
**Solution:** Use only PDF, Word, HTML, Markdown, CSV, or Excel files

### 🔴 "Cost too high"
**Solution:**
- Reduce "Max Tokens" setting (try 5000 instead of 10000)
- Process fewer documents at once

### 🔴 Application won't start
**Solution:**
1. Make sure you ran `setup.sh` or `setup.bat` first
2. Check that Python 3.8+ is installed
3. Try running from command line to see error messages

### 🔴 Questions don't make sense
**Solution:**
- Check your document has clear, readable text
- Try adjusting Temperature (lower = more focused)
- Some documents may not be suitable for Q/A generation

## Tips for Best Results

✅ **DO:**
- Use clear, well-formatted documents
- Start with 1-2 documents to test
- Check cost estimate before large batches
- Review questions for accuracy

❌ **AVOID:**
- Very large documents (>50 pages) - they get truncated
- Scanned PDFs without text layer
- Documents that are mostly images/charts
- Documents with complex formatting

## Getting Help

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Check the main [README.md](README.md) for technical details
3. Review ChunkNorris docs: https://wikit-ai.github.io/chunknorris/
4. Open an issue on GitHub (if using GitHub version)

## Next Steps

Once you're comfortable with the GUI:
- Process larger document batches
- Experiment with different settings
- Use generated questions to test your RAG applications
- Export to different formats for your workflow

---

**Need the command-line version?** See [QUICKSTART.md](QUICKSTART.md) for CLI instructions.
