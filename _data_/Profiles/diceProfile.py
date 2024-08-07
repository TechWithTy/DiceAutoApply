from dataclasses import dataclass, field
from typing import Dict, List
import os

from _data_.filterSettings import JobFilter, job_filter  # Import the JobFilter class
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

secret_website = os.getenv("WEBSITE", "HTTPS://GOOGLE.COM")
secret_portfollio = os.getenv("PORTFOLLIO", "HTTPS://GOOGLE.COM")
secret_booking_link = os.getenv("BOOKME", "HTTPS://GOOGLE.COM")


@dataclass
class JobTitle:
    title: str
    experience: int
    relevant_resume_path: str  # Path to the resume file
    skills: List[str] = field(default_factory=list)
    interview_questions: InterviewAnswerDataset


@dataclass
class UserProfile:
    name: str
    email: str
    online_presence: Dict[str, str]  # Correctly using Dict for dictionary type
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
            relevant_resume_path="_data_\Resumes\8-5-24-Ai-Full-Stack.pdf",
            skills=["Python", "JavaScript", "React", "Django"],
            interview_questions=interview_data
        ),
        JobTitle(
            title="Data Scientist",
            experience=4,
            relevant_resume_path="_data_\Resumes\8-5-24-Ai-Full-Stack.pdf",
            skills=["Python", "Machine Learning", "Statistics", "TensorFlow"],
            interview_questions=interview_data
        ),
        JobTitle(
            title="Project Manager",
            experience=4,
            relevant_resume_path="_data_\Resumes\8-5-24-Ai-Full-Stack.pdf",
            skills=["Project Management", "Agile", "Scrum", "Communication"],
            interview_questions=interview_data
        ),
    ]

    about_me = "Enthusiastic software engineer with a keen interest in data science and project management."
    online_presence = {
        "website": secret_website,
        "portfolio": secret_portfollio,
        "booking_link": secret_booking_link,

    },
    # Create a UserProfile instance with general interview questions
    user_profile = UserProfile(
        name=secret_name,
        online_presence=online_presence,
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
