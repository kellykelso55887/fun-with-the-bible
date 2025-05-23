#!/usr/bin/env python3

# this file counts the words in the chapters of the bible 
# in s3 buckets and pushes the summary to Github
# last reviewed on 23 May 2025

# run ./fun-with-the-bible.py in myenv


import os
import boto3
import pandas as pd
from github import Github, InputGitTreeElement, GithubException
from dotenv import load_dotenv 


# set variables
load_dotenv()                                   # loads variables from .env
s3            = boto3.client('s3')              # initialise s3
bucket        = os.getenv("BUCKET")
github_repo   = os.getenv("GITHUB_REPO")
github_token  = os.getenv("GITHUB_TOKEN")



#get all the file names (chapters) and count the words in each 
summary       = []
page_iterator = s3.get_paginator('list_objects_v2').paginate(Bucket=bucket) #paginate list_objects_v2 as it maxes out at 1000 files
for page in page_iterator:                                                  # loop through the pages - there should be 2 as there are 1193 files (chapters)
   contents = page.get('Contents', [])
   for obj in contents:
       key = obj['Key']
       if key.endswith('.txt'):      
           text = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
           word_count = len(text.split())
           summary.append({'chapter': key, 'word_count': word_count})
           print(key, word_count)



summary_df = pd.DataFrame(summary)

# create the chapters word count file
summary_df[['book', 'chapter_number']] = summary_df['chapter'].str.extract(r'^(.*?)\s+(\d+)\.txt$')
summary_df                            = summary_df[['book', 'chapter_number', 'word_count']]
summary_df['chapter_number']          = summary_df['chapter_number'].str.extract(r'(\d+)$')
chapters_csv = summary_df.to_csv(index=False)

# create the book word count file
summary_book_df = summary_df.groupby('book').agg(
    chapters=('chapter_number', 'size'),
    word_count=('word_count', 'sum')
).reset_index()
books_csv = summary_book_df.to_csv(index=False)


# upload the files to Github
repo = Github(github_token).get_repo(github_repo)

blob1 = repo.create_git_blob(chapters_csv, "utf-8")
blob2 = repo.create_git_blob(books_csv, "utf-8")

element1 = InputGitTreeElement(path="chapter_wordcount.csv", mode="100644", type="blob", sha=blob1.sha)
element2 = InputGitTreeElement(path="book_wordcount.csv", mode="100644", type="blob", sha=blob2.sha)

ref       = repo.get_git_ref(f"heads/{repo.default_branch}")
parent    = repo.get_git_commit(ref.object.sha)
base_tree = parent.tree 
tree      = repo.create_git_tree([element1, element2], base_tree=base_tree)

commit = repo.create_git_commit(
    "Add word count summaries",
    tree,
    [parent]
)
ref.edit(commit.sha)
print("Committed multiple files to GitHub.")