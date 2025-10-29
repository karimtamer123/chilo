# Deployment Guide

This guide will help you deploy your Chiller Picker Pro application to Streamlit Cloud via GitHub.

## Prerequisites

1. **Install Git** (if not already installed):
   - Download from: https://git-scm.com/download/win
   - Follow the installation wizard
   - Restart your terminal after installation

2. **Create a GitHub account** (if you don't have one):
   - Go to: https://github.com/signup
   - Complete the registration

## Step 1: Initialize Git Repository

Open PowerShell or Command Prompt in your project directory and run:

```bash
# Initialize git repository
git init

# Add all files (except those in .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: Chiller Picker Pro application"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Fill in the repository details:
   - **Repository name**: `chiller-picker-pro` (or your preferred name)
   - **Description**: Professional chiller selection and comparison tool
   - **Visibility**: Choose Public or Private
   - **Do NOT** initialize with README, .gitignore, or license (we already have these)
3. Click "Create repository"

## Step 3: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/chiller-picker-pro.git

# Rename main branch if needed
git branch -M main

# Push your code to GitHub
git push -u origin main
```

If you're prompted for credentials:
- **Username**: Your GitHub username
- **Password**: Use a Personal Access Token (not your password)
  - Create one at: https://github.com/settings/tokens
  - Give it `repo` permissions

## Step 4: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click "New app"
4. Configure your app:
   - **Repository**: Select `YOUR_USERNAME/chiller-picker-pro`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Choose your custom subdomain (optional)
5. Click "Deploy"

Streamlit Cloud will automatically:
- Install dependencies from `packages.txt`
- Deploy your app
- Provide you with a public URL (e.g., `https://your-app.streamlit.app`)

## Step 5: Database Considerations

⚠️ **Important**: The application uses a local SQLite database (`chillers.db`). 

For production deployment, you have a few options:

1. **Start with empty database**: Users can import data through the web interface
2. **Include sample data**: Add `sample_data.csv` but keep the database empty in the repo
3. **Use external database** (future enhancement): Consider migrating to PostgreSQL or similar for persistent data storage

## Updating Your Deployed App

After making changes locally:

```bash
# Stage your changes
git add .

# Commit changes
git commit -m "Description of your changes"

# Push to GitHub
git push origin main
```

Streamlit Cloud will automatically detect the changes and redeploy your app (usually takes 1-2 minutes).

## Troubleshooting

### Git not found
- Make sure Git is installed and added to your PATH
- Restart your terminal after installation

### Authentication issues
- Use Personal Access Tokens instead of passwords
- Consider using GitHub CLI (`gh auth login`)

### Deployment fails
- Check that `packages.txt` includes all required dependencies
- Verify that `app.py` is in the root directory
- Check Streamlit Cloud logs for error messages

## Alternative: Manual Git Commands

If you prefer to use Git from a GUI:
- **GitHub Desktop**: https://desktop.github.com/
- **GitKraken**: https://www.gitkraken.com/
- **SourceTree**: https://www.sourcetreeapp.com/

## Need Help?

- Streamlit Cloud docs: https://docs.streamlit.io/streamlit-community-cloud
- Git documentation: https://git-scm.com/doc
- GitHub guides: https://guides.github.com/

