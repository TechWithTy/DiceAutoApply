from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
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
    uploaded_resume_name: Optional[str] = None  # Existing Dice resume label/file name to re-select
    generated_resume_profile_id: Optional[str] = None  # Generated profile id from backend/resume_builder/data/generated_profiles
    work_settings: Optional[List[str]] = None  # Local search settings; None uses the profile-wide filter.
    remote_work_settings: Optional[List[str]] = field(
        default_factory=lambda: [
            JobFilter.WorkSetting.REMOTE,
            JobFilter.WorkSetting.HYBRID,
            JobFilter.WorkSetting.ONSITE,
        ]
    )  # Override per title when a Remote search should use a narrower setting.


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
    cities: List[str]
    country: str
    timezone: str
    apply_every: ApplyEvery

    @property
    def city(self) -> str:
        return self.cities[0] if self.cities else ""

    @city.setter
    def city(self, value: str) -> None:
        normalized = (value or "").strip()
        self.cities = [normalized] if normalized else []


# Instantiate the user_profile at the module level for importing
interview_data = InterviewAnswerDataset()
MAIN_DICE_RESUME = r"_data_\Resumes\Dice\Tyrique Daniel Updated Data Resume.pdf"
AI_SOLUTIONS_RESUME = r"_data_\Resumes\Dice\Tyrique Daniel - AI Automation Solutions Engineer.pdf"
TECHNICAL_LEAD_RESUME = r"_data_\Resumes\Dice\Tyrique Daniel - Technical Lead Founding Engineer.pdf"
FORWARD_DEPLOYED_RESUME = r"_data_\Resumes\Dice\Tyrique Daniel - Forward Deployed Engineer.pdf"
BACKEND_PLATFORM_RESUME = r"_data_\Resumes\Dice\Tyrique Daniel - Senior Backend Platform Engineer.pdf"

