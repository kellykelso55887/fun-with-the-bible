#!/usr/bin/env python3

# this file does a wordsearch from the chapters of the bible
# in s3 buckets creates a web server to interact with it
# last reviewed on 18 May 2025

# run 'aws sso login' then './word_search.py

import os
from fastapi import FastAPI, HTTPException, Request
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import re
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import traceback
from dotenv import load_dotenv 


load_dotenv('/Users/mogsta/fun-with-the-bible/.env')                                   # loads variables from .env
app         = FastAPI()
s3          = boto3.client("s3")
bucket_name = os.getenv("BUCKET")

# the following search needs to search synonyms
@app.get("/search")
def search_word(q: str):
    results = []
    try:
        # List all objects (chapters) in the S3 bucket by pages (as capped to 1000 per page)
        resp_iterator = s3.get_paginator('list_objects_v2').paginate(Bucket=bucket_name)
        for resp in resp_iterator:
            contents = resp.get("Contents",[])
            for obj in contents:
                key = obj["Key"]  # e.g., "Genesis1.txt"
                if key.endswith('.txt'): 
                    # Fetch object content
                    content = s3.get_object(Bucket=bucket_name, Key=key)["Body"].read().decode("utf-8")
                    # Split into sentences (simple regex)
                    sentences = re.split(r'(?<=[.!?])\s+|\n+', content)
                    # Find sentences containing the query (case-sensitive)
                    for sentence in sentences:
                        if q in sentence:
                            results.append({"file": key, "sentence": sentence.strip()})
    except Exception as e:
        print("Error during search:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    return {"matches": results}


# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



#####################################################################
# testing by loading the s3 object locally
#response = s3.get_object(Bucket=bucket_name, Key="1 Timothy 1.txt")
#content = response['Body'].read().decode('utf-8')
