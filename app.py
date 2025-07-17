import streamlit as st
import pandas as pd
from twilio.rest import Client

USERS_FILE = "users.csv"
DONORS_FILE = "donors.csv"

def load_data(file, cols):
    try:
        return pd.read_csv(file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=cols)
        df.to_csv(file, index=False)
        return df

def save_data(file, new_data):
    try:
        df = pd.read_csv(file)
    except FileNotFoundError:
        df = pd.DataFrame()
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(file, index=False)

def send_whatsapp_message(to, message):
    account_sid = st.secrets["twilio"]["account_sid"]
    auth_token = st.secrets["twilio"]["auth_token"]
    from_whatsapp = st.secrets["twilio"]["from_whatsapp"]

    client = Client(account_sid, auth_token)
    try:
        msg = client.messages.create(
            body=message,
            from_=from_whatsapp,
            to=f'whatsapp:{to}'
        )
        return f"Message sent to {to}"
    except Exception as e:
        return f"Failed to send message: {e}"

st.set_page_config("Blood Donation App", layout="wide")
st.title("🩸 Blood Donation App")

menu = st.sidebar.radio("Menu", ["User Registration", "Donor Registration", "Search Donors"])

if menu == "User Registration":
    st.header("Register as User")
    name = st.text_input("Name")
    email = st.text_input("Email")
    age = st.number_input("Age", 1, 100)
    city = st.text_input("City / Area")

    if st.button("Register User"):
        if name and email:
            user_data = pd.DataFrame([{
                "Name": name,
                "Email": email,
                "Age": age,
                "City": city
            }])
            save_data(USERS_FILE, user_data)
            st.success("User registered successfully")
        else:
            st.warning("Please fill in all required fields")

elif menu == "Donor Registration":
    st.header("Register as Donor")
    name = st.text_input("Full Name")
    phone = st.text_input("WhatsApp Phone Number (e.g. +91XXXXXXXXXX)")
    blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    age = st.number_input("Age", 18, 65)
    city = st.text_input("City / Area")

    if st.button("Register Donor"):
        if name and phone and blood_group and city:
            donor_data = pd.DataFrame([{
                "Name": name,
                "Phone": phone,
                "BloodGroup": blood_group,
                "Age": age,
                "City": city
            }])
            save_data(DONORS_FILE, donor_data)
            st.success("Donor registered successfully")
        else:
            st.warning("Please complete all fields")

elif menu == "Search Donors":
    st.header("Search Blood Donors")

    df = load_data(DONORS_FILE, ["Name", "Phone", "BloodGroup", "Age", "City"])
    if df.empty:
        st.info("No donor data available yet.")
    else:
        city_filter = st.text_input("Search by City / Area")
        blood_filter = st.selectbox("Select Blood Group", ["All"] + sorted(df["BloodGroup"].unique()))

        filtered = df.copy()
        if city_filter:
            filtered = filtered[filtered["City"].str.contains(city_filter, case=False, na=False)]
        if blood_filter != "All":
            filtered = filtered[filtered["BloodGroup"] == blood_filter]

        st.write(f"Found {len(filtered)} donor(s)")
        st.dataframe(filtered.reset_index(drop=True))

        if not filtered.empty:
            selected = st.selectbox("Select Donor to Send WhatsApp Message", filtered["Phone"].tolist())
            message = st.text_area("Message", f"Hello, we urgently need {blood_filter} blood in {city_filter}. Can you help?")
            if st.button("Send WhatsApp Message"):
                result = send_whatsapp_message(selected, message)
                st.info(result)
