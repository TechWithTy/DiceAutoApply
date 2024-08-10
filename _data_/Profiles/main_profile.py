from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
import os

# Import the JobFilter class
from _data_.Filters.diceFilterSettings import JobFilter, dice_job_filter
# Import the InterviewAnswerDataset class
from _data_.Profiles.interviewQuestions import InterviewAnswerDataset
from dotenv import load_dotenv

# Load environment variables from a .env file (if applicable)
load_dotenv()

# Fetching environment variables
secrets = {
    "linkedin_profile": os.getenv("LINKEDIN_PROFILE", "https://linkedin.com/in/default"),
    "name": os.getenv("NAME", "Default Name"),
    "email": os.getenv("EMAIL", "default@example.com"),
    "phone_number": os.getenv("PHONE_NUMBER", "000-000-0000"),
    "website": os.getenv("WEBSITE", "https://google.com"),
    "portfolio": os.getenv("PORTFOLIO", "https://google.com"),
    "booking_link": os.getenv("BOOKME", "https://google.com")
}

@dataclass
class JobTitle:
    title: str
    experience: int
    relevant_resume_path: str  # Path to the resume file
    interview_questions: InterviewAnswerDataset  # Move this before skills
    skills: List[str] = field(default_factory=list)
    max_apply_jobs: int = 100  # Default value for max_apply_jobs


class ApplyEvery(Enum):
    ONE_HOUR = "1Hour"
    FOUR_HOURS = "4Hours"
    EIGHT_HOURS = "8Hours"
    SIXTEEN_HOURS = "16Hours"
    TWENTY_FOUR_HOURS = "24Hours"


@dataclass
class UserProfile:
    name: str
    email: str
    online_presence: Dict[str, str]  # Correctly using Dict for dictionary type
    phone_number: str
    linkedin_profile: str
    about_me: str
    job_titles: List[JobTitle]  # List of JobTitle instances
    dice_job_filter: JobFilter  # User's job filter preferences
    main_interview_questions: InterviewAnswerDataset  # General interview questions
    city: str
    country: str
    timezone: str
    apply_every: ApplyEvery


# Instantiate the user_profile at the module level for importing
interview_data = InterviewAnswerDataset()

job_titles = [
    JobTitle(
        title="AI Engineer",
        experience=7,
        relevant_resume_path=r"_data_\\Resumes\\8-6-24-Ai-Full-Stack.pdf",
        skills=[
            "Python", "TensorFlow", "PyTorch", "Machine Learning", "Docker",
            "Kubernetes", "CI/CD", "Unit Testing"
        ],
        interview_questions=interview_data,
        max_apply_jobs=100
    ),
    JobTitle(
        title="Data Scientist",
        experience=5,
        relevant_resume_path=r"_data_\\Resumes\\8-6-24-Ai-Full-Stack.pdf",
        skills=[
            "Python", "Machine Learning", "Data Analysis", "TensorFlow",
            "PyTorch", "Sci-kit Learn", "Pandas", "SQL", "Feature Engineering"
        ],
        interview_questions=interview_data,
        max_apply_jobs=50
    ),
    JobTitle(
        title="Full Stack Developer",
        experience=6,
        relevant_resume_path=r"_data_\\Resumes\\8-6-24-Ai-Full-Stack.pdf",
        skills=[
            "JavaScript", "React", "Node.js", "Redux", "GraphQL", "CI/CD",
            "HTML5", "CSS3", "TypeScript", "Git"
        ],
        interview_questions=interview_data,
        max_apply_jobs=100
    ),
    JobTitle(
        title="AI Automation Engineer",
        experience=3,
        relevant_resume_path=r"_data_\\Resumes\\8-6-24-Ai-Full-Stack.pdf",
        skills=[
            "AI Model Optimization", "Automation", "Python", "TensorFlow",
            "PyTorch", "RAG Systems", "Docker", "Kubernetes"
        ],
        interview_questions=interview_data,
        max_apply_jobs=100
    )
]

about_me = "Enthusiastic software engineer with a keen interest in data science and project management."
online_presence = {
    "website": secrets["website"],
    "portfolio": secrets["portfolio"],
    "booking_link": secrets["booking_link"],
}

user_profile = UserProfile(
    name=secrets["name"],
    online_presence=online_presence,
    email=secrets["email"],
    phone_number=secrets["phone_number"],
    linkedin_profile=secrets["linkedin_profile"],
    about_me=about_me,
    job_titles=job_titles,
    dice_job_filter=dice_job_filter,
    main_interview_questions=interview_data,
    city="Denver",
    country="USA",
    timezone="MST",  # Mountain Standard Time
    apply_every=ApplyEvery.EIGHT_HOURS  # Apply every 8 hours
)

def display_profile(profile: UserProfile):
    """
    Display user profile information.
    """
    print(f"Name: {profile.name}")
    print(f"Email: {profile.email}")
    print(f"Phone Number: {profile.phone_number}")
    print(f"LinkedIn: {profile.linkedin_profile}")
    print(f"About Me: {profile.about_me}")
    print(f"City: {profile.city}")
    print(f"Country: {profile.country}")
    print(f"Timezone: {profile.timezone}")
    print(f"Apply Every: {profile.apply_every.value}")

    print("\nGeneral Interview Questions:")
    for keywords in profile.main_interview_questions.answers:
        general_answer = profile.main_interview_questions.answers[keywords].get("general")
        if general_answer:
            print(f"  - {general_answer}")

    print("\nJob Titles and Resumes:")
    for job_title in profile.job_titles:
        print(f"  Job Title: {job_title.title}")
        print(f"  Resume Path: {job_title.relevant_resume_path}")
        print("  Skills: ")
        for skill in job_title.skills:
            print(f"    - {skill}")
        print("  Interview Questions: ")
        for keywords in job_title.interview_questions.answers:
            general_answer = job_title.interview_questions.answers[keywords].get("general")
            if general_answer:
                print(f"    - {general_answer}")

    print("\nJob Filter Settings:")
    print(f"  Work Setting: {profile.dice_job_filter.work_setting}")
    print(f"  Posted Date: {profile.dice_job_filter.posted_date}")
    print(f"  Employment Types: {', '.join(profile.dice_job_filter.employment_types)}")
    print(f"  Willing to Sponsor: {profile.dice_job_filter.willing_to_sponsor}")
    print(f"  Employer Types: {', '.join(profile.dice_job_filter.employer_types)}")
    print(f"  Easy Apply: {profile.dice_job_filter.easy_apply}")


def main():
    # Display the user profile
    display_profile(user_profile)


if __name__ == "__main__":
    main()
