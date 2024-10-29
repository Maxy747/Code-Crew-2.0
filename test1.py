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

# ... (other functions remain the same)

def handle_input():
    """Handle user input and update chat"""
    if st.session_state.current_message:
        # Add user message to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": st.session_state.current_message
        })
        
        # Process the input and get response
        bot_response = process_user_input(st.session_state.current_message)
        
        # Add bot response to chat history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": bot_response
        })
        
        # Handle speech in a separate thread
        speak_in_thread(bot_response)
        
        # Clear current message
        st.session_state.current_message = ""

# Streamlit UI
st.title("MAX - Your Personal Diet Planning Assistant")
st.write("I can help you create a personalized diet plan. You can type or speak!")

# Create a container for chat history
chat_container = st.container()

# Create a container for input
input_container = st.container()

with input_container:
    # Create columns for input field and buttons
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Text input with Enter key handling
        st.session_state.current_message = st.text_input(
            "Your message",
            key="user_input",
            on_change=handle_input
        )
    
    with col2:
        if st.button("Send"):
            handle_input()
    
    with col3:
        if st.button("🎤 Speak"):
            with sr.Microphone() as source:
                st.write("Listening...")
                try:
                    audio = recognizer.listen(source, timeout=5)
                    st.session_state.current_message = recognizer.recognize_google(audio)
                    handle_input()
                except Exception as e:
                    st.error("Could not understand you, could you repeat?")

# Display chat history in the container
with chat_container:
    st.write("Chat History:")
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.write("You:", message["content"])
            st.write("---")
        else:
            st.markdown(f"**MAX:** {message['content']}")
            st.write("---")

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.session_state.user_info = {}
    st.session_state.current_message = ""
    st.session_state.current_question_index = 0
    st.session_state.questioning_mode = False
    st.session_state.memory = {'name': None, 'preferences': {}, 'context': []}