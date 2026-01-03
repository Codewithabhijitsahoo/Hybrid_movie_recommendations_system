import pickle
import streamlit as st
import os

# --------------------------------
# Page config
# --------------------------------
st.set_page_config(page_title="Admin Panel", layout="centered")
st.header("🛠 Admin Panel – User Management")

# --------------------------------
# Custom CSS (UI ONLY)
# --------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #141E30, #243B55);
    color: white;
}

h1, h2, h3 {
    text-align: center;
    font-weight: 700;
}

.admin-card {
    background: rgba(255, 255, 255, 0.08);
    padding: 25px;
    border-radius: 15px;
    margin-top: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
}

.user-list {
    background: rgba(0,0,0,0.25);
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-weight: 500;
}

.warning-text {
    color: #ffcc70;
    font-size: 14px;
}

.stButton > button {
    background: linear-gradient(90deg, #ff416c, #ff4b2b);
    color: white;
    border-radius: 25px;
    padding: 10px 25px;
    font-weight: bold;
    border: none;
}

.stButton > button:hover {
    transform: scale(1.05);
    transition: 0.2s ease;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------
# Load ratings
# --------------------------------
if os.path.exists("ratings.pkl"):
    ratings = pickle.load(open("ratings.pkl", "rb"))
else:
    ratings = {}

# --------------------------------
# Delete user function (UNCHANGED)
# --------------------------------
def delete_user(user_id):
    if user_id in ratings:
        del ratings[user_id]
        pickle.dump(ratings, open("ratings.pkl", "wb"))
        return True
    return False

# --------------------------------
# UI
# --------------------------------
if ratings:
    st.subheader("👥 Existing Users")
    st.write("Here are the current users in the system:")

    st.markdown("<div class='admin-card'>", unsafe_allow_html=True)

    for user in ratings.keys():
        st.markdown(f"<div class='user-list'>👤 {user}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    user_to_delete = st.selectbox(
        "🧨 Select a user to delete",
        list(ratings.keys())
    )

    st.markdown(
        f"<p class='warning-text'>⚠ To confirm deletion, type <b>{user_to_delete}</b> exactly below:</p>",
        unsafe_allow_html=True
    )

    confirm_username = st.text_input(
        "Confirmation",
        placeholder="Type the username here"
    )

    if st.button("❌ Delete User", disabled=confirm_username != user_to_delete):
        if confirm_username == user_to_delete:
            if delete_user(user_to_delete):
                st.success(f"✅ User '{user_to_delete}' deleted successfully")
                st.rerun()
            else:
                st.error("❌ User not found")
        else:
            st.warning("⚠ Confirmation does not match. Please type the exact username.")
else:
    st.info("ℹ No users available to delete")