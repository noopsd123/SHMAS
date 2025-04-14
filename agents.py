from typing import TypedDict, List, Dict
from langchain.schema import HumanMessage
import os, random, json
from langchain_groq import ChatGroq
import pytz
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
import logging
from logging import debug
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
conn = psycopg2.connect(
    host="localhost",
    database="hospital",
    user="postgres",
    password="Neeltej@9",
    port="5432"
    )
cursor = conn.cursor()
queued_patients = []

def get_beds():
    query = """
        SELECT DISTINCT type,
                (SELECT COUNT(*) FROM rooms r1 WHERE r1.type = r.type AND is_occupied = FALSE) available,
                (SELECT COUNT(*) FROM rooms r1 WHERE r1.type = r.type AND is_occupied = TRUE) blocked 
        FROM rooms r;
        """
    cursor.execute(query)
    rows = cursor.fetchall()
    output = {}
    for data in rows:
        output[data[0]] = data[1:]
    return output

def get_doctor_status():
    debug("Getting doctor status update...")
    query = "SELECT refresh_data();"
    cursor.execute(query)
    conn.commit()
    query = f"""
        SELECT
            d.name doctor_name,
            d.specialist department,
            (CASE WHEN d.is_busy=TRUE THEN 'BUSY' ELSE 'AVAILABLE' END) status,
            (CASE WHEN d.is_busy=TRUE THEN p.patient_name ELSE NULL END) with_patient,
            (CASE WHEN d.is_busy=TRUE THEN ROUND(EXTRACT(EPOCH FROM (d.busy_till - CURRENT_TIMESTAMP)) / 60,2) ELSE NULL END) time_remaining,
            (CASE WHEN d.is_busy=TRUE THEN d.busy_till ELSE NULL END) finish_time,
            (CASE WHEN d.is_busy=TRUE THEN d.busy_from ELSE NULL END) start_time
        FROM doctors d
        LEFT JOIN ongoing_cases oc
        ON d.doctor_id = oc.doctor_id
        LEFT JOIN patient_info p
        ON oc.patient_id = p.patient_id;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    output = []
    cols = ["doctor_name","department","status","with_patient","time_remaining","finish_time","start_time"]
    for i in range(len(rows)):
        temp_dict = {}
        for idx, data in enumerate(rows[i]):
            temp_dict[cols[idx]] = data
        output.append(temp_dict)
    return output

def get_block_duration(triage_level):
    return timedelta(minutes=max(1, triage_level))

def get_current_est_time():
    est = pytz.timezone('US/Eastern')
    return datetime.now(est)

def get_current_time_with_ms():
    return datetime.now(pytz.timezone('US/Eastern')).strftime('%H:%M:%S.%f')[:-3]

class Patient:
    def __init__(self, name, vitals, email, gender, age, symptoms, symptom_duration):
        self.name = name
        self.symptoms = symptoms
        self.symptom_duration = symptom_duration
        self.email = email
        self.phone = None
        self.age = age
        self.vitals = vitals
        self.gender = gender
        self.mood = None
        self.triage_level = None
        self.department = None
        self.assigned_doctor = None
        self.assigned_bed = None
        self.bed_priority = None
        self.priority_score = 0.0
        self.entry_time = get_current_est_time()
        self.treatment_completed = False
        self.treatment_end_time = None

    def calculate_priority(self):
        triage_weight = 10
        triage_score = self.triage_level * triage_weight
        
        if self.age >= 50:
            age_score = 8
        elif self.age < 15:
            age_score = 5
        else:
            age_score = 0
            
        hr = self.vitals.get("heart_rate", 80)
        bp_sys = self.vitals.get("blood_pressure", {}).get("systolic", 120)
        bp_dia = self.vitals.get("blood_pressure", {}).get("diastolic", 80)
        
        hr_dev = max(hr - 100, 60 - hr, 0)
        bp_sys_dev = abs(bp_sys - 120) if bp_sys > 140 or bp_sys < 90 else 0
        bp_dia_dev = abs(bp_dia - 80) if bp_dia > 90 or bp_dia < 60 else 0
        vital_score = (hr_dev + bp_sys_dev + bp_dia_dev) * 0.7
        
        duration_score = self.symptom_duration * 0.2
        
        self.priority_score = round(triage_score + age_score + vital_score + duration_score, 1)

    def to_dict(self):
        self.calculate_priority()
        return {
            "name": self.name,
            "symptoms": self.symptoms,
            "symptom_duration": self.symptom_duration,
            "contact_number": self.phone,
            "age": self.age,
            "email": self.email,
            "gender": self.gender,
            "mood": self.mood,
            "triage_level": self.triage_level,
            "department": self.department,
            "assigned_doctor": self.assigned_doctor,
            "assigned_bed": self.assigned_bed,
            "priority_score": self.priority_score,
            "treatment_completed": self.treatment_completed,
            "treatment_end_time": self.treatment_end_time.strftime('%H:%M:%S.%f')[:-3] if self.treatment_end_time else None,
            "entry_time": self.entry_time.strftime('%H:%M:%S.%f')[:-3]
        }

class AgentState(TypedDict):
    patient: Patient
    logs: List[str]
    status: dict
    cache: dict

def adjust_mood_based_on_vitals(patient, detected_mood):
    symptoms_str = " ".join(patient.symptoms).lower()
    if patient.vitals["heart_rate"] > 120 or patient.vitals["blood_pressure"].get("diastolic",80) < 80:
        detected_mood = "panicked"
    elif "cardiac arrest" in symptoms_str:
        detected_mood = "panicked"
    elif "mild cough" in symptoms_str and patient.vitals["heart_rate"] < 100:
        detected_mood = "calm"
    return detected_mood

class MentalHealthAnalyzerAgent:
    def __init__(self):
        self._GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(api_key=self._GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")

    def __call__(self, state: AgentState) -> AgentState:
        debug(f"Entering {self.__class__.__name__} call...")
        patient = state["patient"]
        patient = state["patient"]
        blood_pressure = patient.vitals.get("blood_pressure", {})
        systolic = blood_pressure.get("systolic", 120)
        diastolic = blood_pressure.get("diastolic", 80)
        
        query = f"""
            INSERT INTO patient_info(patient_name, email, phone, gender, symptoms, symptoms_duration, vitals)
            VALUES ('{patient.name}', '{patient.email}', NULL, '{patient.gender}',
            '{", ".join(patient.symptoms)}','{patient.symptom_duration}','{str(patient.vitals).replace("'","\"")}');
            """
        print(query)
        cursor.execute(query)
        conn.commit()
        debug("Patient information inserted successfully...")
        prompt = f"""Analyze patient's emotional state based on:
        - Vitals: BP {systolic}/{diastolic}, HR {patient.vitals.get("heart_rate", 80)}
        - Symptoms: {patient.symptoms}
        - Duration: {patient.symptom_duration} hours
        - Age: {patient.age}
        Return JSON: {{ "mood": "chosen_mood" }}"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        debug("Got mood estimate from LLM...")
        try:
            if '{' in response.content:
                mood_info = json.loads(response.content[response.content.find('{'):response.content.rfind('}')+1])
                if "mood" in mood_info:
                    detected_mood = adjust_mood_based_on_vitals(patient, mood_info["mood"])
                    patient.mood = detected_mood
                    debug("Successfully completed task. Updating status...")
                    mood_emoji = {"calm":"😌", "frustrated":"😖","anxious":"😥","stressed":"😧","confused":"😵‍💫","panicked":"🫨"}
                    state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : Detected Mood is {patient.mood} {mood_emoji[patient.mood]}")
                    state["status"]["MoodAnalyzer"] = "Success"
                    debug(f"Exiting {self.__class__.__name__} call...")
        except Exception as e:
            debug(f"Error estimating the mood...\n{e}")
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : {str(e)}")
            state["status"]["MoodAnalyzer"] = "Failed"
        return state

