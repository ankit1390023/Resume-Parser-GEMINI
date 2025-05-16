import google.generativeai as genai
import yaml
import json
import re
import fitz  # PyMuPDF for extracting links from PDF
import os

# Configuration loading
def load_config(config_path=None):
    if config_path is None:
        config_path = "config.yaml"
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
        
    with open(config_path) as file:
        data = yaml.load(file, Loader=yaml.SafeLoader)
        if 'GEMINI_API_KEY' not in data:
            raise KeyError("GEMINI_API_KEY not found in config file")
        return data['GEMINI_API_KEY']

# Text cleaning and JSON parsing functions
def clean_json_string(text):
    # Remove markdown code block formatting
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    return text.strip()

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with improved error handling and text processing"""
    try:
        print(f"Attempting to open PDF at: {pdf_path}")
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        print("Opening PDF document...")
        doc = fitz.open(pdf_path)
        print(f"PDF opened successfully. Page count: {doc.page_count}")
        
        if doc.page_count == 0:
            raise ValueError("PDF file is empty or corrupted")
            
        text = ""
        for page_num, page in enumerate(doc):
            print(f"Processing page {page_num + 1}...")
            # Get text with layout preservation
            page_text = page.get_text("text")
            if page_text:
                # Clean the text
                page_text = page_text.strip()
                # Remove multiple newlines
                page_text = re.sub(r'\n\s*\n', '\n', page_text)
                # Remove multiple spaces
                page_text = re.sub(r'\s+', ' ', page_text)
                text += page_text + "\n"
                print(f"Extracted {len(page_text)} characters from page {page_num + 1}")
            else:
                print(f"Warning: No text found on page {page_num + 1}")
                
        doc.close()
        
        if not text.strip():
            raise ValueError("No text content found in PDF. The file might be scanned or contain only images.")
            
        print(f"Successfully extracted {len(text)} characters total")
        return text
        
    except fitz.FileDataError as e:
        print(f"PDF file is corrupted or invalid: {str(e)}")
        raise ValueError("The PDF file appears to be corrupted or invalid. Please ensure it's a valid PDF file.")
    except fitz.EmptyFileError as e:
        print(f"PDF file is empty: {str(e)}")
        raise ValueError("The PDF file is empty. Please upload a non-empty PDF file.")
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_links_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        links = {}
        
        # Extract hyperlinks from PDF
        for page_num, page in enumerate(doc):
            for link in page.get_links():
                if "uri" in link:
                    url = link["uri"]
                    # Try to categorize the link
                    if "github.com" in url.lower():
                        links["github"] = url
                    elif "linkedin.com" in url.lower():
                        links["linkedin"] = url
                    elif "leetcode.com" in url.lower():
                        links["leetcode"] = url
                    elif "geeksforgeeks.org" in url.lower() or "gfg" in url.lower():
                        links["gfg"] = url
                    elif "portfolio" in url.lower() or "personal" in url.lower():
                        links["portfolio"] = url
                    else:
                        # Store project links
                        for project in ["workify", "school management", "food delivery"]:
                            if project.lower().replace(" ", "") in url.lower():
                                if project not in links:
                                    links[project] = {}
                                
                                if "github.com" in url.lower():
                                    links[project]["github"] = url
                                else:
                                    links[project]["live"] = url
        
        return links
    except Exception as e:
        print(f"Error extracting links from PDF: {str(e)}")
        return {}

def extract_field_info(resume_text):
    """Extract basic fields before sending to AI to ensure accurate information"""
    info = {}
    
    # Split text into lines and clean them
    lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
    
    # Extract name (usually first line)
    if lines:
        info["full_name"] = lines[0].strip()
    
    # Extract location (usually second line)
    if len(lines) > 1:
        info["location"] = lines[1].strip()
    
    # Extract contact info
    for line in lines:
        # Extract phone number
        phone_match = re.search(r'(\+\d{1,4}-\d{10})', line)
        if phone_match:
            info["phone"] = phone_match.group(1)
        
        # Extract email
        email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line)
        if email_match:
            info["email"] = email_match.group(1)
        
        # Extract professional links
        if '|' in line:
            links = line.split('|')
            info["professional_links"] = {}
            for link in links:
                link = link.strip()
                if 'github' in link.lower():
                    info["professional_links"]["github"] = link
                elif 'linkedin' in link.lower():
                    info["professional_links"]["linkedin"] = link
                elif 'leetcode' in link.lower():
                    info["professional_links"]["leetcode"] = link
                elif 'portfolio' in link.lower():
                    info["professional_links"]["portfolio"] = link
                elif 'gfg' in link.lower():
                    info["professional_links"]["gfg"] = link
    
    return info

def parse_resume(resume_text, extracted_links=None, basic_info=None):
    """Enhanced resume parsing function with improved prompt"""
    
    # Create a detailed prompt with specific instructions
    prompt = '''
    You are an AI expert in resume parsing. Extract the following information from the resume text and format it as a structured JSON object. Your task is to identify and extract all relevant information accurately.

    Extract the following fields:

    {
        "personal_info": {
            "full_name": "",
            "location": "",
            "contact": {
                "phone": "",
                "email": "",
                "professional_links": {
                    "github": "",
                    "leetcode": "",
                    "linkedin": "",
                    "gfg": "",
                    "portfolio": "",
                    "codechef": "",
                    "hackerrank": "",
                    "website": ""
                }
            }
        },
        "education": [
            {
                "degree": "",
                "institute": "",
                "board_university": "",
                "score": "",
                "year": ""
            }
        ],
        "skills": {
            "programming_languages": [],
            "frontend_technologies": [],
            "backend_technologies": [],
            "version_control_deployment": [],
            "computer_science_fundamentals": []
        },
        "experience": [
            {
                "title": "",
                "company": "",
                "location": "",
                "duration": "",
                "achievements": []
            }
        ],
        "projects": [
            {
                "name": "",
                "technologies": [],
                "links": {
                    "live_site": "",
                    "github_repo": ""
                },
                "achievements": []
            }
        ],
        "achievements": [],
        "positions_of_responsibility": []
    }

    IMPORTANT GUIDELINES:
    1. Extract only factual information present in the resume, don't invent details
    2. For sections that are not found, use null or empty arrays/lists
    3. Return ONLY the JSON object without any additional text or markdown formatting
    4. Pay special attention to extracting all links and URLs correctly
    5. Format the JSON properly with correct nesting, arrays, and syntax
    6. For the education section, match each degree with its institute, board/university, score, and year
    7. For projects, extract complete descriptions and match with technologies and links
    8. For experience entries, extract all details including company, location, duration, and achievements
    9. Extract full achievements and positions of responsibility as complete sentences
    10. Handle bullet points (•) properly in achievements and responsibilities
    11. Ensure proper spacing and formatting in extracted text
    12. Maintain the original order of information as it appears in the resume
    '''

    # If we have pre-extracted info, include it in the prompt
    if basic_info:
        prompt += f"\n\nPRE-EXTRACTED INFORMATION:\n"
        for key, value in basic_info.items():
            prompt += f"{key}: {value}\n"
    
    # If we have extracted links, include them in the prompt
    if extracted_links:
        prompt += f"\n\nEXTRACTED LINKS FROM PDF:\n"
        for key, value in extracted_links.items():
            if isinstance(value, dict):
                prompt += f"{key}: {json.dumps(value)}\n"
            else:
                prompt += f"{key}: {value}\n"

    # Add the resume text to the prompt
    prompt += f"\n\nRESUME TEXT:\n{resume_text}"

    return prompt

def ats_extractor(resume_path):
    """Main function to extract resume information"""
    try:
        print(f"\nStarting resume extraction for: {resume_path}")
        
        # Load configuration
        print("Loading configuration...")
        api_key = load_config()
        print("Configuration loaded successfully")
        
        # Extract text from PDF
        print("\nExtracting text from PDF...")
        try:
            resume_text = extract_text_from_pdf(resume_path)
        except ValueError as e:
            return json.dumps({
                "error": "Failed to extract text from PDF",
                "details": str(e),
                "path": resume_path
            })
        
        print(f"Successfully extracted {len(resume_text)} characters from PDF")
        
        # Extract links from PDF
        print("\nExtracting links from PDF...")
        extracted_links = extract_links_from_pdf(resume_path)
        print(f"Found {len(extracted_links)} links in PDF")
        
        # Extract basic information
        print("\nExtracting basic information...")
        basic_info = extract_field_info(resume_text)
        print(f"Extracted basic info: {basic_info}")
        
        # Create the prompt
        print("\nCreating prompt for AI...")
        prompt = parse_resume(resume_text, extracted_links, basic_info)
        
        # Configure Gemini
        print("\nConfiguring Gemini AI...")
        genai.configure(api_key=api_key)
        
        generation_config = {
            "temperature": 0.1,  # Reduced temperature for more consistent output
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
        }

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]

        # Initialize the model
        print("Initializing Gemini model...")
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Generate the response
        print("Generating AI response...")
        response = model.generate_content(prompt)
        data = response.text.strip()
        print("AI response generated successfully")

        # Clean and parse the JSON
        print("\nCleaning and parsing JSON...")
        cleaned_data = clean_json_string(data)

        # Further process the JSON to enhance it with the extracted links
        try:
            parsed_json = json.loads(cleaned_data)
            print("JSON parsed successfully")
            
            # Enhance with extracted links if not already populated
            if extracted_links:
                print("Enhancing JSON with extracted links...")
                # Update professional links
                for link_type, url in extracted_links.items():
                    if link_type in ["github", "linkedin", "leetcode", "gfg", "portfolio"]:
                        if not parsed_json["personal_info"]["contact"]["professional_links"][link_type]:
                            parsed_json["personal_info"]["contact"]["professional_links"][link_type] = url
                
                # Update project links
                for project_name, project_links in extracted_links.items():
                    if isinstance(project_links, dict):
                        # Find matching project in parsed data
                        for i, project in enumerate(parsed_json["projects"]):
                            if project_name.lower() in project["name"].lower():
                                if "github" in project_links and not project["links"]["github_repo"]:
                                    parsed_json["projects"][i]["links"]["github_repo"] = project_links["github"]
                                if "live" in project_links and not project["links"]["live_site"]:
                                    parsed_json["projects"][i]["links"]["live_site"] = project_links["live"]
            
            print("JSON processing completed successfully")
            return json.dumps(parsed_json, indent=2)
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            return json.dumps({
                "error": "Failed to parse resume data",
                "details": str(e),
                "raw_response": cleaned_data
            })
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return json.dumps({
            "error": "Failed to process resume",
            "details": str(e)
        })

# Example usage
if __name__ == "__main__":
    resume_path = "Ankit_CV.pdf"  # Path to your resume PDF
    parsed_data = ats_extractor(resume_path)
    print(parsed_data)
    
    # Optionally save to file
    with open("parsed_resume.json", "w") as f:
        f.write(parsed_data)
