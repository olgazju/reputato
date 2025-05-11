import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Reputato", page_icon="🥔")
st.title("🥔 Reputato")
st.subheader("Is this company worth your time? Let us check.")

# --- Input section (always on top) ---
company_name = st.text_input("Company name", placeholder="e.g. Google")
submit = st.button("Analyze")

# --- Placeholder for results ---
result_container = st.empty()

if submit and company_name.strip():
    with st.spinner("Analyzing... getting potatoes ready"):
        try:
            response = requests.get(
                f"{BACKEND_URL}/analyze_company", params={"name": company_name}
            )

            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary")
                rating = data.get("rating", 1)

                full = "🥔"
                empty = "<span style='opacity:0.3;'>🥔</span>"
                rating_str = full * rating + empty * (5 - rating)

                with result_container.container():
                    st.success("Done!")
                    st.markdown("### Company Summary")
                    st.write(summary)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='font-size: 1.8rem;'>{rating_str}</div>",
                        unsafe_allow_html=True
                    )
            else:
                result_container.error("Something went wrong.")
        except Exception as e:
            result_container.error(f"Request failed: {e}")
