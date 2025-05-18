#!/usr/bin/env python3

import os
import boto3
import pandas as pd
from github import Github, InputGitTreeElement 


# set variables
s3            = boto3.client('s3')                                          # initialise s3
BUCKET        = 'esv-chapters'
GITHUB_REPO   = 'kellykelso55887/fun-with-the-bible'
github_token  = os.getenv("GITHUB_TOKEN")


#get all the file names (chapters) and count the words in each 
summary       = []
page_iterator = s3.get_paginator('list_objects_v2').paginate(Bucket=BUCKET) #paginate list_objects_v2 as it maxes out at 1000 files
for page in page_iterator:                                                  # loop through the pages - there should be 2 as there are 1193 files (chapters)
   contents = page.get('Contents', [])
   for obj in contents:
       key = obj['Key']
       if key.endswith('.txt'):      
           text = s3.get_object(Bucket=BUCKET, Key=key)['Body'].read().decode('utf-8')
           word_count = len(text.split())
           summary.append({'chapter': key, 'word_count': word_count})
           print(key, word_count)



summary_df = pd.DataFrame(summary)

# create the chapters word count file
summary_df[['book','chapter_number']] = summary_df['chapter'].str.replace('.txt', '', regex=False).str.split('/', expand=True)
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
repo = Github(github_token).get_repo(GITHUB_REPO)

blob1 = repo.create_git_blob(chapters_csv, "utf-8")
blob2 = repo.create_git_blob(books_csv, "utf-8")

element1 = InputGitTreeElement(path="chapter_wordcount.csv", mode="100644", type="blob", sha=blob1.sha)
element2 = InputGitTreeElement(path="book_wordcount.csv", mode="100644", type="blob", sha=blob2.sha)

ref = repo.get_git_ref(f"heads/{repo.default_branch}")
parent = repo.get_git_commit(ref.object.sha)
base_tree = parent.tree 
tree = repo.create_git_tree([element1, element2], base_tree=base_tree)

commit = repo.create_git_commit(
    "Add word count summaries",
    tree,
    [parent]
)
ref.edit(commit.sha)
print("Committed multiple files to GitHub.")



