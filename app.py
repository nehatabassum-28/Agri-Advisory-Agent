import streamlit as st
import urllib.request
import json

st.title("🌾 Agri-Advisory Agent")

question = st.text_input("👨‍🌾 Ask your farming question:")

if st.button("Get Advice"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        data = json.dumps({
            "model": "llama3.2:latest",
            "prompt": question,
            "stream": False
        }).encode("utf-8")

        request = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode("utf-8"))

            st.subheader("🤖 AI Advice")
            st.write(result["response"])

        except Exception as e:
            st.error("Ollama connection error: " + str(e))