job_titles = [
   

         JobTitle(
        title="Full Stack AI Engineer",
        experience=6,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "Python", "JavaScript", "React", "Node.js", "Golang", "Docker",
            "Kubernetes", "GraphQL", "CI/CD", "Machine Learning Integration"
        ],
        interview_questions=interview_data,
        max_apply_jobs=100
    ),
    JobTitle(
        title="AI Integration Engineer",
        experience=6,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=[
            "Python", "JavaScript", "React", "Node.js", "Golang", "Docker",
            "Kubernetes", "GraphQL", "CI/CD", "Machine Learning Integration"
        ],
        interview_questions=interview_data,
        max_apply_jobs=100
    ),
    JobTitle(
        title="Senior Full Stack Developer",
        experience=7,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "JavaScript", "React", "Next.js", "Node.js", "Golang", "GraphQL",
            "Docker", "Kubernetes", "CI/CD", "TypeScript", "Git"
        ],
        interview_questions=interview_data,
        max_apply_jobs=100
    ),
    JobTitle(
        title="Full Stack Engineer",
        experience=5,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "JavaScript", "React", "Node.js", "Python", "Golang", "Docker",
            "CI/CD", "Git", "GraphQL", "HTML5", "CSS3"
        ],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Frontend Engineer",
        experience=4,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "JavaScript", "React", "Next.js", "HTML5", "CSS3", "Tailwind CSS",
            "GraphQL", "REST APIs", "AI Integration"
        ],
        interview_questions=interview_data,
        max_apply_jobs=60
    ),
    JobTitle(
        title="TypeScript Developer",
        experience=5,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "TypeScript", "JavaScript", "React", "Next.js", "Node.js", "Python", "Golang", "Docker", "CI/CD", "GraphQL", "HTML5", "CSS3"
        ],
        interview_questions=interview_data,
        max_apply_jobs=70
    ),
    JobTitle(
        title="React Developer",
        experience=5,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "React", "JavaScript", "Next.js", "HTML5", "CSS3", "TypeScript",
            "GraphQL", "REST APIs", "Tailwind CSS"
        ],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Next.js Developer",
        experience=5,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "Next.js", "React", "JavaScript", "TypeScript", "HTML5", "CSS3",
            "GraphQL", "REST APIs", "Tailwind CSS"
        ],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Full Stack Software Engineer",
        experience=6,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "JavaScript", "React", "Node.js", "Golang", "GraphQL", "Docker",
            "CI/CD", "HTML5", "CSS3", "TypeScript", "Git"
        ],
        interview_questions=interview_data,
        max_apply_jobs=90
    ),
    JobTitle(
        title="Web Developer",
        experience=5,
        relevant_resume_path=MAIN_DICE_RESUME,
        skills=[
            "JavaScript", "Next.js", "React", "TypeScript", "GraphQL",
            "HTML5", "CSS3", "Tailwind CSS", "REST APIs", "Node.js"
        ],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Founding Engineer",
        experience=5,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=[
            "System Design", "TypeScript", "React", "Node.js", "Python",
            "PostgreSQL", "Kubernetes", "Terraform", "Technical Strategy"
        ],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="AI Solutions Engineer",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["TypeScript", "Python", "REST APIs", "CRM Integrations", "LLMs", "AWS", "Google Cloud", "Kubernetes"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="AI Automation Engineer",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["Python", "TypeScript", "AI Agents", "LLMs", "Webhooks", "REST APIs", "CRM Integrations", "Docker"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Solutions Architect",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["System Design", "API Design", "AWS", "Google Cloud", "Kubernetes", "CRM Integrations", "PostgreSQL"],
        interview_questions=interview_data,
        max_apply_jobs=70
    ),
    JobTitle(
        title="Technical Solutions Engineer",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["Python", "TypeScript", "REST APIs", "GraphQL", "Webhooks", "Customer Integrations", "AWS"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Implementation Engineer",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["API Integrations", "REST APIs", "Webhooks", "CRM Integrations", "Python", "PostgreSQL", "Docker"],
        interview_questions=interview_data,
        max_apply_jobs=70
    ),
    JobTitle(
        title="Forward Deployed Engineer",
        experience=8,
        relevant_resume_path=FORWARD_DEPLOYED_RESUME,
        skills=["Python", "TypeScript", "LLMs", "AI Agents", "API Integrations", "AWS", "Kubernetes"],
        interview_questions=interview_data,
        max_apply_jobs=70
    ),
    JobTitle(
        title="Senior Backend Engineer",
        experience=8,
        relevant_resume_path=BACKEND_PLATFORM_RESUME,
        skills=["Python", "Node.js", "Go", "PostgreSQL", "REST APIs", "Microservices", "Event-Driven Systems", "Kubernetes"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Senior Platform Engineer",
        experience=8,
        relevant_resume_path=BACKEND_PLATFORM_RESUME,
        skills=["Python", "Go", "Apache Pulsar", "Redis", "Kubernetes", "Docker", "AWS", "Google Cloud", "Observability"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Integration Engineer",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["REST APIs", "GraphQL", "Webhooks", "CRM Integrations", "Node.js", "Python", "PostgreSQL"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Customer Engineer",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["Technical Discovery", "API Integrations", "CRM Integrations", "TypeScript", "Python", "AWS", "Google Cloud"],
        interview_questions=interview_data,
        max_apply_jobs=60
    ),
    JobTitle(
        title="AI Consultant",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["LLMs", "AI Agents", "Workflow Automation", "API Integrations", "Python", "TypeScript", "Cloud Architecture"],
        interview_questions=interview_data,
        max_apply_jobs=60
    ),
    JobTitle(
        title="Automation Architect",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["Workflow Orchestration", "Event-Driven Systems", "Apache Pulsar", "AI Agents", "CRM Integrations", "Kubernetes"],
        interview_questions=interview_data,
        max_apply_jobs=60
    ),
    JobTitle(
        title="Technical Consultant",
        experience=8,
        relevant_resume_path=AI_SOLUTIONS_RESUME,
        skills=["Technical Discovery", "Solutions Architecture", "API Integrations", "REST APIs", "Python", "TypeScript", "AWS"],
        interview_questions=interview_data,
        max_apply_jobs=60
    ),
    JobTitle(
        title="Lead Software Engineer",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["System Design", "TypeScript", "Python", "Event-Driven Systems", "Kubernetes", "PostgreSQL", "Technical Leadership"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Technical Lead",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["Architecture Reviews", "Technical Strategy", "React", "Node.js", "Python", "Kubernetes", "Team Leadership"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Engineering Lead",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["Technical Leadership", "System Design", "CI/CD", "Cloud Infrastructure", "Cross-Functional Delivery", "Mentorship"],
        interview_questions=interview_data,
        max_apply_jobs=70
    ),
    JobTitle(
        title="Lead Full Stack Engineer",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["TypeScript", "React", "Next.js", "Node.js", "Python", "PostgreSQL", "AWS", "Kubernetes"],
        interview_questions=interview_data,
        max_apply_jobs=80
    ),
    JobTitle(
        title="Principal Engineer",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["System Design", "Microservices", "Event-Driven Systems", "Cloud Architecture", "Technical Strategy", "Architecture Reviews"],
        interview_questions=interview_data,
        max_apply_jobs=60
    ),
    JobTitle(
        title="Startup CTO",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["Product Architecture", "Technical Strategy", "Team Leadership", "Cloud Platform", "CI/CD", "Full Stack Development"],
        interview_questions=interview_data,
        max_apply_jobs=50
    ),
    JobTitle(
        title="Head of Engineering",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["Engineering Leadership", "Technical Strategy", "System Design", "Delivery Management", "Cloud Infrastructure", "Mentorship"],
        interview_questions=interview_data,
        max_apply_jobs=50
    ),
    JobTitle(
        title="Senior Staff Engineer",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["System Design", "Distributed Systems", "Technical Strategy", "Event-Driven Systems", "Kubernetes", "PostgreSQL"],
        interview_questions=interview_data,
        max_apply_jobs=60
    ),
    JobTitle(
        title="Platform Lead",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["Platform Architecture", "Kubernetes", "Docker", "Terraform", "CI/CD", "Observability", "AWS"],
        interview_questions=interview_data,
        max_apply_jobs=70
    ),
    JobTitle(
        title="Product Engineering Lead",
        experience=8,
        relevant_resume_path=TECHNICAL_LEAD_RESUME,
        skills=["Product Architecture", "React", "Node.js", "Python", "Technical Strategy", "Cross-Functional Delivery", "CI/CD"],
        interview_questions=interview_data,
        max_apply_jobs=70
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
    cities=["Remote", "Denver, CO", "Boulder, CO", "Aurora, CO"],
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
    print(f"Primary City: {profile.city}")
    print(f"Cities: {', '.join(profile.cities)}")
    print(f"Country: {profile.country}")
    print(f"Timezone: {profile.timezone}")
    print(f"Apply Every: {profile.apply_every.value}")

    print("\nGeneral Interview Questions:")
    for keywords in profile.main_interview_questions.answers:
        general_answer = profile.main_interview_questions.answers[keywords].get(
            "general")
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
            general_answer = job_title.interview_questions.answers[keywords].get(
                "general")
            if general_answer:
                print(f"    - {general_answer}")

    print("\nJob Filter Settings:")
    print(f"  Work Setting: {profile.dice_job_filter.work_setting}")
    print(f"  Posted Date: {profile.dice_job_filter.posted_date}")
    print(f"  Employment Types: {', '.join(
        profile.dice_job_filter.employment_types)}")
    print(f"  Willing to Sponsor: {
          profile.dice_job_filter.willing_to_sponsor}")
    print(f"  Employer Types: {', '.join(
        profile.dice_job_filter.employer_types)}")
    print(f"  Easy Apply: {profile.dice_job_filter.easy_apply}")


def main():
    # Display the user profile
    display_profile(user_profile)


if __name__ == "__main__":
    main()
