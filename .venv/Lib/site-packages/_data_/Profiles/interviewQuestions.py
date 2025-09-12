from typing import Dict, Union, Optional


class InterviewAnswerDataset:
    def __init__(self):
        # Initialize a dictionary to store keywords and their corresponding answers
        # Each entry can have a general response and/or yes/no responses
        self.answers: Dict[str, Dict[str, Union[str, str]]] = {
            "citizen|residency|work permit|visa": {
                "general": "Yes, I am a citizen and authorized to work in this country without restrictions.",
                "yes_no": "yes"
            },
            "strengths|strong points|best qualities": {
                "general": "My strengths include adaptability, problem-solving, and strong communication skills."
            },
            "weaknesses|improve|challenges": {
                "general": "One of my weaknesses is that I can be overly detail-oriented, but I am working on balancing my attention to detail with efficiency."
            },
            "teamwork|collaboration|team player": {
                "general": "I thrive in team environments and enjoy collaborating with others to achieve shared goals.",
                "yes_no": "yes"
            },
            "leadership|lead|managerial": {
                "general": "I have experience leading projects and teams, focusing on effective communication and motivating team members."
            },
            "conflict resolution|disagreement|handle conflict": {
                "general": "I handle conflicts by listening to all parties involved, understanding their perspectives, and finding a mutually beneficial resolution."
            },
            "deadline|time management|prioritization": {
                "general": "I prioritize tasks based on deadlines and importance, using time management tools to ensure timely completion."
            },
            "why choose you|fit for this role|why you": {
                "general": "I am a great fit for this role because of my relevant experience, skills, and passion for the industry."
            },
            "past experience|background|career history": {
                "general": "My background includes several years of experience in the field, working on diverse projects and developing key skills."
            },
            "goals|future|career aspirations": {
                "general": "My long-term goals include advancing in my career, taking on leadership roles, and continuing to develop my skills."
            },
            "driver's license|driving license|driver license": {
                "general": "Yes, I have a valid driver's license.",
                "yes_no": "yes"
            },
            "willing to relocate|relocation": {
                "general": "Yes, I am willing to relocate for the right opportunity.",
                "yes_no": "yes"
            },
            "work overtime|weekends": {
                "general": "Yes, I am available to work overtime and weekends when necessary.",
                "yes_no": "yes"
            },
            "currently employed|current job": {
                "general": "No, I am actively seeking new opportunities.",
                "yes_no": "no"
            },
            "experience with|familiar with": {
                "general": "Yes, I have experience with {technology or skill}.",
                "yes_no": "yes"
            },
        }

    def find_answer(self, question: str, expect_yes_no: Optional[bool] = None) -> str:
        """
        Find an answer based on keywords found in the question.
        
        :param question: The question to analyze.
        :param expect_yes_no: Optional flag indicating if a yes/no response is expected.
        :return: A string containing the matched answer or a default response.
        """
        # Convert the question to lowercase for case-insensitive matching
        question_lower = question.lower()

        # Iterate through the keywords and answers
        for keywords, response in self.answers.items():
            # Check if any of the keywords are present in the question
            if any(keyword in question_lower for keyword in keywords.split("|")):
                # Return yes/no answer if expected and available
                if expect_yes_no and "yes_no" in response:
                    return response["yes_no"]
                return response["general"]

        # Return a default response if no keywords match
        return "I'm sorry, I don't have a prepared answer for that question. Can you clarify or ask a different question?"


# Example Usage
def main():
    interview_data = InterviewAnswerDataset()

    # Sample questions
    questions = [
        "Are you a citizen or do you have a work permit?",
        "What are your strengths?",
        "Tell me about your weaknesses.",
        "How do you handle conflict in the workplace?",
        "Why should we choose you for this role?",
        "What are your long-term career goals?",
        "Do you have a driver's license?",
        "Are you willing to relocate?",
        "Can you work overtime or weekends?",
        "Are you currently employed?",
        "Do you have experience with Python?",
    ]

    # Get answers for each question
    for question in questions:
        # Assuming questions with 'do', 'are', 'can' expect yes/no answers
        expect_yes_no = question.lower().startswith(("do", "are", "can"))
        answer = interview_data.find_answer(question, expect_yes_no)
        print(f"Question: {question}\nAnswer: {answer}\n")


if __name__ == "__main__":
    main()
