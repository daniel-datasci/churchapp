import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, date

today = datetime.now().date()

# --- Database Setup ------------------------------------------------------------
conn = sqlite3.connect("church.db", check_same_thread=False)
c = conn.cursor()

def init_table(name, columns_defs):
    c.execute(f"CREATE TABLE IF NOT EXISTS {name} ({columns_defs})")
    conn.commit()

init_table("branches",
    "BranchName TEXT, BranchLocation TEXT, TotalCellVenues INTEGER, BranchStatus TEXT")
init_table("members",
    "MemberName TEXT, MemberDOB TEXT, MemberEmail TEXT, MemberPhone TEXT, MemberGender TEXT, MemberStatus TEXT")
init_table("staff",
    "StaffName TEXT, StaffEmail TEXT, StaffPhone TEXT, StaffPCF TEXT, StaffRole TEXT")
init_table("meeting_days",
    "MeetingDay TEXT")
init_table("service_reports",
    "MeetingDay TEXT, TotalAttn INTEGER, MaleAttn INTEGER, FemaleAttn INTEGER, NewConverts INTEGER, FirstTimers INTEGER, DateOfMeeting TEXT")
init_table("cell_reports", 
    "BranchName TEXT, PCFPastor TEXT, CellLeader TEXT, TotalAttn INTEGER, NewConverts INTEGER, FirstTimers INTEGER, SundayServiceAttn INTEGER, TotalOffering REAL, DateOfMeeting TEXT")

# --- Helper to load each table into a DataFrame --------------------------------
def load_df(table, cols, date_cols=None):
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    if df.empty:
        df = pd.DataFrame(columns=cols)
    else:
        # rename columns if needed, and parse dates
        df.columns = cols
        if date_cols:
            for dc in date_cols:
                df[dc] = pd.to_datetime(df[dc]).dt.date
    return df

# --- Initialize Session State DataFrames ---------------------------------------
def init_state():
    if "branches" not in st.session_state:
        st.session_state.branches = load_df(
            "branches",
            ["Branch Name", "Branch Location", "Total Cell Venues", "Branch Status"]
        )
    if "members" not in st.session_state:
        st.session_state.members = load_df(
            "members",
            ["Member Name", "Member Date of Birth", "Member Email", "Member Phone", "Member Gender", "Member Status"],
            date_cols=["Member Date of Birth"]
        )
    if "staff" not in st.session_state:
        st.session_state.staff = load_df(
            "staff",
            ["Staff Name", "Staff Email", "Staff Phone", "Staff PCF", "Staff Role"]
        )
    if "meeting_days" not in st.session_state:
        st.session_state.meeting_days = load_df(
            "meeting_days",
            ["Meeting Day"]
        )
    if "service_reports" not in st.session_state:
        st.session_state.service_reports = load_df(
            "service_reports",
            ["Meeting Day","Total Attn.","Male Attn.","Female Attn.","New Converts","First Timers","Date of Meeting"],
            date_cols=["Date of Meeting"]
        )
    if "cell_reports" not in st.session_state:
        st.session_state.cell_reports = load_df(
            "cell_reports",
            ["Branch Name", "PCF Pastor", "Cell Leader", "Total Attn.", "New Converts", "First Timers", "Sunday Service Attn", "Total Offering", "Date of Meeting"],
            date_cols=["Date of Meeting"]
        )

init_state()

# --- Insert helpers ------------------------------------------------------------
def db_insert(table, cols, values):
    placeholders = ",".join("?" for _ in cols)
    c.execute(
        f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})",
        values
    )
    conn.commit()

# --- App Config ---------------------------------------------------------------
st.set_page_config(page_title="Church Management", layout="wide")
church_name = "Dominion City Ago"

# --- Sidebar Navigation --------------------------------------------------------
st.sidebar.title("Menu")
menu = st.sidebar.radio("", [
    'Dashboard','Service Reports','Cell Reports', 'Meeting Days','Branches','Members','Staff & Roles','Tools & Resources','Communications Hub','Support'
])

