Sure, let's enhance the `README.md` with a **Roadmap** section to provide a clear path of current and future features for your job application automation project. Here's the updated version with the roadmap included.

---

# Job Application Automation Project

## Overview

This project is designed to automate job applications on platforms like Dice, leveraging environment variables, dynamic job filters, user profiles, and interview questions.

## Features

- **User Profile Management**: Easily manage user details, including personal information, job titles, and skills.
- **Job Filter Customization**: Configure job search filters for targeted job applications.
- **Interview Preparation**: Access a predefined set of interview questions.
- **Environment Variable Configuration**: Securely store and manage sensitive data using environment variables.

## Roadmap

Here are some of the current and planned features for the project:

### Current Features

- [x] **Load Environment Variables**: Use `.env` files for configuration.
- [x] **Set Up Job Filters**: Configure job filters for specific job searches.
- [x] **Manage User Profiles**: Create and display user profiles with detailed information.
- [x] **Integrate Static Interview Questions**: Use predefined questions and answers.
- [x] **Support Multiple Job Titles**: Manage applications for different job titles within the same user profile.

### Upcoming Features

- [ ] **Auto-apply to Different Job Titles**: Implement functionality to automatically apply for multiple job titles within the profile.
- [ ] **Answer Questions with AI**: Leverage LLMs to dynamically generate responses to interview questions based on context and job requirements.
- [ ] **Improved Decision Making with AI**: Use AI to make decisions during applications, such as selecting suitable options in forms and evaluating job descriptions.
- [ ] **User Interface for Configurations**: Build a user-friendly interface for setting up profiles and job filters with streamlit.
- [ ] **Scheduled Auto Job Applying**: Apply to these jobs every day at a set time

### Stretch Goals

- [ ] **Advanced LLM Integration**: Enable complex decision-making processes during job applications with AI assistance.
- [ ] **Cross-platform Support**: Expand automation support to additional job application platforms beyond Dice.

## Setup

### Prerequisites

- Python 3.7+
- `python-dotenv` package

### Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/automate-job-application.git
   cd automate-job-application
   ```

2. **Install Required Packages**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Environment Variables**:

   Create a `.env` file in the root of the project directory with the following content:

   ```plaintext
   EMAIL=your-email@example.com
   PASSWORD=your-password
   SEARCH_KEYWORDS=your-search-keywords
   WEBSITE=https://yourwebsite.com
   PORTFOLIO=https://yourportfolio.com
   BOOKME=https://yourbookinglink.com
   LINKEDIN_PROFILE=https://linkedin.com/in/yourprofile
   NAME=Your Full Name
   PHONE_NUMBER=123-456-7890
   ```

   Update these values with your actual data.

### Environment Variables Usage

- **EMAIL**: Your email address used for applications.
- **PASSWORD**: Your password for logging into job platforms.
- **SEARCH_KEYWORDS**: Keywords for searching job listings.
- **WEBSITE**: Personal or professional website URL.
- **PORTFOLIO**: Link to your portfolio.
- **BOOKME**: Booking link for scheduling interviews.
- **LINKEDIN_PROFILE**: Link to your LinkedIn profile.
- **NAME**: Your full name.
- **PHONE_NUMBER**: Your contact number.

### Running the Project

1. **Load Environment Variables**:

   Use `python-dotenv` to load your environment variables at the start of your Python scripts:

   ```python
   from dotenv import load_dotenv
   import os

   # Load environment variables
   load_dotenv()

   # Access variables
   email = os.getenv('EMAIL')
   name = os.getenv('NAME')
   ```

2. **Setting Up User Profile and Job Filters**:

   - **User Profile**: The `UserProfile` class manages user details and job preferences.
   - **Job Filters**: Customize job searches using the `JobFilter` class.

   ```python
   from _data_.filterSettings import JobFilter
   from _data_.interviewQuestions import InterviewAnswerDataset

   # Define Job Filters
   job_filter = JobFilter()
   job_filter.set_work_setting(JobFilter.WorkSetting.REMOTE)
   job_filter.set_posted_date("Last 7 Days")
   job_filter.add_employment_type(JobFilter.EmploymentType.FULL_TIME)
   job_filter.add_employer_type(JobFilter.EmployerType.DIRECT_HIRE)

   # User Profile Setup
   user_profile = UserProfile(
       name=os.getenv('NAME'),
       email=os.getenv('EMAIL'),
       phone_number=os.getenv('PHONE_NUMBER'),
       linkedin_profile=os.getenv('LINKEDIN_PROFILE'),
       about_me="A passionate software engineer with extensive experience.",
       job_titles=[
           JobTitle(
               title="Software Engineer",
               experience=5,
               relevant_resume_path="/path/to/resume.pdf",
               skills=["Python", "Java", "AWS"],
               interview_questions=InterviewAnswerDataset()
           )
       ],
       job_filter=job_filter,
       online_presence={
           "website": os.getenv('WEBSITE'),
           "portfolio": os.getenv('PORTFOLIO'),
           "booking_link": os.getenv('BOOKME')
       }
   )
   ```

3. **Running the Application**:

   Execute your main script to start the job application process:

   ```bash
   python AutomateDice.py
   ```

### Conclusion

This project provides a comprehensive framework for automating job applications, managing user profiles, and preparing for interviews. By leveraging environment variables and integrating LLMs, the system offers flexibility and dynamic response generation.

Feel free to contribute to this project by submitting issues or pull requests on [GitHub](https://github.com/yourusername/automate-job-application).

---

### Notes

- Make sure to replace placeholders like `/path/to/resume.pdf` and GitHub links with actual values relevant to your project.
- Adjust the LLM integration as necessary to fit your specific use case, especially if you have specific API usage requirements or limitations.

This updated README provides a clear roadmap for your project, highlighting both the current features and future enhancements planned for the automation tool.