import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

def setup_gemini():
    """Setup Gemini API with the API key."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY in your .env file")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def parse_analysis_response(response_text):
    """
    Parse the analysis response into a structured format.
    
    Args:
        response_text (str): The raw response text from Gemini
        
    Returns:
        dict: Structured analysis results
    """
    try:
        # Extract overall score
        overall_score_match = re.search(r'Overall ATS Score:\s*(\d+)', response_text)
        overall_score = int(overall_score_match.group(1)) if overall_score_match else 0

        # Extract detailed scores
        scores = {}
        score_pattern = r'- ([^:]+):\s*(\d+)/100'
        for match in re.finditer(score_pattern, response_text):
            category = match.group(1).strip()
            score = int(match.group(2))
            scores[category] = score

        # Extract category analysis
        analysis = {}
        category_pattern = r'(\d+)\. ([^:]+):\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\d+\.|\nKey Strengths:|$)'
        for match in re.finditer(category_pattern, response_text):
            category = match.group(2).strip()
            feedback = match.group(3).strip()
            analysis[category] = feedback

        # Extract strengths
        strengths = []
        strengths_section = re.search(r'Key Strengths:\s*(.*?)(?=\nAreas for Improvement:|$)', response_text, re.DOTALL)
        if strengths_section:
            strengths = [s.strip() for s in re.findall(r'\d+\.\s*([^\n]+)', strengths_section.group(1))]

        # Extract improvements
        improvements = []
        improvements_section = re.search(r'Areas for Improvement:\s*(.*?)(?=\nActionable Recommendations:|$)', response_text, re.DOTALL)
        if improvements_section:
            improvements = [i.strip() for i in re.findall(r'\d+\.\s*([^\n]+)', improvements_section.group(1))]

        # Extract recommendations
        recommendations = []
        recommendations_section = re.search(r'Actionable Recommendations:\s*(.*?)(?=\nNote:|$)', response_text, re.DOTALL)
        if recommendations_section:
            recommendations = [r.strip() for r in re.findall(r'\d+\.\s*([^\n]+)', recommendations_section.group(1))]

        return {
            'ats_score': overall_score,
            'detailed_scores': scores,
            'category_analysis': analysis,
            'strengths': strengths,
            'improvements': improvements,
            'recommendations': recommendations
        }
    except Exception as e:
        print(f"Error parsing response: {str(e)}")
        return {
            'ats_score': 0,
            'detailed_scores': {},
            'category_analysis': {},
            'strengths': [],
            'improvements': [],
            'recommendations': []
        }

def analyze_resume(resume_text):
    """
    Analyze resume using Gemini API and return ATS score and feedback.
    
    Args:
        resume_text (str): The content of the resume
        
    Returns:
        dict: Structured analysis results
    """
    model = setup_gemini()
    
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) analyzer. Analyze this resume and provide a detailed assessment.
    
    Resume content:
    {resume_text}
    
    Please analyze the resume for the following categories and provide scores. Calculate the overall score by taking the weighted average of all categories.
    
    IMPORTANT: For ANY category with a score below 80, you MUST provide at least one specific recommendation based on the actual content of the resume.
    Do not skip recommendations for any category scoring below 80, including ATS Parse Rate, Quantifying Impact, and Style.
    
    1. Content Quality (15% of total score):
       - Relevance of information
       - Clarity of descriptions
       - Professional tone
       - Value proposition
       - Industry-specific terminology
       - Keyword optimization
       - Content relevance to target role
    
    2. ATS Parse Rate (15% of total score):
       - Machine readability
       - File format compatibility
       - Text extraction accuracy
       - Character recognition
       - Special character handling
       - Table and list formatting
       - Header and footer compatibility
    
    3. Quantifying Impact (15% of total score):
       - Use of metrics and numbers
       - Achievement quantification
       - Results-oriented language
       - Performance indicators
       - ROI and cost savings
       - Project impact metrics
       - Team/process improvements
    
    4. Repetition Check (10% of total score):
       - Redundant information
       - Word variety
       - Phrase repetition
       - Content uniqueness
       - Skill overlap
       - Experience redundancy
       - Keyword density
    
    5. Spelling & Grammar (10% of total score):
       - Spelling accuracy
       - Grammar correctness
       - Punctuation
       - Language consistency
       - Technical term accuracy
       - Industry jargon usage
       - Professional terminology
    
    6. Format (10% of total score):
       - Document structure
       - Layout consistency
       - White space usage
       - Visual hierarchy
       - Section alignment
       - Bullet point consistency
       - Margin and spacing
    
    7. Sections (12.5% of total score):
       - Required sections presence
       - Section organization
       - Content distribution
       - Section relevance
       - Chronological order
       - Section completeness
       - Information hierarchy
    
    8. Style (12.5% of total score):
       - Professional appearance
       - Font consistency
       - Design elements
       - Visual appeal
       - Color usage
       - Header formatting
       - Section styling
    
    Additional Analysis:
    1. Skills Analysis:
       - Technical skills identified
       - Soft skills identified
       - Skill relevance to industry
       - Skill presentation format
    
    2. Experience Analysis:
       - Job role progression
       - Industry alignment
       - Achievement patterns
       - Responsibility scope
    
    3. Education Analysis:
       - Degree relevance
       - Certification value
       - Course alignment
       - Academic achievements
    
    4. Keyword Optimization:
       - Industry keywords found
       - Keyword placement
       - Keyword density
       - Missing important keywords
    
    5. Career Progression:
       - Role advancement
       - Responsibility growth
       - Industry movement
       - Career trajectory
    
    For each category with a score below 80, you MUST provide:
    1. A detailed analysis of what's missing or needs improvement
    2. At least one specific recommendation based on the actual content
    3. Concrete examples from the resume to support your recommendations
    4. Specific suggestions for improvement with examples of how to implement them
    
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
    [For each category, provide detailed feedback with specific examples from the resume]
    
    Additional Analysis Results:
    1. Skills Analysis:
       [Detailed analysis of skills with specific examples]
    
    2. Experience Analysis:
       [Detailed analysis of experience with specific examples]
    
    3. Education Analysis:
       [Detailed analysis of education with specific examples]
    
    4. Keyword Optimization:
       [Detailed analysis of keywords with specific examples]
    
    5. Career Progression:
       [Detailed analysis of career progression with specific examples]
    
    Actionable Recommendations:
    [For EACH category with score < 80, provide at least one specific recommendation]
    Format your recommendations as follows:
    
    For [Category Name] (Score: [X]/100):
    1. [Specific recommendation based on actual resume content]
    2. [Another specific recommendation if applicable]
    
    For [Next Category Name] (Score: [Y]/100):
    1. [Specific recommendation based on actual resume content]
    2. [Another specific recommendation if applicable]
    
    [Continue for all categories with scores below 80]
    
    Note: The overall score is calculated as a weighted average of all categories.
    Each recommendation MUST be specific to the content of the resume and provide actionable steps for improvement.
    Do not skip recommendations for any category scoring below 80.
    """
    
    try:
        response = model.generate_content(prompt)
        return parse_analysis_response(response.text)
    except Exception as e:
        print(f"Error analyzing resume: {str(e)}")
        return {
            'ats_score': 0,
            'detailed_scores': {},
            'category_analysis': {},
            'strengths': [],
            'improvements': [],
            'recommendations': []
        }

def get_ats_score(resume_text):
    """
    Get ATS score for the given resume text.
    This function can be imported and used by other modules.
    
    Args:
        resume_text (str): The content of the resume
        
    Returns:
        dict: Structured analysis results including score, feedback, and suggestions
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
    print(json.dumps(result, indent=2)) 