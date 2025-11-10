# Quick Git Commands for GitHub Push

## One-Line Setup (Copy & Paste)

### First Time Setup
```bash
# Initialize and push (replace YOUR_USERNAME and YOUR_REPO)
git init && git add . && git commit -m "Initial commit: ITU Transcript Processing Application" && git branch -M main && git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git && git push -u origin main
```

## Step-by-Step (Safer)

### 1. Initialize
```bash
git init
```

### 2. Add Remote (replace with your repo URL)
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### 3. Stage, Commit, Push
```bash
git add .
git commit -m "Initial commit: ITU Transcript Processing Application"
git branch -M main
git push -u origin main
```

## Quick Status Check
```bash
# See what will be committed
git status

# See what's being ignored
git status --ignored
```

## If You Need to Update
```bash
git add .
git commit -m "Your commit message here"
git push
```

## Common Issues

### Already initialized?
```bash
# Check if git is initialized
git status

# If it shows a repo, just add your remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Wrong remote?
```bash
# Remove old remote
git remote remove origin

# Add correct remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### Force push (use carefully!)
```bash
git push -f origin main
```

---
**Note**: Make sure you have a GitHub account and have created a repository before running these commands!

