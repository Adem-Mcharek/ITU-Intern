# Git Push Guide

## Your repository is now clean and ready for GitHub!

### What Was Done
1. ✅ Created comprehensive `.gitignore` file
2. ✅ Moved test files to `_archive/` folder (14 files)
3. ✅ Organized documentation into `docs/` folder (9 files)
4. ✅ Cleaned up app directory (removed backups and legacy files)

### Before Pushing to GitHub

#### 1. Initialize Git (if not already done)
```bash
git init
```

#### 2. Add Remote Repository
Replace `YOUR_USERNAME` and `YOUR_REPO` with your GitHub details:
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

#### 3. Stage Your Files
```bash
# Add all files (gitignore will exclude unwanted files)
git add .

# Or stage specific files if you want more control
git add app/
git add docs/
git add migrations/
git add .gitignore
git add README.md
git add requirements.txt
git add run.py
git add setup.sh setup.bat
git add start.sh start.bat
```

#### 4. Check What Will Be Committed
```bash
git status
```

**Expected output**: Should NOT see:
- `__pycache__/` files
- `.venv/` or `venv/`
- `uploads/` folder
- `app.db` database file
- `.env` file
- `uv.lock`
- Files in `_archive/` (if you added _archive to .gitignore)

#### 5. Commit Your Changes
```bash
git commit -m "Initial commit: Clean ITU transcript processing application"
```

#### 6. Push to GitHub
```bash
# For first push
git branch -M main
git push -u origin main

# For subsequent pushes
git push
```

### Important Notes

#### Files That Won't Be Pushed (Good!)
- Virtual environment (`.venv/`)
- Database (`app.db`, `instance/`)
- Environment variables (`.env`)
- User uploads (`uploads/`)
- Python cache (`__pycache__/`, `*.pyc`)
- IDE files (`.cursor/`, `.vscode/`)
- Lock files (`uv.lock`)

#### Files That WILL Be Pushed (Good!)
- Application code (`app/`)
- Database migrations (`migrations/`)
- Documentation (`docs/`, `README.md`)
- Configuration (`requirements.txt`, `pyproject.toml`)
- Setup scripts (`setup.sh`, `start.sh`, etc.)
- `.gitignore` itself

#### Archive Folder
The `_archive/` folder contains test and backup files. You have two options:
1. **Keep it in .gitignore** (recommended) - These files won't be pushed
2. **Push it** - Remove `_archive/` from `.gitignore` if you want these files on GitHub

### Creating .env File
Before deployment, create a `.env` file (this won't be pushed to GitHub):
```bash
cp env.example .env
# Then edit .env with your actual API keys
```

### After Pushing

#### Clone on Another Machine
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
cp env.example .env
# Edit .env with your API keys
chmod +x setup.sh start.sh
./setup.sh
./start.sh
```

### Useful Git Commands

#### Check what's gitignored
```bash
git status --ignored
```

#### See what would be committed
```bash
git diff --cached
```

#### Remove accidentally tracked files
```bash
# If you accidentally committed .env or uploads/
git rm --cached .env
git rm --cached -r uploads/
git commit -m "Remove sensitive files"
git push
```

#### Create a new branch for development
```bash
git checkout -b development
git push -u origin development
```

### GitHub Repository Setup Tips

1. **Create Repository on GitHub** (if not done):
   - Go to https://github.com/new
   - Name it (e.g., "itu-transcribe")
   - Don't initialize with README (you already have one)
   - Don't add .gitignore (you already have one)

2. **Set Repository to Private** if it contains sensitive information

3. **Add a .env.example** to show required environment variables:
   ```bash
   cp .env .env.example
   # Remove actual values, keep only keys
   git add .env.example
   git commit -m "Add environment template"
   ```

4. **Add Branch Protection** (optional):
   - Settings → Branches → Add rule
   - Protect `main` branch
   - Require pull request reviews

### Next Steps
1. Review the cleanup summary: `CLEANUP_SUMMARY.md`
2. Test your application locally to ensure nothing broke
3. Follow the git commands above to push to GitHub
4. Consider adding GitHub Actions for CI/CD (optional)

---
**Ready to push!** 🚀

