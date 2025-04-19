import os
import boto3
import pandas as pd
from github import Github, GithubException

# set variables
s3            = boto3.client('s3')                                          # initialise s3
BUCKET        = 'esv-chapters'
GITHUB_REPO   = 'kellykelso55887/fun-with-the-bible'
github_token  = os.getenv("GITHUB_TOKEN")


# get all the file names (chapters) and count the words in each 
#summary       = []
#page_iterator = s3.get_paginator('list_objects_v2').paginate(Bucket=BUCKET) #paginate list_objects_v2 as it maxes out at 1000 files
#for page in page_iterator:                                                  # loop through the pages - there should be 2 as there are 1193 files (chapters)
#    contents = page.get('Contents', [])
#    for obj in contents:
#        key = obj['Key']
#        if key.endswith('.txt'):
#            text = s3.get_object(Bucket=BUCKET, Key=key)['Body'].read().decode('utf-8')
#            word_count = len(text.split())
#            summary.append({'chapter': key, 'word_count': word_count})
#            print(key, word_count)


summary = [{'chapter': 'Zephaniah/Zephaniah 1.txt', 'word_count': 520}, {'chapter': 'Zephaniah/Zephaniah 2.txt', 'word_count': 449}, {'chapter': 'Zephaniah/Zephaniah 3.txt', 'word_count': 587}]
summary_df  = pd.DataFrame(summary)
summary_csv = summary_df.to_csv(index=False)


repo = Github(github_token).get_repo(GITHUB_REPO)

try:
    contents = repo.get_contents('chapter_wordcount.csv')
    repo.update_file(
        path=contents.path,
        message='Update word count summary',
        content=summary_csv,
        sha=contents.sha,
        branch='main'
    )
    print("Updated chapter_wordcount.csv in GitHub repo.")
except GithubException as e:
    if e.status == 404:
        repo.create_file(
            path='chapter_wordcount.csv',
            message='Add word count summary',
            content=summary_csv,
            branch='main'
         )
        print("Created chapter_wordcount.csv in GitHub repo.")
    else:
        raise e
    


