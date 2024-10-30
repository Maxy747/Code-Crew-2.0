import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3

# Configure Gemini API
genai.configure(api_key='YOUR_API_KEY_HERE')
model = genai.GenerativeModel('gemini-pro')

# Initialize speech recognition
recognizer = sr.Recognizer()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'asking_questions' not in st.session_state:
    st.session_state.asking_questions = False
if 'sound_enabled' not in st.session_state:
    st.session_state.sound_enabled = True

# Basic questions for diet planning
QUESTIONS = [
    "What is your height (cm)?",
    "What is your weight (kg)?",
    "What is your goal? (lose/gain/maintain weight)",
    "Any dietary restrictions?",
    "How many meals per day? (2-6)"
]

def calculate_bmi(height_cm, weight_kg):
    try:
        height_m = float(height_cm) / 100
        return round(float(weight_kg) / (height_m * height_m), 2)
    except:
        return None

def speak(text):
    if st.session_state.sound_enabled:
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            st.error(f"Speech Error: {str(e)}")

def get_bot_response(user_input):
    try:
        prompt = f"You are a diet planning assistant. User message: {user_input}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"I'm having trouble responding. Error: {str(e)}"

def process_input(user_input):
    if "diet" in user_input.lower():
        st.session_state.asking_questions = True
        return QUESTIONS[0]
    
    if st.session_state.asking_questions:
        st.session_state.user_info[f"q_{st.session_state.current_question}"] = user_input
        st.session_state.current_question += 1
        
        if st.session_state.current_question < len(QUESTIONS):
            return QUESTIONS[st.session_state.current_question]
        else:
            st.session_state.asking_questions = False
            return generate_diet_plan()
    
    return get_bot_response(user_input)

def generate_diet_plan():
    try:
        height = st.session_state.user_info.get('q_0')
        weight = st.session_state.user_info.get('q_1')
        bmi = calculate_bmi(height, weight)
        
        prompt = f"""Create a diet plan based on:
        - BMI: {bmi}
        - Goal: {st.session_state.user_info.get('q_2')}
        - Restrictions: {st.session_state.user_info.get('q_3')}
        - Meals per day: {st.session_state.user_info.get('q_4')}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating diet plan: {str(e)}"

def main():
    st.set_page_config(page_title="Diet Assistant", layout="wide")
    
    # Sidebar
    with st.sidebar:
        st.title("Diet Planning Assistant")
        st.write("You can ask anything related to diet here.")
        
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.user_info = {}
            st.session_state.current_question = 0
            st.session_state.asking_questions = False
            st.rerun()
            
        # Sound toggle
        st.session_state.sound_enabled = st.toggle("Enable Sound", st.session_state.sound_enabled)
    
    # Main chat area
    st.title("Your Personal Diet Assistant")
    st.write("I can help you create a personalized diet plan. Just start by asking about diet!")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # User input
    user_input = st.chat_input("Type your message...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        bot_response = process_input(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
        speak(bot_response)
        st.rerun()

if __name__ == "__main__":
    main()