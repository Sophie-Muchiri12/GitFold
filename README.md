# Gitfold

> One command to stage, commit, merge, push, and open a PR — powered by AI.

Gitfold automates your entire Git workflow with a single terminal command. It stages your files, uses AI to write a meaningful commit message based on your actual code changes, syncs with your development branch, pushes to GitHub, and creates a pull request — all in one go.

---

## Features

- **One command** — just type `done` and Gitfold handles the rest
- **AI-powered commit messages** — understands your diff and writes proper conventional commits
- **AI-powered PR descriptions** — generates a clear summary and bullet-point changelog
- **Intelligent branch detection** — auto-detects your main, dev, and current branches
- **Real-time terminal output** — watch every step happen live
- **Manual mode** — use `done --manual` to confirm each step yourself
- **GitHub PR creation** — opens the PR in your browser automatically
- **Cross-platform** — works on macOS, Linux, and Windows

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/gitfold.git
cd gitfold
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Gitfold as a global command

```bash
pip install -e .
```

After this, you can type `done` from any Git repository on your machine.

---

## Setup

Create a `.env` file in your project root with your API keys:

```dotenv
OPENAI_API_KEY=your_openai_key_here
GITHUB_TOKEN=your_github_token_here
```

**Getting your OpenAI API key:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

**Getting your GitHub token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate a new token with `repo` and `read:user` scopes
3. Copy and paste it into your `.env` file

> Never commit your `.env` file. Add it to `.gitignore`.

---

## Usage

### Automatic mode (recommended)

```bash
done
```

Gitfold will:
1. Detect your repo and branches
2. Stage all changed files
3. Generate an AI commit message — you can accept, edit, or regenerate it
4. Commit your changes
5. Pull and merge from your dev/main branch
6. Push to remote
7. Generate an AI PR description and create the PR on GitHub
8. Open the PR in your browser
9. Print a summary of everything that happened

---

### Manual mode

```bash
done --manual
```

Gitfold will ask for your confirmation before each step.

---

### Additional flags

```bash
done --no-push       # Commit only, skip push and PR
done --no-pr         # Push but skip PR creation
done --branch main   # Override the target base branch
```

---

## First run

On your first run, Gitfold will ask you a few setup questions:

```
⚙️  Welcome to Gitfold! Let's set up your config.

What is your default branch? (detected: 'main', press Enter to confirm):
Development branch detected as 'dev'. Use this? [y/n]:
Auto-push to remote after commit? [y/n] (default: y):
Auto-open PR in browser after push? [y/n] (default: y):
Your GitHub username (optional, press Enter to skip):
```

Your answers are saved to `.gitfold.json` in your project root. You can edit this file anytime.

---

## Project structure

```
gitfold/
├── src/
│   ├── main.py            # Entry point and command flow
│   ├── git_handler.py     # All Git operations
│   ├── ai_integration.py  # LLM commit and PR generation
│   ├── config_manager.py  # Config loading and setup
│   ├── github_api.py      # GitHub API and PR creation
│   └── logger.py          # Terminal output and display
├── tests/
│   ├── test_git_handler.py
│   ├── test_ai_integration.py
│   └── test_github_api.py
├── .env                   # Your API keys (never commit this)
├── .gitignore
├── requirements.txt
├── setup.py
└── README.md
```
# gitfold-proxy

The AI backend for [gitfold](https://github.com/Sophie-Muchiri12/GitFold).

This is a tiny FastAPI server that holds your Featherless API key server-side.
Users who install `gitfold` via `pip install gitfold` never need to configure
an API key — they just call this proxy.

---

## Architecture

```
User's terminal
  └── gitfold CLI (PyPI)
        └── POST https://your-proxy.onrender.com/generate/commit
              └── Featherless API  (key lives only on your server)
```

---

## Deploy in 5 minutes (Render — free tier)

1. Push this folder to a new GitHub repo (e.g. `gitfold-proxy`)
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Render auto-detects the `render.yaml` — click **Deploy**
5. In the Render dashboard → **Environment** tab, add:
   ```
   FEATHERLESS_API_KEY = your_actual_key_here
   ```
6. Copy your service URL, e.g. `https://gitfold-proxy.onrender.com`

> **Note:** Render's free tier spins down after 15 min of inactivity.
> The first request after sleep takes ~5 seconds (cold start). Upgrade
> to a paid instance ($7/mo) to keep it always-on.

---

## Deploy on Railway (always-on free tier)

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
3. Select your repo
4. Add env var: `FEATHERLESS_API_KEY = your_key`
5. Railway uses the `railway.toml` config automatically

---

## After deploying

Update the default proxy URL in the gitfold package's `ai_integration.py`:

```python
PROXY_BASE_URL = os.getenv(
    "GITFOLD_PROXY_URL",
    "https://YOUR-SERVICE.onrender.com",  # ← your real URL here
)
```

Then bump the version in `setup.py` and republish to PyPI:

```bash
python -m build
twine upload dist/*
```

---

## Endpoints

| Method | Path                    | Description                        |
|--------|-------------------------|------------------------------------|
| GET    | `/health`               | Liveness check                     |
| POST   | `/generate/commit`      | Generate a commit message          |
| POST   | `/generate/commit/regen`| Regenerate with higher temperature |
| POST   | `/generate/pr`          | Generate PR title + body           |

### POST /generate/commit

```json
Request:  { "diff": "<git diff string>" }
Response: { "message": "feat(auth): add JWT refresh token support", "provider": "Featherless" }
```

### POST /generate/pr

```json
Request:  { "diff": "...", "commit_message": "...", "branch_name": "feature/auth" }
Response: { "title": "Add JWT refresh tokens", "body": "## Summary\n...", "provider": "Featherless" }
```

---

## Rate limiting

30 requests/minute per IP address. This is generous for a CLI tool.
Adjust `@limiter.limit("30/minute")` in `server.py` if needed.

---

## Bring-your-own-key

Power users who want higher limits can add their own key to their project's `.env`:

```
FEATHERLESS_API_KEY=their_own_key
```

The gitfold package detects this and calls Featherless directly, bypassing
the proxy entirely.
---

## Contributing

Gitfold is open source and contributions are welcome! Feel free to open issues, suggest features, or submit pull requests.

---

## License

MIT License. See [LICENSE](LICENSE) for details.