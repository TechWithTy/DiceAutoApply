from dataclasses import dataclass, field
from typing import List
import os

from _data_.filterSettings import JobFilter  # Import the JobFilter class
from dotenv import load_dotenv
# Load environment variables from a .env file (if applicable)
load_dotenv()

# Fetching environment variables
secret_linkedin_profile = os.getenv(
    "LINKEDIN_PROFILE", "https://linkedin.com/in/default")
secret_name = os.getenv("NAME", "Default Name")
secret_email = os.getenv("EMAIL", "default@example.com")
secret_phone_number = os.getenv("PHONE_NUMBER", "000-000-0000")


@dataclass
class JobTitle:
    title: str
    relevant_resume_path: str  # Path to the resume file


@dataclass
class UserProfile:
    name: str
    email: str
    phone_number: str
    linkedin_profile: str
    job_titles: List[JobTitle]  # List of JobTitle instances
    job_filter: JobFilter  # User's job filter preferences

    def display_profile(self):
        """
        Display user profile information.
        """
        print(f"Name: {self.name}")
        print(f"Email: {self.email}")
        print(f"Phone Number: {self.phone_number}")
        print(f"LinkedIn: {self.linkedin_profile}")

        print("Job Titles and Resumes:")
        for job_title in self.job_titles:
            print(f"  Job Title: {job_title.title}")
            print(f"  Resume Path: {job_title.relevant_resume_path}")

        print("Job Filter Settings:")
        print(f"  Work Setting: {self.job_filter.work_setting}")
        print(f"  Posted Date: {self.job_filter.posted_date}")
        print(f"  Employment Types: {', '.join(
            self.job_filter.employment_types)}")
        print(f"  Willing to Sponsor: {self.job_filter.willing_to_sponsor}")
        print(f"  Employer Types: {', '.join(self.job_filter.employer_types)}")
        print(f"  Easy Apply: {self.job_filter.easy_apply}")

# Example Usage


def main():
    # Define a list of job titles
    job_titles = [
        JobTitle(title="Software Engineer",
                 relevant_resume_path="/path/to/software_engineer_resume.pdf"),
        JobTitle(title="Data Scientist",
                 relevant_resume_path="/path/to/data_scientist_resume.pdf"),
        JobTitle(title="Project Manager",
                 relevant_resume_path="/path/to/project_manager_resume.pdf"),
    ]

    # Define the JobFilter with the desired settings
    job_filter = JobFilter()
    job_filter.set_work_setting(JobFilter.WorkSetting.REMOTE)
    job_filter.set_posted_date("Last 7 Days")
    job_filter.add_employment_type(JobFilter.EmploymentType.FULL_TIME)
    job_filter.add_employment_type(JobFilter.EmploymentType.CONTRACT)
    job_filter.set_willing_to_sponsor(False)
    job_filter.add_employer_type(JobFilter.EmployerType.DIRECT_HIRE)
    job_filter.set_easy_apply(True)

    # Create a UserProfile instance
    user_profile = UserProfile(
        name=secret_name,
        email=secret_email,
        phone_number=secret_phone_number,
        linkedin_profile=secret_linkedin_profile,
        job_titles=job_titles,
        job_filter=job_filter
    )
    # Display the user profile
    user_profile.display_profile()

if __name__ == "__main__":
    main()
