import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
from datetime import datetime
import json
import re
import threading

# Configure Gemini API
genai.configure(api_key='AIzaSyDsp-Q1M2CM548oSCoAAO_UCAaeM2dOdVI')
model = genai.GenerativeModel('gemini-pro')

# Initialize speech recognition
recognizer = sr.Recognizer()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'current_message' not in st.session_state:
    st.session_state.current_message = ""
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'questioning_mode' not in st.session_state:
    st.session_state.questioning_mode = False
if 'memory' not in st.session_state:
    st.session_state.memory = {
        'name': None,
        'preferences': {},
        'context': []
    }

# Updated question flow for comprehensive diet planning
RECIPE_QUESTIONS = [
    "What is your height in centimeters?",
    "What is your weight in kilograms?",
    "What is your age?",
    "What is your goal? (lose weight/gain weight/maintain weight)",
    "Do you have any dietary restrictions or allergies?",
    "What are your favorite foods or cuisines?",
    "How many meals do you prefer per day? (2-6)",
    "Do you prefer vegetarian, non-vegetarian, or both types of food?",
    "How much time can you spend on cooking per day?"
]

def calculate_bmi(height_cm, weight_kg):
    try:
        height_m = float(height_cm) / 100
        weight = float(weight_kg)
        bmi = weight / (height_m * height_m)
        return round(bmi, 2)
    except:
        return None

def check_diet_safety(height, weight, age, goal):
    """Check if the proposed diet goal is safe for the user"""
    try:
        bmi = calculate_bmi(height, weight)
        if bmi is None:
            return False, "Unable to calculate BMI with provided measurements."
        
        if bmi >= 30:  # Obese
            if goal.lower() == "gain weight":
                return False, "Based on your BMI, gaining weight might be unsafe. Consider a weight loss or maintenance plan instead."
        elif bmi < 18.5:  # Underweight
            if goal.lower() == "lose weight":
                return False, "Based on your BMI, losing weight might be unsafe. Consider a weight gain or maintenance plan instead."
        return True, "Your goal appears appropriate for your current health status."
    except:
        return False, "Unable to assess diet safety with provided information."

def create_tts_engine():
    engine = pyttsx3.init()
    return engine

def clean_text_for_speech(text):
    """Clean text to contain only alphanumeric characters and basic punctuation"""
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s.,?!]', ' ', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r'\s+([.,?!])', r'\1', cleaned_text)
    return cleaned_text.strip()

def text_to_speech(text):
    """Convert text to speech using only alphanumeric characters"""
    try:
        engine = create_tts_engine()
        cleaned_text = clean_text_for_speech(text)
        engine.say(cleaned_text)
        engine.runAndWait()
        engine.stop()
        del engine
    except Exception as e:
        st.error(f"Speech Error: {str(e)}")

def speak_in_thread(text):
    """Run text-to-speech in a separate thread"""
    thread = threading.Thread(target=text_to_speech, args=(text,))
    thread.start()

def update_memory(user_input, bot_response):
    """Update bot's memory based on conversation"""
    name_match = re.search(r"my name is (\w+)", user_input.lower())
    if name_match and not st.session_state.memory['name']:
        st.session_state.memory['name'] = name_match.group(1)
    
    st.session_state.memory['context'].append({
        'user_input': user_input,
        'bot_response': bot_response,
        'timestamp': str(datetime.now())
    })
    
    if len(st.session_state.memory['context']) > 10:
        st.session_state.memory['context'] = st.session_state.memory['context'][-10:]

def get_memory_context():
    """Get relevant context from memory"""
    context = ""
    if st.session_state.memory['name']:
        context += f"The user's name is {st.session_state.memory['name']}. "
    
    if st.session_state.memory['context']:
        context += "Recent conversations:\n"
        for conv in st.session_state.memory['context'][-3:]:
            context += f"User: {conv['user_input']}\nAssistant: {conv['bot_response']}\n"
    
    return context

def get_next_question():
    """Get the next question based on current state"""
    if st.session_state.questioning_mode and st.session_state.current_question_index < len(RECIPE_QUESTIONS):
        return RECIPE_QUESTIONS[st.session_state.current_question_index]
    return None