#menu = st.sidebar.selectbox(
    #"Navigate",
    #["Dashboard","Reports","Meeting Days","Branches","Members","Staff & Roles","Tools & Resources","Communications Hub","Support"]
#)

# --- Dashboard ---------------------------------------------------------------
if menu == "Dashboard":
    st.title(church_name)
    st.markdown(f"**Date:** {datetime.now():%A, %B %-d, %Y}")
    cols = st.columns(4)
    cols[0].metric("Total Branches", len(st.session_state.branches))
    cols[1].metric("Total Staff",    len(st.session_state.staff))
    cols[2].metric("Total Members",  len(st.session_state.members))

    # Attendance chart
    if not st.session_state.service_reports.empty:
        chart_data = (
            st.session_state.service_reports
              .groupby("Meeting Day")["Total Attn."]
              .sum()
              .reset_index()
        )
        fig, ax = plt.subplots()
        ax.plot(chart_data["Meeting Day"], chart_data["Total Attn."], marker="o")
        ax.set_xlabel("Meeting Day")
        ax.set_ylabel("Total Attendance")
        ax.set_title("Attendance by Meeting Day")
        st.pyplot(fig)
    else:
        st.info("No service reports yet to chart.")

    # Upcoming meeting days
    st.subheader("Upcoming Meeting Days")
    if st.session_state.meeting_days.empty:
        st.write("No meeting days set.")
    else:
        st.write(", ".join(st.session_state.meeting_days["Meeting Day"]))

    # Upcoming birthdays (next 30 days)
    st.subheader("Upcoming Birthdays")
    today = datetime.now().date()
    bdays = []
    for _, r in st.session_state.members.iterrows():
        dob = r["Member Date of Birth"]
        this_year = dob.replace(year=today.year)
        delta = (this_year - today).days
        if 0 <= delta <= 30:
            bdays.append(f"{r['Member Name']} ({this_year:%b %-d})")
    st.write(", ".join(bdays) if bdays else "No birthdays in the next 30 days.")

# --- Reports ---------------------------------------------------------------
elif menu == "Service Reports":
    st.header("Service Reports")
    st.selectbox("View by", ["Each Meeting Day","Monthly","Global"])
    with st.form("add_report", clear_on_submit=True):
        md    = st.selectbox("Meeting Day", st.session_state.meeting_days["Meeting Day"])
        total = st.number_input("Total Attendance", min_value=0, step=1)
        male  = st.number_input("Male Attendance", min_value=0, step=1)
        female= st.number_input("Female Attendance", min_value=0, step=1)
        conv  = st.number_input("New Converts", min_value=0, step=1)
        first = st.number_input("First Timers", min_value=0, step=1)
        date_ = st.date_input("Date of Meeting", value=today)
        if st.form_submit_button("ADD SERVICE REPORT"):
            row = {
              "Meeting Day": md, "Total Attn.": total,
              "Male Attn.": male, "Female Attn.": female,
              "New Converts": conv, "First Timers": first,
              "Date of Meeting": date_
            }
            # DB insert
            db_insert(
              "service_reports",
              ["MeetingDay","TotalAttn","MaleAttn","FemaleAttn","NewConverts","FirstTimers","DateOfMeeting"],
              [md,total,male,female,conv,first,str(date_)]
            )
            # session_state append
            st.session_state.service_reports = pd.concat(
              [st.session_state.service_reports, pd.DataFrame([row])],
              ignore_index=True
            )
            st.success("Report added.")
    st.dataframe(st.session_state.service_reports)


