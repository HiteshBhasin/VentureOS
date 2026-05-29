#!/bin/bash
while true; do
    echo "Enter commit message (or 'exit' to quit):"
    read commit_message
    git add .
    git commit -m "$commit_message"

    if git push origin sub_dev; then
        echo "Changes pushed successfully."
    else
        echo "Push failed. Try again? (y/n)"
        read retry
        [[$retry !="y"]] && break
    fi
done