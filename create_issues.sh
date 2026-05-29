#!/bin/bash

while IFS= read -r line
do
    gh issue create\
     --title "$line" \
     --body "Auto-generate issue"

done < issue.txt