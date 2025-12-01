import re 
import google.generativeai as genai
from configparser import ConfigParser, ExtendedInterpolation
import os 

def get_similar_gift_ideas(gift_name: str, num_ideas: int = 2):
    """
    Returns short, thematically similar gift ideas.
    """
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up one level to SantasHelpr folder
    config_path = os.path.join(script_dir, '..', 'config.ini')


    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(config_path)

    GEMINI = config['gemini']['GEMINI_API_KEY'].strip()

    genai.configure(api_key=GEMINI)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"List {num_ideas} toys or gifts similar to '{gift_name}', separated by commas. Only return names."
    
    # Generate response
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.8,
            top_p=0.9,
            max_output_tokens=60,
        )
    )
    
    text = response.text
    
    # Remove unwanted labels or formatting artifacts
    text = re.sub(r"(?i)\b(solution|answer|response|output)\s*[:\-–]*", "", text)
    text = text.replace("**", "").strip()
    
    # Extract clean list
    ideas = re.split(r"[,;\n]+", text)
    ideas = [i.strip(" -*") for i in ideas if i.strip()]
    
    return ideas[:num_ideas] if ideas else ["(no ideas found)"]


def main():
    print(get_similar_gift_ideas("power rangers"))

if __name__ == "__main__":
    main()