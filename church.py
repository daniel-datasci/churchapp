import streamlit as st
import pandas as pd
from datetime import datetime, date
import matplotlib.pyplot as plt

# Initialize session state for data storage
if 'branches' not in st.session_state:
    st.session_state.branches = pd.DataFrame(columns=[
        'Branch Name','Branch Location','Total Cell Venues','Branch Status'
    ])
if 'members' not in st.session_state:
    st.session_state.members = pd.DataFrame(columns=[
        'Member Name','Date of Birth','Email','Phone','Gender','Status'
    ])
if 'staff' not in st.session_state:
    st.session_state.staff = pd.DataFrame(columns=[
        'Staff Name','Email','Phone','PCF','Role'
    ])
if 'meeting_days' not in st.session_state:
    st.session_state.meeting_days = []
if 'reports' not in st.session_state:
    st.session_state.reports = pd.DataFrame(columns=[
        'Meeting Day','Total Attn.','Male Attn.','Female Attn.','New Converts','First Timers','Date of Meeting'
    ])

st.set_page_config(page_title="Dominion City Ago Church Management App", layout="wide")

st.sidebar.title("Menu")
page = st.sidebar.radio("", [
    'Dashboard','Reports','Meeting Days','Branches','Members','Staff & Roles','Tools & Resources','Communications Hub','Support'
])

# Common helpers
def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

# Dashboard
if page == 'Dashboard':
    st.title("Dominion City Ago")
    st.write(datetime.now().strftime("%B %d, %Y"))
    # Summaries
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Branches", len(st.session_state.branches))
    col2.metric("Total Staff", len(st.session_state.staff))
    col3.metric("Total Members", len(st.session_state.members))

    # Attendance chart
    st.subheader("Attendance Chart")
    if not st.session_state.reports.empty:
        attn = st.session_state.reports.groupby('Meeting Day')['Total Attn.'].sum()
        st.line_chart(attn)
    else:
        st.info("No reports to display.")

    # Upcoming meeting days
    st.subheader("Upcoming Meeting Day Events")
    upcoming = [d for d in st.session_state.meeting_days if datetime.strptime(d, "%Y-%m-%d").date() >= date.today()]
    st.write(upcoming or "No upcoming meeting days.")

    # Upcoming birthdays
    st.subheader("Upcoming Birthdays")
    today = date.today()
    birthdays = []
    for _, row in st.session_state.members.iterrows():
        dob = datetime.strptime(row['Date of Birth'], "%Y-%m-%d").date()
        this_year_bday = dob.replace(year=today.year)
        delta = (this_year_bday - today).days
        if 0 <= delta <= 30:
            birthdays.append(f"{row['Member Name']} - {this_year_bday}")
    st.write(birthdays or "No upcoming birthdays in the next 30 days.")

# Reports
elif page == 'Reports':
    st.title("Reports")
    # Filter options
    filter_opt = st.selectbox("Filter Reports By", [
        'Service (Meeting Day)','Monthly','Global'
    ])
    # ADD SERVICE REPORT
    with st.form("report_form", clear_on_submit=True):
        st.subheader("Add Service Report")
        mday = st.selectbox("Meeting Day", st.session_state.meeting_days)
        total = st.number_input("Total Attendance", min_value=0)
        male = st.number_input("Male Attendance", min_value=0)
        female = st.number_input("Female Attendance", min_value=0)
        converts = st.number_input("New Converts", min_value=0)
        first_timers = st.number_input("First Timers", min_value=0)
        dom = st.date_input("Date of Meeting")
        submitted = st.form_submit_button("Add Service Report")
        if submitted:
            new_row = pd.DataFrame([{
                'Meeting Day': mday,
                'Total Attn.': total,
                'Male Attn.': male,
                'Female Attn.': female,
                'New Converts': converts,
                'First Timers': first_timers,
                'Date of Meeting': dom.strftime('%Y-%m-%d')
            }])
            st.session_state.reports = pd.concat([st.session_state.reports, new_row], ignore_index=True)
            st.success("Report added.")
    # Display table
    st.subheader("Service Reports")
    st.dataframe(st.session_state.reports)

