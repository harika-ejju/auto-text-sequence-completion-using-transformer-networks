import streamlit as st
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(page_title="TextNext", layout="centered")

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.environ.get("GEMINI_API_KEY")

# Fallback to hardcoded key if environment variable is not set
# This is not recommended for production use
if not api_key:
    api_key = "AIzaSyDPFOSdoAXf6FFkFQag9xywTwtYu2apImM"
    st.warning("⚠️ Using default API key. For security, set the GEMINI_API_KEY environment variable.")

# Configure the Gemini API
# Configure the Gemini API
genai.configure(api_key=api_key)

# Use Gemini-Pro model
try:
    model = genai.GenerativeModel("gemini-pro")
except Exception as e:
    st.error(f"Failed to initialize Gemini model: {str(e)}")
    # Try the new model name format as fallback
    try:
        model = genai.GenerativeModel("models/gemini-1.0-pro")
        st.success("Successfully connected using alternative model name")
    except Exception as e:
        st.error(f"Failed to initialize alternative model: {str(e)}")
        model = None
# Apply custom styles
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(145deg, #3b4d3b, #001f3f);
        color: #ffffff;
    }
    .stTextInput > div > div > input {
        background-color: #f0f4f8;
        color: #1a1a1a;
        border-radius: 0.5rem;
        border: 2px solid #3b4d3b;
        padding: 10px;
        font-size: 1rem;
    }
    .next-word {
        background-color: rgba(59, 77, 59, 0.2);
        padding: 15px;
        border-radius: 0.5rem;
        font-size: 1.2rem;
        margin-top: 20px;
    }
    .next-word span {
        font-weight: bold;
        color: #4caf50;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 3px 8px;
        border-radius: 4px;
    }
    .stButton button {
        background-color: #4caf50;
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 10px 20px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.title("TextNext: AI Word Prediction")
st.subheader("Enter a sentence and see what comes next!")

# User input field
user_input = st.text_input("Your sentence", max_chars=100)

def sanitize_input(text):
    """Remove potentially harmful characters and normalize whitespace"""
    if not text:
        return ""
    # Remove any HTML/script tags that could be malicious
    sanitized = re.sub(r'<[^>]*>', '', text)
    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())
    return sanitized

def validate_input(text):
    """Check if the input is valid for prediction"""
    if not text or text.strip() == "":
        return False, "Please enter some text for prediction."
    if len(text.strip()) < 3:
        return False, "Input is too short. Please enter a longer phrase."
    return True, ""

def predict_next_word(text):
    """Predict the next word using the Gemini API."""
    prompt = f"""
    Based on the following input text, predict ONLY the next single word that would most naturally follow.
    Return just the single word without any punctuation, explanation, or additional context.
    
    Input text: "{text}"
    
    Next word:
    """
    
    # Check if model was initialized properly
    if model is None:
        return "⚠️ Model not available"
        
    try:
        # Generate response with safety settings
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 5,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Generate the response
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Extract the first word from the response
        if response and hasattr(response, 'text') and response.text:
            words = re.findall(r'\b\w+\b', response.text.strip())
            return words[0] if words else "..."
        else:
            return "No prediction available"
            
    except Exception as e:
        error_message = str(e).lower()
        
        if "blocked" in error_message or "safety" in error_message:
            return "⚠️ Content blocked due to safety concerns"
        elif "stopped" in error_message:
            return "⚠️ Generation stopped unexpectedly"
        elif "not found" in error_message or "model" in error_message:
            return "⚠️ Model not available"
        elif "api key" in error_message or "authentication" in error_message:
            return "⚠️ API key error"
        elif "quota" in error_message or "limit" in error_message:
            return "⚠️ API quota exceeded"
        else:
            st.error(f"Error: {str(e)}")
            return "⚠️ Error in prediction"

# Process user input
if user_input:
    # Sanitize the input
    clean_input = sanitize_input(user_input)
    
    # Validate the input
    valid, message = validate_input(clean_input)
    
    if valid:
        # Show loading spinner while predicting
        with st.spinner("Predicting next word..."):
            next_word = predict_next_word(clean_input)
        
        # Display the prediction
        st.markdown(f'<p class="next-word">🔮 Predicted Next Word: <span>{next_word}</span></p>', unsafe_allow_html=True)
        
        # Display the complete sentence with the prediction (only for successful predictions)
        if next_word and next_word not in ["...", "No prediction available", 
                                         "⚠️ Content blocked due to safety concerns",
                                         "⚠️ Generation stopped unexpectedly", 
                                         "⚠️ Error in prediction"]:
            st.success(f"Complete phrase: {clean_input} **{next_word}**...")
    else:
        # Show validation error
        st.warning(message)

# Add footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and Google's Gemini API")

# Add instructions
with st.expander("How to use"):
    st.write("""
    1. Type your sentence in the text box above
    2. The AI will predict the next word that should follow
    3. Try different sentence structures to see how predictions change
    4. For best results, use complete phrases that naturally lead to a next word
    """)

# Add error notification for API key issues
if not os.environ.get("GEMINI_API_KEY"):
    st.sidebar.error("""
    ⚠️ For production use:
    1. Create a .env file in the project directory
    2. Add: GEMINI_API_KEY=your_actual_api_key
    3. Restart the application
    """)
