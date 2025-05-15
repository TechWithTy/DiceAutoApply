"""
FastAPI-based API for headless Dice job automation.
"""
import sys
print(sys.path)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from app.dice.utils.login import login
from app.dice.utils.extract import extract_job_ids
from app.dice.utils.apply import write_job_titles_to_file
from app.dice.utils.profile_to_url import userprofile_to_search_url
from _data_.Profiles.main_profile import user_profile

# Load environment variables
load_dotenv()

app = FastAPI(title="Dice AutoApply API", description="Headless Dice automation as an API.")

class JobApplyRequest(BaseModel):
    job_title: Optional[str] = None
    location: Optional[str] = None
    # Extend with more search params as needed

class JobApplyResult(BaseModel):
    applied: int
    failed: int
    failed_jobs: List[str]
    message: str

@app.post("/apply-jobs", response_model=JobApplyResult)
def apply_jobs(request: JobApplyRequest):
    """
    Run the Dice automation workflow headlessly for the given search params.
    """
    job_title = request.job_title or "Full Stack Developer"
    location = request.location or "Remote"
    failed_jobs = []
    applied_count = 0
    failed_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            login(page)
            search_url = userprofile_to_search_url(user_profile, job_title=job_title, location=location)
            page.goto(search_url)
            job_ids = []
            extract_job_ids(page, job_ids)
            if not job_ids:
                return JobApplyResult(applied=0, failed=0, failed_jobs=[], message="No jobs found.")
            # Write job titles to file and attempt to apply
            output_file = f"applied_jobs_{job_title.replace(' ', '_')}.txt"
            applied, failed, failed_jobs = write_job_titles_to_file(page, job_ids, output_file)
            message = f"Applied to {applied} jobs, {failed} failed."
            return JobApplyResult(applied=applied, failed=failed, failed_jobs=failed_jobs, message=message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Automation error: {str(e)}")
        finally:
            context.close()
            browser.close()
