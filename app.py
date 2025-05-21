import os
import sqlite3
import datetime

import streamlit as st
import google.generativeai as genai

from dotenv import load_dotenv
from typing import Any, Dict, List

from db_ops import get_recent_conversations, init_db, start_conversations_summary, store_message

# Load enviorment variables from .env file
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini Model
model = genai.GenerativeModel("gemini-2.0-flash")

def chat_with_gemini(prompt:str, chat_history:List[Dict[str, str]]) -> str:
    try:
        # Format message for gemini
        messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append({"role": "user", "parts": [msg["content"]]})
            else:
                messages.append({"role": "model", "parts": [msg["content"]]})

        # Add curemt prompt
        messages.append({"role": "user", "parts": [prompt]})

        # Generate response from GEMINI
        chat = model.start_chat(history=messages[:-1])
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"Error communicating with GEMINI PI: {str(e)}."


def summarize_conversations(conversations:List[Dict[str, Any]])->str:
    if not conversations:
        return "No recent conversations found"
    
    # Format conversations for the model
    conversations_texts = []
    for idx, conv in enumerate(conversations):
        conv_text = f"Conversations {idx + 1} ({conv['timestamp']}:\n)"
        for msg in conv['messages']:
            conv_text += f"{msg['role'].upper()}: {msg['content']}\n"
        conversations_texts.append(conv_text)
        text = '\n\n'.join(conversations_texts)

    prompt = f"""
Please provide a concise summary of this following recent conversations:
{text}
Focus on key topics discussed, questions asked, and information provided.
Highligh any recurring themes or important points.
"""
    
    response = model.generate_content(prompt)
    return response.text



# Streamlit UI
def main():
    st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖")
    st.title("© Gemini AI Chatbot")

    # Intialize database
    init_db()

    # Intialize session state for chat history and session ID
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.datetime.now().strftime("^Y%m%d%H%M%S")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat input area
    with st.container():
        user_input = st.chat_input("Type your message here...")

        if user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({"role":"user", "content": user_input})
            store_message(st.session_state.session_id, "user", user_input)

            # Get response from Gemini
            with st.spinner("Thinking..."):
                response = chat_with_gemini(user_input, st.session_state.chat_history)

            # Add assistant response to hat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            store_message(st.session_state.session_id, "assistant", response)

    # Display the chat history
    for messsage in st.session_state.chat_history:
        with st.chat_message(messsage["role"]):
            st.write(messsage["content"])

    # Sidebar with recall feature
    with st.sidebar:
        st.title("Conversation Recall")

        if st.button("📜 Summarize Recent Conversations"):
            with st.spinner("Generating summary..."):
                # Get recent conversations
                recent_convs = get_recent_conversations(st.session_state.session_id)

                # Generate Summary
                summary = summarize_conversations(recent_convs)
                
                # Store summary for most recent conversations

                if recent_convs:
                    start_conversations_summary(
                        st.session_state.session_id, recent_convs[0]['id'],
                        summary)
                    
                # Display summary
                st.subheader("Summary of Recent Conversations")
                st.write(summary)
            
        # Clear Chat button
        if st.button("🧹 Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            st.rerun()
            
if __name__ == "__main__":
    main()