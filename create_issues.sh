#!/bin/bash

while IFS= read -r line
do
    gh issue create --title "$line"
done < issue.txt