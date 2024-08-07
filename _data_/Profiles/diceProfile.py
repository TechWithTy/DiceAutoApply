from dataclasses import dataclass, field
from typing import List
import os

from _data_.filterSettings import JobFilter  # Import the JobFilter class
# Import the InterviewAnswerDataset class
from _data_.interviewQuestions import InterviewAnswerDataset
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
    experience: int
    relevant_resume_path: str  # Path to the resume file
    # Skills relevant to the job
    skills: List[str] = field(default_factory=list)
    # Interview questions specific to the job
    interview_questions: InterviewAnswerDataset


@dataclass
class UserProfile:
    name: str
    email: str
    phone_number: str
    linkedin_profile: str
    about_me: str
    job_titles: List[JobTitle]  # List of JobTitle instances
    job_filter: JobFilter  # User's job filter preferences
    main_interview_questions: InterviewAnswerDataset  # General interview questions

    def display_profile(self):
        """
        Display user profile information.
        """
        print(f"Name: {self.name}")
        print(f"Email: {self.email}")
        print(f"Phone Number: {self.phone_number}")
        print(f"LinkedIn: {self.linkedin_profile}")
        print(f"About Me: {self.about_me}")

        print("\nGeneral Interview Questions:")
        for question in self.interview_questions:
            print(f"  - {question}")

        print("\nJob Titles and Resumes:")
        for job_title in self.job_titles:
            print(f"  Job Title: {job_title.title}")
            print(f"  Resume Path: {job_title.relevant_resume_path}")
            print("  Skills: ")
            for skill in job_title.skills:
                print(f"    - {skill}")
            print("  Interview Questions: ")
            for question in job_title.interview_questions:
                print(f"    - {question}")

        print("\nJob Filter Settings:")
        print(f"  Work Setting: {self.job_filter.work_setting}")
        print(f"  Posted Date: {self.job_filter.posted_date}")
        print(f"  Employment Types: {', '.join(
            self.job_filter.employment_types)}")
        print(f"  Willing to Sponsor: {self.job_filter.willing_to_sponsor}")
        print(f"  Employer Types: {', '.join(self.job_filter.employer_types)}")
        print(f"  Easy Apply: {self.job_filter.easy_apply}")


# Example Usage
def main():
    # Define a list of job titles with skills and interview questions
    interview_data = InterviewAnswerDataset()

    job_titles = [
        JobTitle(
            title="Software Engineer",
            experience=7,
            relevant_resume_path="/path/to/software_engineer_resume.pdf",
            skills=["Python", "JavaScript", "React", "Django"],
            interview_questions=interview_data
        ),
        JobTitle(
            title="Data Scientist",
            experience=4,
            relevant_resume_path="/path/to/data_scientist_resume.pdf",
            skills=["Python", "Machine Learning", "Statistics", "TensorFlow"],
            interview_questions=interview_data
        ),
        JobTitle(
            title="Project Manager",
            experience=4,
            relevant_resume_path="/path/to/project_manager_resume.pdf",
            skills=["Project Management", "Agile", "Scrum", "Communication"],
            interview_questions=interview_data
        ),
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

    about_me = "Enthusiastic software engineer with a keen interest in data science and project management."
    # Create a UserProfile instance with general interview questions
    user_profile = UserProfile(
        name=secret_name,
        email=secret_email,
        phone_number=secret_phone_number,
        linkedin_profile=secret_linkedin_profile,
        about_me=about_me,
        job_titles=job_titles,
        job_filter=job_filter,
        main_interview_questions=interview_data
    )

    # Display the user profile
    user_profile.display_profile()


if __name__ == "__main__":
    main()
