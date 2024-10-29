import os
import streamlit as st
from transformers import pipeline
from langdetect import detect
import google.generativeai as gen_ai

# Load API key from environment variable for security
GOOGLE_API_KEY = ("AIzaSyBiBNeryv264Z7EV61QwncsoKk_6T2i-tE")

# Check if the API key is available
if not GOOGLE_API_KEY:
    st.error("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

# Initialize NLP pipeline for text classification
nlp_classifier = pipeline("zero-shot-classification")

st.set_page_config(
    page_title="Chat with Gemini-Pro!",
    page_icon=":brain:",  # Favicon emoji
)

# Function to translate roles between Gemini-Pro and Streamlit terminology
def translate_role_for_streamlit(user_role):
    if user_role == "model":
        return "assistant"
    else:
        return user_role

# Initialize chat session in Streamlit if not already present
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# Function to determine if the question is relevant to fitness or nutrition
def is_relevant_question(question):
    # Detect the language of the question
    language = detect(question)
    if language == "en":
        # Classify the question using zero-shot classification
        classification = nlp_classifier(question, model=["fitness", "nutrition"], multi_label=True)
        relevant_labels = [label for label, score in zip(classification["labels"], classification["scores"]) if score > 0.5]
        return any(label.lower() in ["fitness", "nutrition"] for label in relevant_labels)
    else:
        return False

# Display the chatbot's title on the page
st.title("Gym BRO")

# Display the chat history
for message in st.session_state.chat_session.history:
    with st.chat_message(translate_role_for_streamlit(message.role)):
        st.markdown(message.parts[0].text)

# Input field for user's message
user_prompt = st.text_input("Ask Gym BRO about fitness or nutrition...")

if user_prompt:
    # Check if the question is relevant
    if is_relevant_question(user_prompt):
        # Process relevant question
        st.write("Processing relevant question...")
    else:
        # Respond with a standard message for irrelevant questions
        st.write("I'm here to help with fitness and nutrition questions. Please ask me about those topics!")