def process_user_input(user_input):
    """Process user input and determine response"""
    if any(keyword in user_input.lower() for keyword in ["diet", "meal", "food", "eat", "nutrition", "healthy recipes"]):
        st.session_state.questioning_mode = True
        st.session_state.current_question_index = 0
        response = RECIPE_QUESTIONS[0]
        update_memory(user_input, response)
        return response
    
    if st.session_state.questioning_mode:
        # Store the answer
        st.session_state.user_info[f"recipe_q_{st.session_state.current_question_index}"] = user_input
        
        # Check diet safety after collecting necessary information
        if st.session_state.current_question_index == 3:  # After collecting goal
            height = float(st.session_state.user_info.get('recipe_q_0', 0))
            weight = float(st.session_state.user_info.get('recipe_q_1', 0))
            age = float(st.session_state.user_info.get('recipe_q_2', 0))
            goal = user_input
            
            is_safe, message = check_diet_safety(height, weight, age, goal)
            if not is_safe:
                st.session_state.questioning_mode = False
                st.session_state.current_question_index = 0
                return f"⚠️ {message} Please consult with a healthcare provider for personalized advice."
        
        # Move to next question
        st.session_state.current_question_index += 1
        
        if st.session_state.current_question_index < len(RECIPE_QUESTIONS):
            response = RECIPE_QUESTIONS[st.session_state.current_question_index]
            update_memory(user_input, response)
            return response
        else:
            st.session_state.questioning_mode = False
            response = generate_recipe_recommendations()
            update_memory(user_input, response)
            return response
    
    response = get_bot_response(user_input)
    update_memory(user_input, response)
    return response

def generate_recipe_recommendations():
    """Generate diet plan based on collected information"""
    try:
        height = float(st.session_state.user_info.get('recipe_q_0', 0))
        weight = float(st.session_state.user_info.get('recipe_q_1', 0))
        bmi = calculate_bmi(height, weight)
        
        context = "Based on the user's information:\n"
        context += f"BMI: {bmi}\n"
        
        for i, answer in enumerate(st.session_state.user_info.values()):
            context += f"- Answer to '{RECIPE_QUESTIONS[i]}': {answer}\n"
        
        memory_context = get_memory_context()
        prompt = f"""{memory_context}\n{context}
Based on this information, provide:
1. BMI Category and what it means
2. Daily caloric needs
3. A detailed 7-day diet plan with 3 meals and 2 snacks that:
   - Matches their food preferences
   - Supports their weight goal
   - Includes portion sizes
   - Considers their time constraints
Please format it clearly and make it easy to follow."""
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return "I apologize, but I'm having trouble generating recommendations right now. Could you please try again?"
            
    except Exception as e:
        return "There was an error processing your information. Please make sure you provided valid numbers for height and weight."

def get_bot_response(user_input):
    """Get response from Gemini API for general queries"""
    memory_context = get_memory_context()
    context = f"""You are MAX, a professional diet planning assistant. Act as a certified nutritionist who:
- Provides evidence-based dietary advice
- Creates personalized meal plans
- Calculates and explains BMI
- Offers practical nutrition guidance
Keep responses focused on nutrition and diet advice. Be direct and concise.

Memory Context:\n{memory_context}"""
    prompt = f"{context}\nUser: {user_input}\nMAX:"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "I apologize, but I'm having trouble generating a response right now. Could you please try again?"

def handle_input(user_input):
    """Handle user input and update chat"""
    if user_input:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        bot_response = process_user_input(user_input)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": bot_response
        })
        
        speak_in_thread(bot_response)
        
        st.session_state.current_message = ""
        
        st.rerun()

def show_prescription_reader():
    st.title("Prescription Reader")
    uploaded_file = st.file_uploader("Upload your prescription", type=['png', 'jpg', 'jpeg', 'pdf'])
    if uploaded_file is not None:
        st.write("Prescription uploaded successfully! (OCR functionality to be implemented)")

def show_diet_assistant():
    st.title("MAX - Your Personal Diet Planning Assistant")
    st.write("I can help you create a personalized diet plan. You can type or speak!")

    # Display chat history using chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        handle_input(user_input)

    # Voice input button
    if st.sidebar.button("🎤 Voice Input"):
        with sr.Microphone() as source:
            st.sidebar.write("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5)
                user_input = recognizer.recognize_google(audio)
                handle_input(user_input)
            except Exception as e:
                st.sidebar.error("Could not understand audio")

    # Clear chat button
    if st.sidebar.button("Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.user_info = {}
        st.session_state.current_message = ""
        st.session_state.current_question_index = 0
        st.session_state.questioning_mode = False
        st.session_state.memory = {'name': None, 'preferences': {}, 'context': []}
        st.rerun()

# Main app
def main():
    st.set_page_config(page_title="Health Assistant", layout="wide")
    
    # Page selection in sidebar
    page = st.sidebar.selectbox("Choose a feature", ["Diet Assistant", "Prescription Reader"])
    with st.sidebar:
        st.title("MAX - The Assistant")
        st.markdown("You can ask MAX anything here.")
        st.markdown("### About")
        st.markdown("MAX is your friendly assistant to help with student tasks!")

    if page == "Diet Assistant":
        show_diet_assistant()
    else:
        show_prescription_reader()

if __name__ == "__main__":
    main()