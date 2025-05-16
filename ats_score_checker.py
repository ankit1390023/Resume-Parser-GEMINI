import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def setup_gemini():
    """Setup Gemini API with the API key."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY in your .env file")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def analyze_resume(resume_text):
    """
    Analyze resume using Gemini API and return ATS score and feedback.
    
    Args:
        resume_text (str): The content of the resume
        
    Returns:
        str: Formatted analysis results
    """
    model = setup_gemini()
    
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) analyzer. Analyze this resume and provide a detailed assessment.
    
    Resume content:
    {resume_text}
    
    Please analyze the resume for the following categories and provide scores. Calculate the overall score by taking the weighted average of all categories:
    
    1. Content Quality (15% of total score):
       - Relevance of information
       - Clarity of descriptions
       - Professional tone
       - Value proposition
    
    2. ATS Parse Rate (15% of total score):
       - Machine readability
       - File format compatibility
       - Text extraction accuracy
       - Character recognition
    
    3. Quantifying Impact (15% of total score):
       - Use of metrics and numbers
       - Achievement quantification
       - Results-oriented language
       - Performance indicators
    
    4. Repetition Check (10% of total score):
       - Redundant information
       - Word variety
       - Phrase repetition
       - Content uniqueness
    
    5. Spelling & Grammar (10% of total score):
       - Spelling accuracy
       - Grammar correctness
       - Punctuation
       - Language consistency
    
    6. Format (10% of total score):
       - Document structure
       - Layout consistency
       - White space usage
       - Visual hierarchy
    
    7. Sections (12.5% of total score):
       - Required sections presence
       - Section organization
       - Content distribution
       - Section relevance
    
    8. Style (12.5% of total score):
       - Professional appearance
       - Font consistency
       - Design elements
       - Visual appeal
    
    Provide your response in the following format:
    
    Overall ATS Score: [total score out of 100]
    
    Detailed Scores (out of 100 for each category):
    - Content Quality: [score]/100 (15% weight)
    - ATS Parse Rate: [score]/100 (15% weight)
    - Quantifying Impact: [score]/100 (15% weight)
    - Repetition Check: [score]/100 (10% weight)
    - Spelling & Grammar: [score]/100 (10% weight)
    - Format: [score]/100 (10% weight)
    - Sections: [score]/100 (12.5% weight)
    - Style: [score]/100 (12.5% weight)
    
    Category Analysis:
    1. Content Quality:
       [Detailed feedback]
    
    2. ATS Parse Rate:
       [Detailed feedback]
    
    3. Quantifying Impact:
       [Detailed feedback]
    
    4. Repetition Check:
       [Detailed feedback]
    
    5. Spelling & Grammar:
       [Detailed feedback]
    
    6. Format:
       [Detailed feedback]
    
    7. Sections:
       [Detailed feedback]
    
    8. Style:
       [Detailed feedback]
    
    Key Strengths:
    1. [First strength]
    2. [Second strength]
    3. [Third strength]
    
    Areas for Improvement:
    1. [First improvement]
    2. [Second improvement]
    3. [Third improvement]
    
    Actionable Recommendations:
    1. [First recommendation]
    2. [Second recommendation]
    3. [Third recommendation]
    
    Note: The overall score is calculated as a weighted average of all categories, ensuring the final score is out of 100.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing resume: {str(e)}"

def get_ats_score(resume_text):
    """
    Get ATS score for the given resume text.
    This function can be imported and used by other modules.
    
    Args:
        resume_text (str): The content of the resume
        
    Returns:
        str: Analysis results including score, feedback, and suggestions
    """
    return analyze_resume(resume_text)

if __name__ == "__main__":
    # Example usage
    print("Resume ATS Score Checker using Gemini API")
    print("-" * 50)
    
    # Get resume text from user
    print("\nPlease paste your resume text (press Ctrl+D or Ctrl+Z when finished):")
    resume_lines = []
    try:
        while True:
            line = input()
            resume_lines.append(line)
    except EOFError:
        pass
    
    resume_text = "\n".join(resume_lines)
    
    if not resume_text.strip():
        print("No resume text provided. Exiting...")
        exit(1)
    
    print("\nAnalyzing resume...")
    result = analyze_resume(resume_text)
    print("\nResults:")
    print("-" * 50)
    print(result) 