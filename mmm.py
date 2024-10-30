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
if 'sound_enabled' not in st.session_state:
    st.session_state.sound_enabled = True
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False

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
    if st.session_state.sound_enabled:
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
    """Handle user input and update chat history"""
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
        st.rerun()

def show_prescription_reader():
    st.title("Prescription Reader")
    uploaded_file = st.file_uploader("Upload your prescription", type=['png', 'jpg', 'jpeg', 'pdf'])
    if uploaded_file is not None:
        st.write("Prescription uploaded successfully! (OCR functionality to be implemented)")

def show_diet_assistant():
    st.title("MAX - Your Personal Diet Planning Assistant")
    st.write("I can help you create a personalized diet plan. You can type or speak!")

    # Add custom CSS for thought bubble chat layout
    st.markdown("""
        <style>
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            scroll-behavior: smooth;
        }
         /* Profile picture styling */
        .profile-pic {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-size: cover;
            background-position: center;
            flex-shrink: 0;
        }
        
        .user-pic {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23EA0103' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E");
        }
        
        .assistant-pic {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%234CAF50' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM7.07 18.28c.43-.9 3.05-1.78 4.93-1.78s4.51.88 4.93 1.78C15.57 19.36 13.86 20 12 20s-3.57-.64-4.93-1.72zm11.29-1.45c-1.43-1.74-4.9-2.33-6.36-2.33s-4.93.59-6.36 2.33C4.62 15.49 4 13.82 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8c0 1.82-.62 3.49-1.64 4.83zM12 6c-1.94 0-3.5 1.56-3.5 3.5S10.06 13 12 13s3.5-1.56 3.5-3.5S13.94 6 12 6z'/%3E%3C/svg%3E");
        }
        
        /* Thought bubble styling for user messages */
        .user-message {
            display: flex;
            justify-content: flex-end;
            margin: 1rem 0;
        }
        .user-bubble {
            background-color: #EA0103;
            color: white;
            border-radius: 20px 20px 0 20px;
            padding: 1rem;
            max-width: 70%;
            position: relative;
            margin-right: 15px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        }
        .user-bubble::after {
            content: '';
            position: absolute;
            right: -15px;
            bottom: 0;
            width: 15px;
            height: 15px;
            background-color: #EA0103;
            border-radius: 0 0 0 15px;
        }
        
        /* Thought bubble styling for assistant messages */
        .assistant-message {
            display: flex;
            justify-content: flex-start;
            margin: 1rem 0;
        }
        .assistant-bubble {
            background-color: #f5f5f5;
            border-radius: 20px 20px 20px 0;
            padding: 1rem;
            max-width: 70%;
            position: relative;
            margin-left: 15px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        .assistant-bubble::after {
            content: '';
            position: absolute;
            left: -15px;
            bottom: 0;
            width: 15px;
            height: 15px;
            background-color: #f5f5f5;
            border-radius: 0 0 15px 0;
        }
        
        /* Input container styling */
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: white;
            padding: 1rem;
            border-top: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
        }
        
        /* Control buttons styling */
        .control-button {
            background-color: #f0f2f6;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            border: none;
            transition: all 0.3s ease;
        }
        
        .control-button:hover {
            background-color: #e0e0e0;
        }
        
        .mic-button.active {
            background-color: #EA0103;
            color: white;
        }
        
        /* Stickied input area */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:has(.input-container) {
            position: sticky;
            bottom: 0;
            background: white;
            z-index: 1000;
        }
        
        /* Hide Streamlit branding */
        #MainMenu, footer {display: none;}
        </style>
    """, unsafe_allow_html=True)

    # Create chat container
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="user-message">
                        <div class="user-bubble">{message["content"]}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="assistant-message">
                        <div class="assistant-bubble">{message["content"]}</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Create input container
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # Create columns for input elements
    col1, col2, col3 = st.columns([10, 1, 1])

    with col1:
        user_input = st.chat_input("Type your message here...", key="chat_input")

    with col2:
        mic_class = "control-button mic-button" + (" active" if st.session_state.is_listening else "")
        if st.button("🎤", key="mic_button", help="Click to start/stop listening", type="secondary"):
            st.session_state.is_listening = not st.session_state.is_listening
            
            if st.session_state.is_listening:
                # Start listening in a separate thread
                def listen_for_speech():
                    with sr.Microphone() as source:
                        st.write("Listening...")
                        try:
                            while st.session_state.is_listening:
                                audio = recognizer.listen(source, timeout=5)
                                user_input = recognizer.recognize_google(audio)
                                if user_input:
                                    handle_input(user_input)
                                    break  # Break after processing one input
                        except Exception as e:
                            st.error("Could not understand audio")
                        finally:
                            st.session_state.is_listening = False
                            st.rerun()
                
                thread = threading.Thread(target=listen_for_speech)
                thread.start()
            else:
                st.write("Stopped listening.")

    with col3:
        sound_icon = "🔊" if st.session_state.sound_enabled else "🔇"
        if st.button(sound_icon, key="sound_button", type="secondary"):
            st.session_state.sound_enabled = not st.session_state.sound_enabled

    st.markdown('</div>', unsafe_allow_html=True)

    # Handle input processing
    if user_input:
        handle_input(user_input)

def main():
    st.set_page_config(page_title="Health Assistant", layout="wide")
    
    # Sidebar content
    with st.sidebar:
        st.title("MAX - The Personal Diet Planner")
        st.markdown("You can ask MAX anything related to diet here.")
        st.markdown("### About")
        
        # Page selection
        page = st.selectbox("Choose a feature", ["Diet Assistant", "Prescription Reader"])
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.user_info = {}
            st.session_state.current_message = ""
            st.session_state.current_question_index = 0
            st.session_state.questioning_mode = False
            st.session_state.memory = {'name': None, 'preferences': {}, 'context': []}
            st.rerun()

    if page == "Diet Assistant":
        show_diet_assistant()
    else:
        show_prescription_reader()

if __name__ == "__main__":
    main()