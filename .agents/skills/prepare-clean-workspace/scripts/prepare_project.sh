#!/bin/bash

# Function to prepare a directory
prepare_repo() {
    local dir=$1
    echo "─────────────────────────────────────────────"
    echo "Preparing repository: $dir"
    echo "─────────────────────────────────────────────"
    
    if [ ! -d "$dir" ]; then
        echo "❌ Error: Directory $dir does not exist."
        return 1
    fi
    
    cd "$dir" || return 1
    
    # Check current branch
    local current_branch
    current_branch=$(git branch --show-current 2>/dev/null)
    echo "Current branch: $current_branch"
    
    # Check for uncommitted changes
    local uncommitted
    uncommitted=$(git status --porcelain 2>/dev/null)
    
    local stashed=0
    if [ -n "$uncommitted" ]; then
        echo "Detected local uncommitted changes. Safely stashing..."
        if git stash -u 2>/dev/null; then
            stashed=1
        else
            echo "❌ Error: Failed to stash changes."
            return 1
        fi
    fi
    
    if [ "$current_branch" != "develop" ]; then
        echo "Switching to branch 'develop'..."
        if ! git checkout develop 2>/dev/null; then
            echo "❌ Error: Failed to checkout develop."
            if [ $stashed -eq 1 ]; then
                echo "Restoring stashed changes..."
                git stash pop 2>/dev/null
            fi
            return 1
        fi
    fi
    
    echo "Pulling latest changes from remote origin/develop..."
    if ! git pull < /dev/null; then
        echo "❌ Error: git pull failed. Please check your VPN connection!"
        if [ $stashed -eq 1 ]; then
            echo "Restoring stashed changes..."
            git stash pop 2>/dev/null
        fi
        return 1
    fi
    
    if [ $stashed -eq 1 ]; then
        echo "Restoring stashed changes..."
        if ! git stash pop 2>/dev/null; then
            echo "⚠️  Warning: Conflict occurred while restoring stashed changes. Please review!"
        fi
    fi
    
    echo "✅ SUCCESS: $dir is prepared and up to date!"
}

# Run for both repositories
prepare_repo "/workspace/sp-met-global"
prepare_repo "/workspace/sp-prod"
