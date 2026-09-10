import sqlite3
import json
import os

class ClinicDatabase:
    def __init__(self, db_name="clinic_management.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Checks for database file; creates it and structures tables instantly if missing."""
        db_exists = os.path.exists(self.db_name)
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    weight REAL NOT NULL,
                    height REAL NOT NULL,
                    bmi REAL NOT NULL,
                    bmi_category TEXT NOT NULL,
                    bmr REAL NOT NULL,
                    triage_status TEXT NOT NULL,
                    vitals_json TEXT NULL
                )
            ''')
            conn.commit()
            
        if not db_exists:
            print(f"[SYSTEM INITIATED] Fresh database initialized file: '{self.db_name}'")
        else:
            print(f"[SYSTEM INITIATED] Connected to existing storage file: '{self.db_name}'")

    def save_patient(self, patient_data):
        """Inserts data and instantly writes/commits it onto the database disk file."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patients (name, age, gender, weight, height, bmi, bmi_category, bmr, triage_status, vitals_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_data["Name"], patient_data["Age"], patient_data["Gender"],
                patient_data["Weight"], patient_data["Height"], patient_data["BMI"],
                patient_data["BMI_Category"], patient_data["BMR"], patient_data["Triage"],
                json.dumps(patient_data["Vitals"])
            ))
            conn.commit()  # Forces an instant hard save to the database file
        print(f"[DATABASE SUCCESS] All metrics written and locked into '{self.db_name}' for {patient_data['Name']}.")

    def load_patients(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients ORDER BY triage_status ASC, id DESC")
            return self._parse_rows(cursor.fetchall())

    def search_patients_by_name(self, search_query):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE name LIKE ? ORDER BY triage_status ASC", (f"%{search_query}%",))
            return self._parse_rows(cursor.fetchall())

    def delete_patient(self, patient_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _parse_rows(self, rows):
        """Fixed helper to transform raw SQL database tuples using exact indices."""
        patients_list = []
        for row in rows:
            patients_list.append({
                "id": row[0],
                "Name": row[1],
                "Age": row[2],
                "Gender": row[3],
                "Weight": row[4],
                "Height": row[5],
                "BMI": row[6],
                "BMI_Category": row[7],
                "BMR": row[8],
                "Triage": row[9],
                "Vitals": json.loads(row[10])
            })
        return patients_list


# --- Clinical Calculation Logic ---

def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 25:
        category = "Normal weight"
    elif 25 <= bmi < 30:
        category = "Overweight"
    else:
        category = "Obesity"
    return round(bmi, 2), category

def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender.lower() == 'male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender.lower() == 'female':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 78
    return round(bmr, 2)

def assess_triage(heart_rate, resp_rate, spo2, systolic_bp):
    if spo2 < 85 or heart_rate < 40 or heart_rate > 140 or resp_rate < 8 or resp_rate > 35 or systolic_bp < 80:
        return "Level 1: Critical (Immediate)"
    elif (85 <= spo2 < 92) or (120 <= heart_rate <= 140) or (25 <= resp_rate <= 35) or (systolic_bp < 90 or systolic_bp > 180):
        return "Level 2: Emergent"
    elif (92 <= spo2 < 95) or (100 <= heart_rate < 120) or (20 <= resp_rate < 25) or (140 < systolic_bp <= 180):
        return "Level 3: Urgent"
    else:
        return "Level 4: Stable (Non-Urgent)"


# --- Interface Operations ---

def run_intake(db):
    print("\n=== Comprehensive Patient Intake ===")
    name = input("Full Name: ").strip()
    age = int(input("Age: ").strip())
    gender = input("Gender (Male/Female/Other): ").strip()
    weight = float(input("Weight (kg): ").strip())
    height = float(input("Height (cm): ").strip())
    
    print("\n--- Enter Current Vitals ---")
    hr = int(input("Heart Rate (bpm): ").strip())
    rr = int(input("Respiratory Rate (breaths/min): ").strip())
    spo2 = int(input("Oxygen Saturation (SpO2 %): ").strip())
    sbp = int(input("Systolic Blood Pressure (mmHg): ").strip())
    
    bmi, bmi_cat = calculate_bmi(weight, height)
    bmr = calculate_bmr(weight, height, age, gender)
    triage_status = assess_triage(hr, rr, spo2, sbp)
    
    record = {
        "Name": name, "Age": age, "Gender": gender, "Weight": weight, "Height": height,
        "BMI": bmi, "BMI_Category": bmi_cat, "BMR": bmr, "Triage": triage_status,
        "Vitals": {"HR": hr, "RR": rr, "SpO2": spo2, "SBP": sbp}
    }
    
    db.save_patient(record)

def print_patient_cards(patients):
    for p in patients:
        print(f"ID: {p['id']} | Name: {p['Name']} | Age: {p['Age']} | Gender: {p['Gender']}")
        print(f"  [STATUS]:  {p['Triage']}")
        print(f"  [VITALS]:  HR: {p['Vitals']['HR']} bpm | RR: {p['Vitals']['RR']}/min | SpO2: {p['Vitals']['SpO2']}% | SBP: {p['Vitals']['SBP']} mmHg")
        print(f"  [METRICS]: BMI: {p['BMI']} ({p['BMI_Category']}) | BMR: {p['BMR']} kcal/day")
        print("-" * 78)

def display_dashboard(db):
    patients = db.load_patients()
    print("\n================ Active Patient Dashboard (Sorted by Priority) ================")
    if not patients:
        print("No active records found in database.")
        return
    print_patient_cards(patients)

def run_search(db):
    print("\n=== Search Patient Records ===")
    query = input("Enter patient name to look up: ").strip()
    results = db.search_patients_by_name(query)
    
    print(f"\n--- Search Results for '{query}' ({len(results)} found) ---")
    if not results:
        print("No matching profiles found.")
        return
    print_patient_cards(results)

def run_discharge(db):
    print("\n=== Discharge Patient ===")
    try:
        pid = int(input("Enter Patient ID to discharge: ").strip())
        confirm = input(f"Are you sure you want to delete patient ID {pid}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            if db.delete_patient(pid):
                print(f"\n[Success] Patient ID {pid} has been successfully discharged and deleted.")
            else:
                print(f"\n[Error] No patient found with ID {pid}.")
        else:
            print("\nDischarge cancelled.")
    except ValueError:
        print("\n[Input Error] Please enter a valid numerical ID number.")


# --- Core Runner Loop ---

def main():
    db = ClinicDatabase()
    while True:
        print("\n=== Clinic Management Terminal ===")
        print("1. Process New Patient Intake")
        print("2. View Patient Dashboard (Queue)")
        print("3. Search for Patient Profile")
        print("4. Discharge Patient (Delete Record)")
        print("5. Exit System")
        choice = input("Select Option (1-5): ").strip()
        
        if choice == "1":
            try:
                run_intake(db)
            except ValueError:
                print("\n[Input Error] Check entries. Ensure stats are numerical numbers.")
        elif choice == "2":
            display_dashboard(db)
        elif choice == "3":
            run_search(db)
        elif choice == "4":
            run_discharge(db)
        elif choice == "5":
            print("Database session safely closed. Goodbye.")
            break
        else:
            print("Invalid system key. Choose a number from 1 to 5.")

if __name__ == "__main__":
    main()