# Meeting Days
elif page == 'Meeting Days':
    st.title("Meeting Days")
    if st.button("Add Meeting Day"):
        new_day = st.date_input("New Meeting Day")
        sd = new_day.strftime('%Y-%m-%d')
        if sd not in st.session_state.meeting_days:
            st.session_state.meeting_days.append(sd)
            st.success(f"Meeting day {sd} added.")
    st.write(st.session_state.meeting_days)

# Branches
elif page == 'Branches':
    st.title("Branches")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Branches", len(st.session_state.branches))
    col2.metric("Total Branch Pastors", "-")
    col3.metric("Total Cell Venues", st.session_state.branches['Total Cell Venues'].sum() if not st.session_state.branches.empty else 0)
    col4.metric("Total Cell Leaders", "-")
    with st.form("branch_form", clear_on_submit=True):
        st.subheader("Add New Branch")
        name = st.text_input("Branch Name")
        loc = st.text_input("Branch Location")
        venues = st.number_input("Total Cell Venues", min_value=0)
        status = st.selectbox("Branch Status", ['Active','Inactive'])
        submitted = st.form_submit_button("Add New Branch")
        if submitted:
            new_row = pd.DataFrame([{
                "Branch Name": name,
                "Branch Location": location,
                "Total Cell Venues": cell_venues,
                "Branch Status": status
            }])
            st.session_state.branches = pd.concat([st.session_state.branches, new_row], ignore_index=True)
            st.success("Branch added.")
    st.dataframe(st.session_state.branches)

# Members
elif page == 'Members':
    st.title("Members")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Members", len(st.session_state.members))
    col2.metric("Total Men", st.session_state.members['Gender'].value_counts().get('Male', 0))
    col3.metric("Total Women", st.session_state.members['Gender'].value_counts().get('Female', 0))
    col4.metric("Total Children", st.session_state.members['Status'].value_counts().get('Child', 0))
    with st.form("member_form", clear_on_submit=True):
        st.subheader("Add New Member")
        name = st.text_input("Member Name")
        dob = st.date_input("Date of Birth")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        gender = st.selectbox("Gender", ['Male','Female'])
        status = st.selectbox("Status", ['Adult','Child'])
        submitted = st.form_submit_button("Add New Member")
        if submitted:
            new_row = pd.DataFrame([{
                'Member Name': name,
                'Date of Birth': dob.strftime('%Y-%m-%d'),
                'Email': email,
                'Phone': phone,
                'Gender': gender,
                'Status': status
            }])
            st.session_state.members = pd.concat([st.session_state.members, new_row], ignore_index=True)
            st.success("Member added.")
    st.dataframe(st.session_state.members)

# Staff & Roles
elif page == 'Staff & Roles':
    st.title("Staff & Roles")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Staff", len(st.session_state.staff))
    col2.metric("Total PCF Pastors", "-")
    col3.metric("Total Head of Departments", "-")
    col4.metric("Total Cell Leaders", "-")
    col5.metric("Total Workers", "-")
    with st.form("staff_form", clear_on_submit=True):
        st.subheader("Add New Staff")
        name = st.text_input("Staff Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        pcf = st.text_input("PCF")
        role = st.selectbox("Role", ['PCF Pastor','Head of Departments','Cell Leader','Worker'])
        submitted = st.form_submit_button("Add New Staff")
        if submitted:
            new_row = pd.DataFrame([{
                'Staff Name': name,
                'Email': email,
                'Phone': phone,
                'PCF': pcf,
                'Role': role
            }])
            st.session_state.staff = pd.concat([st.session_state.staff, new_row], ignore_index=True)
            st.success("Staff added.")
    st.dataframe(st.session_state.staff)

# Placeholder pages
elif page == 'Tools & Resources':
    st.title("Tools & Resources")
    st.info("To be implemented.")
elif page == 'Communications Hub':
    st.title("Communications Hub")
    st.info("To be implemented.")
elif page == 'Support':
    st.title("Support")
    st.info("To be implemented.")
