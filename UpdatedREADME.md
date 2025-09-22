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
- [x] **Auto-apply to Different Job Titles**: Implement functionality to automatically apply for multiple job titles within the profile.

### Upcoming Features
- [ ] **Scheduled Auto Job Applying**: Apply to these jobs every day at a set time
- [ ] **Answer Questions with AI**: Leverage LLMs to dynamically generate responses to interview questions based on context and job requirements.
- [ ] **Improved Decision Making with AI**: Use AI to make decisions during applications, such as selecting suitable options in forms and evaluating job descriptions.
- [ ] **User Interface for Configurations**: Build a user-friendly interface for setting up profiles and job filters with streamlit.

### Stretch Goals

- [ ] **Advanced LLM Integration**: Enable complex decision-making processes during job applications with AI assistance.
- [ ] **Cross-platform Support**: Expand automation support to additional job application platforms beyond Dice (LI).

## Setup

### Prerequisites

 - Python 3.8+
 - uv (install via `winget install Astral-uv` or `pipx install uv`)
 - Playwright browsers (installed via a command below)

### Installation

1. **Clone the Repository**:

   ```bash
   git clone {repo}
   cd DiceAutoApply
   ```

2. **Install Project Dependencies (uv)**:

   ```bash
   uv sync
   ```

3. **Install Playwright Browser (Chromium)**:

   ```bash
   uv run playwright install chromium
   ```

3. **Setup Environment Variables**:

   Create a `.env` file in the root of the project directory with the following content:

   ```plaintext
   EMAIL=your-email@example.com
   PASSWORD=your-password
   SEARCH_KEYWORDS=your-search-keywords
   WEBSITE=https://yourwebsite.com
   PORTFOLIO=https://yourportfolio.com
   BOOKME=https://yourbookinglink.com (Scheduling link)
   LINKEDIN_PROFILE=https://linkedin.com/in/yourprofile
   NAME=Your Full Name
   PHONE_NUMBER=123-456-7890
   ```

   Update these values with your actual data.
   
   Tip (Windows):
   ```powershell
   copy .env.example .env
   ```

### Environment Variables Usage

- **EMAIL**: Your email address used for applications.
- **PASSWORD**: Your password for logging into job platforms.
- **SEARCH_KEYWORDS**: Keywords for searching job listings.
--------------------------------------------------------------
- **WEBSITE**: Personal or professional website URL.
- **PORTFOLIO**: Link to your portfolio.
- **BOOKME**: Booking link for scheduling interviews.
- **LINKEDIN_PROFILE**: Link to your LinkedIn profile.
- **NAME**: Your full name.
- **PHONE_NUMBER**: Your contact number.

### Running the Project

1. **Run the automation (uv)**:

   ```bash
   uv run --env-file .env apply-dice
   ```

   Notes:
   - The console entry point `apply-dice` is defined in `pyproject.toml` under `[project.scripts]` as `app.dice.AutomateDiceMin:main`.
   - Alternatively, you can run the module directly:
     ```bash
     uv run python -m app.dice.AutomateDiceMin
     ```

### Headless Mode

To run the automation in headless mode:

**PowerShell:**
```powershell
.\run_headless.ps1
```

**Git Bash:**
```bash
./run_headless.sh
```

**Windows CMD:**
```cmd
run_headless.bat
```

### Conclusion

This project provides a comprehensive framework for automating job applications, managing user profiles, and preparing for interviews. By leveraging environment variables and integrating LLMs, the system offers flexibility and dynamic response generation.

Feel free to contribute to this project by submitting issues or pull requests on [GitHub](https://github.com/yourusername/automate-job-application).

---

### Notes

- Make sure to replace placeholders like `/path/to/resume.pdf` and GitHub links with actual values relevant to your project.
- Adjust the LLM integration as necessary to fit your specific use case, especially if you have specific API usage requirements or limitations.

This updated README provides a clear roadmap for your project, highlighting both the current features and future enhancements planned for the automation tool.