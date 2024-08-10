import streamlit as st
from AutomateDice import main as run_playwright_script
from _data_.Profiles.main_profile import user_profile, display_profile

# Streamlit UI
st.title("Automated Job Search Application")

# Display user profile
st.subheader("User Profile")
st.write(f"Name: {user_profile.name}")
st.write(f"Email: {user_profile.email}")
st.write(f"City: {user_profile.city}")
st.write(f"Country: {user_profile.country}")
st.write(f"Timezone: {user_profile.timezone}")
st.write(f"Apply Every: {user_profile.apply_every.value}")

# Display the profile in a detailed view
st.subheader("Full Profile Details")
st.text(display_profile(user_profile))

# Run the Playwright script
if st.button("Run Job Search"):
    st.write("Starting job search...")
    run_playwright_script()
    st.success("Job search completed.")