class EmergencyTriageAgent:
    def __init__(self):
        self._GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(api_key=self._GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")
    
    def __call__(self, state: AgentState) -> AgentState:
        debug(f"Entering {self.__class__.__name__} call...")
        patient = state["patient"]
        bp = patient.vitals.get("blood_pressure", {})
        hr = patient.vitals.get("heart_rate", 80)
        prompt = f"""Assign triage_level (1-5) and department based on:
        - Symptoms: {patient.symptoms}
        - BP: {bp.get('systolic', 120)}/{bp.get('diastolic', 80)}
        - HR: {hr}
        - Mood: {patient.mood}
        - Age: {patient.age}
        - Duration: {patient.symptom_duration}h
        Return JSON: {{"triage_level": number, "department": "string"}}
        return value of department should be in ["Cardiology","Pediatrics","Neurology","Dentist"]"""
        
        llm = ChatGroq(api_key=self._GROQ_API_KEY, model_name="deepseek-r1-distill-llama-70b")
        response = llm.invoke([HumanMessage(content=prompt)])
        debug("Got triage level from the LLM...")
        try:
            if '{' in response.content:
                triage_info = json.loads(response.content[response.content.find('{'):response.content.rfind('}')+1])
                if "triage_level" in triage_info and "department" in triage_info:
                    patient.triage_level = triage_info["triage_level"]
                    patient.department = triage_info["department"]
                    debug(f"triage level : {triage_info["triage_level"]}, department : {triage_info["department"]}")
                    debug("Successfully completed task. Updating status...")
                    state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : Level {patient.triage_level} -> {patient.department}")
                    state["status"]["EmergencyTriage"] = "Success"
                    debug(f"Exiting {self.__class__.__name__} call...")
        except Exception as e:
            debug(f"Error estimating the triage...\n{e}")
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : Error estimating the traige : {str(e)}")
            state["status"]["EmergencyTriage"] = "Failed"
        return state

class DoctorSchedulerAgent:
    def __call__(self, state: AgentState) -> AgentState:
        debug(f"Entering {self.__class__.__name__} call...")
        patient = state["patient"]
        dept = patient.department
        now = datetime.now(pytz.timezone('US/Eastern'))
        formatted_time = now.strftime("%I:%M %p")
        debug("fAttempting to fetch available {dept} specialist doctors...")
        query = f"SELECT * FROM get_available_doctors('{dept}');"
        cursor.execute(query)
        available = cursor.fetchall()
        debug("Fetched the available doctors...")
        print(f"available = {available}")
        if available:
            assigned_doctor_details = random.choice(available)
            patient.assigned_doctor = assigned_doctor_details[1]
            state["cache"]["doctor_assigned"] = assigned_doctor_details
            block_duration = get_block_duration(patient.triage_level)
            blocked_until = now + block_duration
            print(f"block_until = {blocked_until}")
            state["cache"]["doctor_blocked_from"] = now
            state["cache"]["doctor_blocked_until"] = blocked_until
            debug("Attempting to allocate doctor...")
            cursor.execute(f"""
                UPDATE doctors SET is_busy = TRUE,
                                   busy_from = '{now}', 
                                   busy_till = '{blocked_until}'
                                   WHERE doctor_id = {assigned_doctor_details[0]};
            """)
            conn.commit()
            debug("Successfully alloted doctor...")
            state["status"]["DoctorScheduler"] = "Success"
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : Assigned {patient.assigned_doctor} to {patient.name}")
            debug(f"Exiting {self.__class__.__name__} call...")
        else:
            debug("No doctors available...")
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : No {dept} doctor availble.")
            state["status"]["DoctorScheduler"] = "Failed"
        debug(f"Exiting {self.__class__.__name__} call...")
        return state

class BedManagerAgent:
    def __call__(self, state: AgentState) -> AgentState:
        debug(f"Entering {self.__class__.__name__} call...")
        patient = state["patient"]
        level = patient.triage_level
        if level == 5:
            self.bed_priority = ["ICU", "Emergency"]
        elif level in [3, 4]:
            self.bed_priority = ["Ward", "Emergency"]
        else:
            self.bed_priority = ["Normal", "Ward", "Emergency"]
        
        for bed_type in self.bed_priority:
            debug("Attempting to find available bed...")
            cursor.execute(f"SELECT * FROM get_available_rooms('{bed_type}')")
            available_bed_details = cursor.fetchall()
            debug(f"Checking bed type {bed_type}...")
            if available_bed_details:
                debug(f"Found a bed that matches requirements in {bed_type}...")
                patient.assigned_bed = available_bed_details[0][0]
                state["cache"]["bed_assigned"] = available_bed_details
                query = f"""
                    UPDATE rooms SET is_occupied = TRUE WHERE room_number = {available_bed_details[0][0]};
                """
                print(query)
                cursor.execute(query)
                conn.commit()
                debug("Successfully allocated a bed...")
                state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : {patient.name} assigned to {bed_type} bed {patient.assigned_bed} (triage {level})")
                # state["logs"].append(
                #      f"BedManager: {patient.name} assigned to {bed_type} bed {patient.assigned_bed} (triage {level})")
                state["status"]["BedManager"] = "Success"
                debug(f"Exiting {self.__class__.__name__} call...")
                return state        
        debug("No beds found...")
        state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : No beds available for {patient.name}")
        state["status"]["BedManager"] = "Failed"
        debug(f"Exiting {self.__class__.__name__} call...")
        return state
    
class ConflictResolverAgent:
    def __call__(self, state: AgentState) -> AgentState:
        debug(f"Entering {self.__class__.__name__} call...")
        patient = state["patient"]
        bed_status = state["status"]["BedManager"]
        doctor_status = state["status"]["DoctorScheduler"]
        debug("Checking for conflicts in decision making...")
        patient.calculate_priority()
        debug(f"Calculated priority score : {patient.priority_score}")
        state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : Calculated priority score : {patient.priority_score}")
        if bed_status == "Success" and doctor_status == "Success":
            debug("No conflicts found. Attempting to create a case...")
            cursor.execute(f"""
                    INSERT INTO ongoing_cases(patient_id, doctor_id, room_number)
                    VALUES ((SELECT patient_id FROM patient_info WHERE email = '{patient.email}'),
                    '{state["cache"]["doctor_assigned"][0]}',
                    '{state["cache"]["bed_assigned"][0][0]}');""")
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : Assigning available doctor and bed to {patient.name}")
            state["status"]["ConflictResolver"] = "Success"
            print(f"State print from CONFLICT :\n\n{state}")
        elif bed_status == "Success" and doctor_status == "Failed":
            debug("There's a conflict!! Doctor not available at this moment. Queuing the admission form...")
            # Release the bed that was alloted
            query = f"""
                UPDATE rooms SET is_occupied=FALSE WHERE room_number = {patient.assigned_bed};
            """
            cursor.execute(query)
            conn.commit()
            debug("Reverted the allocated bed...")
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : No doctors available at this moment. Queuing the application.")
            state["status"]["ConflictResolver"] = "Queued"
        elif bed_status == "Failed" and doctor_status == "Success":
            debug("There's a conflict!! Bed not available at this moment. Queuing the admission form...")
            # Release the doctor that was alloted
            query = f""""
                UPDATE doctors SET is_busy=FALSE, busy_from=NULL, busy_until=NULL WHERE doctor_id = {state["cache"]["doctor_assigned"][0]};
            """
            cursor.execute(query)
            conn.commit()
            debug("Reverted the allocated doctor...")
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : No beds available at this moment. Queuing the application.")
            state["status"]["ConflictResolver"] = "Queued"
        else:
            debug("There's a conflict!! No bed or doctor available at this moment. Please try at nearby hospitals...")
            state["logs"].append(f"[{get_current_time_with_ms()}] {self.__class__.__name__} : No beds and doctors available at this moment. Please try at nearby hospitals.")
            state["logs"].append(f"ConflictResolver: ")
            state["status"]["ConflictResolver"] = "Failed"
        
        if state["status"]["ConflictResolver"] == "Queued":
            query = f"""
                INSERT INTO queue VALUES (
                    (SELECT patient_id FROM patient_info WHERE email='{patient.email}'),
                    {patient.priority_score},
                    '{patient.bed_priority[0] if bed_status=="Failed" else state["cache"]["bed_assigned"][1][1]}'
                );
            """
            cursor.execute(query)
            conn.commit()
            debug("Application queued...")
            state["status"]["ConflictResolver"] = "Success"
        debug(f"Exiting {self.__class__.__name__} call...")
        return state