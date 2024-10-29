import streamlit as st

from PIL import Image
import google.generativeai as genai

# Load environment variables


genai.configure(api_key="your api key")

# Load gemini vision model
model = genai.GenerativeModel('gemini-pro-vision')

# get response from gemini pro vision model
def gemini_vision_response(model,prompt,image):
    response = model.generate_content([prompt,image])
    return response.text

# Set page title ans icon




st.title("Chat with Image - Gemini Pro Vision")

image = st.file_uploader("Upload an image",type=["jpg","png","jpeg"])

user_prompt = st.text_input("Enter your query:")



load_image = Image.open(image)




st.image(load_image.resize((400,200)))

caption_response = gemini_vision_response(model,user_prompt,load_image)

st.info(caption_response)