import streamlit as st
from smart_hospital import run_patient_flow, get_doctor_status, get_beds
import logging
from logging import debug
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


st.set_page_config(page_title="SHMAS : Smart Hospital Multi-Agent System", layout="wide")
st.markdown("""
<div class="logo"></div>
<style>
    /* Add background image */
    [data-testid="stAppViewContainer"] {
        # background-image: url("https://images.unsplash.com/photo-1586773860418-d37222d8fce3?auto=format&fit=crop&q=80");
        background-image: url("https://img.freepik.com/free-vector/blue-pink-halftone-background_53876-99004.jpg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Add semi-transparent background to main content */
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem;
    }

    /* Hospital logo styling */
    .logo {
        position: fixed;
        top: 50px;
        right: 15px;
        z-index: 50;
        width: 100px;
        height: 100px;
        # background-image: url("https://www.freepnglogos.com/uploads/doctor-png/doctor-png-gallery-images-yopriceville-22.png");
        background-image: url("https://png.pngtree.com/png-vector/20220920/ourmid/pngtree-healthcare-png-image_6207439.png");
        background-size: contain;
        background-repeat: no-repeat;
        transition: transform 1s ease;
    }

    .logo:hover {
        transform: rotate(10deg) scale(1.1);
    }

    /* Adjust existing elements for better visibility */
    .patient-form, .doctor-card, .patient-card {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(5px);
    }
</style>
<style>
    /* Target all input elements in the patient form */
    .patient-form input {
        background-color: #eeffee !important;  /* Light blue hospital theme */
        border-radius: 5px;
        padding: 8px 12px !important;
    }

    /* Specific styling for text areas */
    .patient-form textarea {
        background-color: #eeffee !important;
        border-radius: 5px;
        padding: 8px 12px !important;
    }

    /* Style number inputs */
    .patient-form .stNumberInput input {
        background-color: #eeffee !important;
    }

    /* Style select boxes */
    .patient-form .stSelectbox select {
        background-color: #eeffee !important;
        border-radius: 5px;
        padding: 8px 12px !important;
    }

    /* Add focus effect */
    .patient-form input:focus, 
    .patient-form textarea:focus,
    .patient-form select:focus {
        background-color: #eeffee !important;
        border-color: #3498db !important;
        box-shadow: 0 0 0 2px rgba(52,152,219,0.2);
    }
</style>
<style>
    .priority-score { font-weight: bold; color: #2ecc71; }
    .department-header { 
        background-color: #34495e !important; 
        color: white !important;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .log-success { color: #2ecc71; }
    .log-error { color: #e74c3c; }
    .log-time { 
        color: #3498db; 
        font-family: monospace;
        font-size: 0.9em;
        margin-right: 10px;
    }
    .status-button { width: 100%; margin-bottom: 10px; }
    .patient-form { background-color: #f8f9fa; padding: 20px; border-radius: 10px; }
    .log-entry { display: flex; align-items: center; margin-bottom: 5px; }
    .doctor-card { 
        border: 1px solid #ddd; 
        border-radius: 8px; 
        padding: 12px; 
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .doctor-busy { background-color: #ffeeee; border-left: 4px solid #e74c3c; }
    .doctor-available { background-color: #eeffee; border-left: 4px solid #2ecc71; }
    .patient-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .critical { border-left: 4px solid #e74c3c; }
    .urgent { border-left: 4px solid #f39c12; }
    .semi-urgent { border-left: 4px solid #f1c40f; }
    .routine { border-left: 4px solid #2ecc71; }
</style>
""", unsafe_allow_html=True)

def get_priority_class(triage_level):
    if triage_level >= 4: return "critical"
    elif triage_level == 3: return "urgent"
    elif triage_level == 2: return "semi-urgent"
    return "routine"

def get_priority_icon(triage_level):
    if triage_level >= 4: return "🔴"
    elif triage_level == 3: return "🟠"
    elif triage_level == 2: return "🟡"
    return "🟢"

def display_patient_form():
    with st.container():
        st.subheader("🧑‍⚕️ New Patient Admission")
        with st.form("patient_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Patient Name", "John Doe")
                age = st.number_input("Age", 0, 120, 45)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            with col2:
                email = st.text_input("Email", "johndoe@example.com")
                symptoms = st.text_area("Symptoms (comma separated)", 
                                     "chest pain, shortness of breath").split(",")
                duration = st.number_input("Symptom Duration (hours)", 0, 720, 2)
                
            
            st.subheader("🩺 Vital Signs")
            vital_cols = st.columns(2)
            with vital_cols[0]:
                systolic = st.number_input("Systolic BP", 60, 250, 120)
                hr = st.number_input("Heart Rate (bpm)", 30, 200, 80)
            with vital_cols[1]:
                diastolic = st.number_input("Diastolic BP", 40, 150, 80)
            
            if st.form_submit_button("🚑 Admit Patient"):
                vitals = {
                    "blood_pressure": {"systolic": systolic, "diastolic": diastolic},
                    "heart_rate": hr
                }
                
                with st.spinner("Processing admission..."):
                    result = run_patient_flow(
                        name=name.strip(),
                        symptoms=[s.strip() for s in symptoms],
                        vitals=vitals,
                        symptom_duration=duration,
                        age=age,
                        gender=gender,
                        email = email
                    )
                    
                    # Store results in session state
                    st.session_state['last_patient'] = result["patient"].to_dict()
                    st.session_state['logs'] = result["logs"]
                    st.session_state['show_results'] = True
                    st.rerun()

