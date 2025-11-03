#!/bin/bash
# Quick script to push to GitHub
# Edit GITHUB_USER below with your GitHub username

GITHUB_USER="YOUR_USERNAME"  # ← CHANGE THIS!
REPO_NAME="icv-toolkit"

echo "Pushing IC Validator Toolkit to GitHub..."
echo ""

# Add remote
git remote add origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git" 2>/dev/null || {
    echo "Note: Remote already exists"
}

# Rename branch to main
git branch -M main

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Your project is now on GitHub!"
    echo ""
    echo "Visit: https://github.com/${GITHUB_USER}/${REPO_NAME}"
    echo ""
else
    echo ""
    echo "❌ Push failed. Check the error message above."
    echo "See GITHUB_SETUP_INSTRUCTIONS.md for troubleshooting."
    echo ""
fi