# --- Cell Reports ---------------------------------------------------------------
elif menu == "Cell Reports":
    st.header("Cell Reports")

    # — Filter by Branch —
    all_branches = list(st.session_state.branches["Branch Name"])
    branch_filter = st.selectbox("Filter by Branch", ["All"] + all_branches)

    # — Add Cell Report Form —
    with st.form("add_cell_report", clear_on_submit=True):
        branch      = st.selectbox("Branch Name", all_branches)
        # dynamic PCF Pastor list
        pcf_opts    = st.session_state.staff.loc[
                          st.session_state.staff["Staff Role"] == "PCF Pastor",
                          "Staff Name"
                      ].tolist()
        pcf_pastor  = st.selectbox("PCF Pastor", pcf_opts)

        # dynamic Cell Leader list
        leader_opts = st.session_state.staff.loc[
                          st.session_state.staff["Staff Role"] == "Cell Leader",
                          "Staff Name"
                      ].tolist()
        cell_leader = st.selectbox("Cell Leader", leader_opts)

        total_attn       = st.number_input("Total Attendance", min_value=0, step=1)
        new_converts     = st.number_input("New Converts", min_value=0, step=1)
        first_timers     = st.number_input("First Timers", min_value=0, step=1)
        sunday_attn      = st.number_input("Sunday Service Attn", min_value=0, step=1)
        total_offering   = st.number_input("Total Offering", min_value=0.0, step=0.01, format="%.2f")
        date_meeting     = st.date_input("Date of Meeting", value=today)

        if st.form_submit_button("ADD CELL REPORT"):
            # 1) insert into SQLite
            db_insert(
                "cell_reports",
                [
                  "BranchName","PCFPastor","CellLeader",
                  "TotalAttn","NewConverts","FirstTimers",
                  "SundayServiceAttn","TotalOffering","DateOfMeeting"
                ],
                [
                  branch, pcf_pastor, cell_leader,
                  total_attn, new_converts, first_timers,
                  sunday_attn, total_offering, str(date_meeting)
                ]
            )
            # 2) append to session_state
            new_row = {
              "Branch Name": branch,
              "PCF Pastor": pcf_pastor,
              "Cell Leader": cell_leader,
              "Total Attn.": total_attn,
              "New Converts": new_converts,
              "First Timers": first_timers,
              "Sunday Service Attn": sunday_attn,
              "Total Offering": total_offering,
              "Date of Meeting": date_meeting
            }
            st.session_state.cell_reports = pd.concat(
                [st.session_state.cell_reports, pd.DataFrame([new_row])],
                ignore_index=True
            )
            st.success("Cell report added.")

    # — Display table, filtered if needed —
    df = st.session_state.cell_reports.copy()
    if branch_filter != "All":
        df = df[df["Branch Name"] == branch_filter]
    st.dataframe(df)

# --- Meeting Days ---------------------------------------------------------------
elif menu == "Meeting Days":
    st.header("Weekly Meeting Days")
    with st.form("add_md", clear_on_submit=True):
        md = st.text_input("Meeting Day (e.g. Sunday)")
        if st.form_submit_button("ADD MEETING DAY"):
            db_insert("meeting_days", ["MeetingDay"], [md])
            st.session_state.meeting_days = pd.concat(
              [st.session_state.meeting_days, pd.DataFrame([{"Meeting Day": md}])],
              ignore_index=True
            )
            st.success(f"Added {md}.")
    st.dataframe(st.session_state.meeting_days)

# --- Branches ---------------------------------------------------------------
elif menu == "Branches":
    st.header("Branches")
    cols = st.columns(4)
    cols[0].metric("Total Branches", len(st.session_state.branches))
    pastors = st.session_state.staff["Staff Role"].value_counts().get("PCF Pastor", 0)
    cols[1].metric("Total Branch Pastors", pastors)
    cols[2].metric("Total Cell Venues", st.session_state.branches["Total Cell Venues"].sum())
    cell_leads = st.session_state.staff["Staff Role"].value_counts().get("Cell Leader", 0)
    cols[3].metric("Total Cell Leaders", cell_leads)

    with st.form("add_branch", clear_on_submit=True):
        name = st.text_input("Branch Name")
        loc  = st.text_input("Branch Location")
        cvs  = st.number_input("Total Cell Venues", min_value=0, step=1)
        stat = st.selectbox("Branch Status", ["Active","Inactive"])
        if st.form_submit_button("ADD NEW BRANCH"):
            db_insert(
              "branches",
              ["BranchName","BranchLocation","TotalCellVenues","BranchStatus"],
              [name,loc,cvs,stat]
            )
            new = {"Branch Name": name, "Branch Location": loc,
                   "Total Cell Venues": cvs, "Branch Status": stat}
            st.session_state.branches = pd.concat(
              [st.session_state.branches, pd.DataFrame([new])],
              ignore_index=True
            )
            st.success(f"Branch '{name}' added.")
    st.dataframe(st.session_state.branches)