def display_status_buttons():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍⚕️ Toggle Doctor Status", key="doctor_btn"):
            st.session_state['show_doctors'] = not st.session_state.get('show_doctors', True)
    with col2:
        if st.button("🛏️ Toggle Bed Status", key="bed_btn"):
            st.session_state['show_beds'] = not st.session_state.get('show_beds', True)

def display_doctor_status():
    if st.session_state.get('show_doctors', True):
        st.subheader("👨‍⚕️ Doctor Status")
        
        # Add auto-refresh
        if st.button("🔄 Refresh Status"):
            st.rerun()
        
        status = get_doctor_status()
        
        for doc in status:
            if doc['status'] == "BUSY":
                st.markdown(f"""
                <div class="doctor-card doctor-busy">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 2;">
                            <strong style="font-size: 1.1em;">{doc['doctor_name']}</strong>
                            <div style="color: #666; font-size: 0.9em;">{doc['department']}</div>
                            <div style="color: #e74c3c; margin-top: 5px;">
                                <strong>BUSY</strong> with {doc['with_patient']}
                            </div>
                        </div>
                        <div style="flex: 1; text-align: right;">
                            <div style="font-size: 0.9em;">
                                <span style="color: #666;">Ends:</span> {doc['finish_time']}
                            </div>
                            <div style="margin-top: 5px;">
                                <span style="background-color: #e74c3c; color: white; padding: 2px 5px; border-radius: 4px;">
                                    ⏱️ {doc['time_remaining']} left
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="doctor-card doctor-available">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 2;">
                            <strong style="font-size: 1.1em;">{doc['doctor_name']}</strong>
                            <div style="color: #666; font-size: 0.9em;">{doc['department']}</div>
                            <div style="color: #2ecc71; margin-top: 5px;">
                                <strong>AVAILABLE</strong>
                            </div>
                        </div>
                        <div style="flex: 1; text-align: right;">
                            <span style="background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 4px;">
                                Ready for patient
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def display_bed_status():
    if st.session_state.get('show_beds', True):
        st.subheader("🛏️ Bed Status")
        beds = get_beds()
        for bed_type, bed_data in beds.items():
            total_beds = bed_data[0] + bed_data[1]
            available_beds = bed_data[0]
            occupied_beds = bed_data[1]
            
            st.markdown(f"""
            <div class="doctor-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <strong style="font-size: 1.1em;">{bed_type.replace('_', ' ')}</strong>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <div style="font-size: 0.9em;">Total: {total_beds}</div>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <div style="color: #2ecc71; font-size: 0.9em;">Available: {available_beds}</div>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <div style="color: #e74c3c; font-size: 0.9em;">Occupied: {occupied_beds}</div>
                    </div>
                    <div style="flex: 1; text-align: right;">
                        <div style="width: 100%; height: 10px; background-color: #eee; border-radius: 5px;">
                            <div style="width: {available_beds/total_beds*100}%; height: 100%; background-color: #2ecc71; border-radius: 5px;"></div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def display_patient_results():
    if st.session_state.get('show_results', False) and 'last_patient' in st.session_state:
        patient = st.session_state['last_patient']
        logs = st.session_state['logs']
        
        st.subheader("📋 Patient Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric(f"{get_priority_icon(patient['triage_level'])} Triage Level", 
                   f"{patient['triage_level']} - {get_priority_class(patient['triage_level']).title()}")
        col2.metric("Department", patient['department'])
        col3.metric("Priority Score", patient['priority_score'])
        
        st.subheader("📜 System Execution Log")
        for log in logs:
            if ']' in log:
                timestamp, message = log.split(']', 1)
                timestamp = timestamp[1:]  # Remove the opening bracket
                message = message.strip()
            else:
                timestamp = ""
                message = log
            
            if "error" in message.lower():
                st.markdown(f"""
                <div class="log-entry">
                    <span style="color: #e74c3c; margin-right: 10px;">❌</span>
                    <span class="log-time">{timestamp}</span>
                    <span class="log-error">{message}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="log-entry">
                    <span style="color: #2ecc71; margin-right: 10px;">✅</span>
                    <span class="log-time">{timestamp}</span>
                    <span class="log-success">{message}</span>
                </div>
                """, unsafe_allow_html=True)

def main():
    # Initialize all necessary session state variables
    if 'last_patient' not in st.session_state:
        st.session_state.last_patient = None
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'show_doctors' not in st.session_state:
        st.session_state.show_doctors = True
    if 'show_beds' not in st.session_state:
        st.session_state.show_beds = True
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    
    st.title("🏥 SHMAS : Smart Hospital Multi-Agent System")
    
    # Layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        with st.container():
            display_patient_form()
            display_patient_results()
    
    with col2:
        display_status_buttons()
        display_doctor_status()
        display_bed_status()
        # display_patient_queues()

if __name__ == "__main__":
    main()