# Sharing the GUI App

This guide explains how to share the RAG Dataset Generator GUI with friends or colleagues.

## Option 1: Gradio Public Link (Easiest) ⭐

**Best for:** Quick sharing, temporary access (up to 72 hours)

### How it works:
- Gradio creates a temporary public URL through their servers
- Your friend can access it from anywhere in the world
- No installation needed for your friend
- URL expires after 72 hours
- **Your machine must stay running**

### Steps:

1. **The share option is already enabled in the code** (as of the latest update)

2. **Run the GUI:**
   ```bash
   ./run_gui.sh
   ```

3. **Look for the public URL in the terminal output:**
   ```
   Running on local URL:  http://127.0.0.1:7860
   Running on public URL: https://abc123xyz.gradio.live

   This share link expires in 72 hours...
   ```

4. **Send the public URL to your friend:**
   - Share: `https://abc123xyz.gradio.live`
   - They can open it in any browser
   - They'll need their own OpenAI API key

### ⚠️ Important Notes:
- Your computer must stay on and connected
- The app runs on your machine (uses your resources)
- Each friend needs their own OpenAI API key
- URL changes each time you restart

---

## Option 2: Local Network Access

**Best for:** Sharing with people on the same WiFi/network

### How it works:
- Your friend connects to your local network (same WiFi)
- They access the app through your local IP address
- No internet connection needed
- Completely private

### Steps:

1. **Find your local IP address:**

   **On Mac/Linux:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

   **On Windows:**
   ```bash
   ipconfig
   ```
   Look for "IPv4 Address" (e.g., `192.168.1.100`)

2. **Modify the GUI to allow network access:**

   Edit `src/gui_gradio.py` line 518:
   ```python
   # Change from:
   server_name="127.0.0.1",

   # To:
   server_name="0.0.0.0",  # Allows network access
   ```

3. **Run the GUI:**
   ```bash
   ./run_gui.sh
   ```

4. **Share the URL with your friend:**
   ```
   http://YOUR_IP_ADDRESS:7860
   ```
   Example: `http://192.168.1.100:7860`

### ⚠️ Security Notes:
- Only people on your network can access
- Make sure you trust your network
- Firewall may need to allow port 7860

---

## Option 3: Send Them the Code (Best for Long-term)

**Best for:** Friends who want their own installation

### How it works:
- Your friend installs the tool on their own computer
- They have full control and privacy
- They use their own resources and API key

### Steps:

1. **Send them the repository:**
   - If you have it on GitHub: Share the repo URL
   - Otherwise: Zip the project folder and send it

2. **They follow the setup instructions:**

   ```bash
   # Clone or unzip
   cd dataset_generator

   # Run setup
   ./setup.sh

   # Add their API key
   cp .env.example .env
   # Edit .env and add OPENAI_API_KEY

   # Run the GUI
   ./run_gui.sh
   ```

3. **Done!** They have their own independent installation

### Benefits:
- ✅ Complete privacy
- ✅ No dependency on your machine
- ✅ They can customize settings
- ✅ No time limits

---

## Option 4: Deploy to Cloud (Advanced)

**Best for:** Production use, multiple users, always available

### Popular platforms:
- **Hugging Face Spaces** (Free tier available)
- **Render** (Free tier with limitations)
- **Railway** (Paid)
- **Your own server** (AWS, DigitalOcean, etc.)

### Deployment example (Hugging Face Spaces):

1. Create a `app.py` in the root directory:
   ```python
   # app.py
   import sys
   sys.path.insert(0, 'src')
   from gui_gradio import build_interface

   app = build_interface()
   app.launch()
   ```

2. Create `requirements.txt` (already exists)

3. Push to Hugging Face Spaces (see their docs)

### Benefits:
- ✅ Always available (24/7)
- ✅ No need to keep your computer on
- ✅ Professional URL
- ✅ Can handle multiple users

### Drawbacks:
- More complex setup
- May require payment for better performance
- Need to manage secrets (API keys)

---

## Comparison Table

| Option | Ease of Setup | Cost | Uptime Required | Privacy | Best For |
|--------|---------------|------|-----------------|---------|----------|
| **Gradio Public Link** | ⭐⭐⭐⭐⭐ | Free | Your machine | Medium | Quick demos |
| **Local Network** | ⭐⭐⭐⭐ | Free | Your machine | High | Same location |
| **Send Code** | ⭐⭐⭐ | Free | Their machine | Highest | Long-term use |
| **Cloud Deploy** | ⭐⭐ | $0-$$ | 24/7 | Medium | Production |

---

## Security Considerations

### API Keys:
- **Never hardcode API keys** in the code
- Each user should use their own key
- Keys are saved locally in `.env` (not shared)

### Public Sharing:
- Anyone with the link can access (if using Gradio share)
- Consider adding authentication for production
- Monitor usage to prevent abuse

### Data Privacy:
- Uploaded documents are processed on the host machine
- Generated datasets are saved locally
- OpenAI processes the content (see their privacy policy)

---

## Recommended Approach

**For a friend who wants to try it:**
→ Use **Option 1** (Gradio Public Link) - just run `./run_gui.sh` and share the public URL

**For a colleague at work (same network):**
→ Use **Option 2** (Local Network) - more private, better control

**For someone who wants their own copy:**
→ Use **Option 3** (Send Code) - best long-term solution

**For a team or production:**
→ Use **Option 4** (Cloud Deploy) - most robust, always available

---

## Current Configuration

✅ **The app is currently configured for public sharing** (`share=True`)

When you run `./run_gui.sh`, you'll see:
```
Running on public URL: https://xxxxx.gradio.live
```

Just share that URL with your friend!

**To disable public sharing**, edit `src/gui_gradio.py` line 516:
```python
share=False,  # Back to local-only
```

---

## Troubleshooting

**Q: The public URL isn't working**
- Make sure your internet is stable
- Check if Gradio services are up
- Try restarting the app

**Q: My friend gets "Connection refused"**
- For local network: Check firewall settings
- For public link: Make sure your app is still running

**Q: How do I stop sharing?**
- Press `Ctrl+C` in the terminal
- The public URL will immediately stop working

**Q: Can multiple people use it at once?**
- Yes! Gradio handles concurrent users
- Each user processes their own documents
- They each need their own API key

---

## Need Help?

- Check the main README.md for general setup
- See CLAUDE.md for development details
- Open an issue on GitHub for bugs