# --- Members ---------------------------------------------------------------
elif menu == "Members":
    st.header("Members")
    cols = st.columns(4)
    cols[0].metric("Total Members", len(st.session_state.members))
    men   = st.session_state.members["Member Gender"].value_counts().get("Male", 0)
    women = st.session_state.members["Member Gender"].value_counts().get("Female", 0)
    kids  = st.session_state.members["Member Status"].value_counts().get("Child", 0)
    cols[1].metric("Total Men", men)
    cols[2].metric("Total Women", women)
    cols[3].metric("Total Children", kids)

    with st.form("add_member", clear_on_submit=True):
        name   = st.text_input("Member Name")
        dob    = st.date_input(
            "Member Date of Birth",
            min_value=date(1950,1,1),
            max_value=date(2025,12,31),
            value=date(1990,1,1)
        )
        email  = st.text_input("Member Email")
        phone  = st.text_input("Member Phone")
        gen    = st.selectbox("Member Gender", ["Male","Female"])
        status = st.selectbox("Member Status", ["Adult","Child"])
        if st.form_submit_button("ADD NEW MEMBER"):
            db_insert(
              "members",
              ["MemberName","MemberDOB","MemberEmail","MemberPhone","MemberGender","MemberStatus"],
              [name,str(dob),email,phone,gen,status]
            )
            new = {
              "Member Name": name, "Member Date of Birth": dob,
              "Member Email": email, "Member Phone": phone,
              "Member Gender": gen, "Member Status": status
            }
            st.session_state.members = pd.concat(
              [st.session_state.members, pd.DataFrame([new])],
              ignore_index=True
            )
            st.success(f"Member '{name}' added.")
    st.dataframe(st.session_state.members)

# --- Staff & Roles -------------------------------------------------------------
elif menu == "Staff & Roles":
    st.header("Staff & Roles")
    cols = st.columns(5)
    cols[0].metric("Total Staff", len(st.session_state.staff))
    cnt = st.session_state.staff["Staff Role"].value_counts()
    cols[1].metric("PCF Pastors", cnt.get("PCF Pastor", 0))
    cols[2].metric("Heads of Dept.", cnt.get("Head of Departments", 0))
    cols[3].metric("Cell Leaders", cnt.get("Cell Leader", 0))
    cols[4].metric("Workers", cnt.get("Worker", 0))

    with st.form("add_staff", clear_on_submit=True):
        name = st.text_input("Staff Name")
        email= st.text_input("Staff Email")
        phone= st.text_input("Staff Phone")
        pcf  = st.text_input("Staff PCF (Branch)")
        role = st.selectbox("Staff Role", ["PCF Pastor","Head of Departments","Cell Leader","Worker"])
        if st.form_submit_button("ADD NEW STAFF"):
            db_insert(
              "staff",
              ["StaffName","StaffEmail","StaffPhone","StaffPCF","StaffRole"],
              [name,email,phone,pcf,role]
            )
            new = {
              "Staff Name": name, "Staff Email": email,
              "Staff Phone": phone, "Staff PCF": pcf, "Staff Role": role
            }
            st.session_state.staff = pd.concat(
              [st.session_state.staff, pd.DataFrame([new])],
              ignore_index=True
            )
            st.success(f"Staff '{name}' added.")
    st.dataframe(st.session_state.staff)

# --- Stub Pages ---------------------------------------------------------------
elif menu == "Tools & Resources":
    st.header("Tools & Resources"); st.info("Coming soon!")
elif menu == "Communications Hub":
    st.header("Communications Hub"); st.info("Coming soon!")
elif menu == "Support":
    st.header("Support"); st.info("Coming soon!")
