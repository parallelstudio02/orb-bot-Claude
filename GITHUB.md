# How to Put This on GitHub Pages

GitHub Pages turns your code into a live website you can open on any browser or phone.

---

## Step 1 — Create a GitHub account

Go to https://github.com and sign up for a free account if you do not have one.

---

## Step 2 — Create a new repository

1. Once logged in, click the green "New" button on the left, or go to https://github.com/new
2. Repository name: `orb-bot` (or any name you like)
3. Set it to **Public** (required for free GitHub Pages)
4. Tick "Add a README file"
5. Click "Create repository"

---

## Step 3 — Upload your files

1. Inside your new repository, click "Add file" → "Upload files"
2. Upload these files from your computer:
   - `index.html`
   - `fetch_signals.py`
   - `README.md`
3. Scroll down, click "Commit changes"

---

## Step 4 — Turn on GitHub Pages

1. In your repository, click "Settings" (top menu)
2. On the left sidebar, click "Pages"
3. Under "Branch", select `main` from the dropdown
4. Leave the folder as `/ (root)`
5. Click "Save"
6. Wait about 60 seconds, then refresh the page
7. You will see a green banner: "Your site is live at https://YOURUSERNAME.github.io/orb-bot"

That URL is your bot. Bookmark it. Open it every night before 9:30 PM SGT.

---

## Step 5 — Update signals each night

Until you automate it, the process each night is:
1. Run `python3 fetch_signals.py` on your computer
2. Upload the new `signals.json` to GitHub (drag and drop into the repo)
3. Open your GitHub Pages URL — it will load the fresh signals

## Optional — Automate with GitHub Actions (advanced)

Once you are comfortable, I can build you a GitHub Actions workflow that runs the Python script automatically at 9:00 PM SGT every day without you touching anything.
