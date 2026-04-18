# VitalLink - Remote Chronic Care Telemedicine App

**Graphical Abstract**  
![Graphical Abstract](graphical_abstract.png)  
*(Single image showing: Patient wearing sensors → data flows to smartphone → cloud → Doctor on video call reviewing graphs → digital prescription. No hospital icon.)*

## Purpose of the Software
- **Software Development Process:** Agile (iterative sprints).  
- **Why Agile?** Flexible for a student group project; allows quick addition of sensor simulation, data visualization, and consultation features based on testing. Waterfall would be too linear and risky for evolving requirements.  
- **Possible usage / Target market:** Patients with chronic illnesses (diabetes, hypertension) in Macau who need frequent bio-stat monitoring. Doctors can review data remotely and prescribe medicine via the app, saving travel time to hospitals/clinics.

## Software Development Plan
### Development Process
Agile with 5 sprints (1 week each):  
1. Planning & DB setup  
2. Patient sensor input + data storage  
3. Doctor dashboard & charts  
4. Consultation & prescription module  
5. Testing, polishing, documentation

### Members (Roles & Responsibilities & Portion)
- **[Member 1 - e.g. Alan]**: Project Manager, Backend & Database (25%)  
- **[Member 2]**: UI/Streamlit Development & Visualization (25%)  
- **[Member 3]**: Sensor simulation, Algorithm & Alerts (25%)  
- **[Member 4]**: Testing, Documentation & Demo Video (25%)

### Schedule
- Week 1: Repo setup, DB, Agile planning  
- Week 2–3: Core features (patient/doctor views)  
- Week 4: Algorithm, consultation, testing  
- Week 5: Documentation, video recording, final submission

### Algorithm
Threshold-based health alert system:  
- Glucose > 180 mg/dL → "High" alert (red)  
- BP > 140/90 → "Hypertension" warning  
- Simple trend analysis (last 7 days average) using pandas.  
Alerts are shown to both patient and doctor automatically.

### Current Status of Your Software
Fully functional pilot (MVP). Patients can log mock sensor data and view history/charts. Doctors can review all patients, see alerts, and conduct simulated consultation with prescription. Runs locally with `streamlit run app.py`.

### Future Plan
- Real IoT sensor integration (Bluetooth/Raspberry Pi)  
- Full video call (WebRTC or Zoom API)  
- AI-based risk prediction (scikit-learn)  
- Cloud deployment (Streamlit Community Cloud or AWS)

## Demo (YouTube URL)
[Insert your 10-15 minute video link here after recording]

## Environments
- **Programming language:** Python 3.10+  
- **Minimum requirements:** Any laptop (no special HW).  
- **Required packages:** (see requirements.txt)  
- **How to run:** `pip install -r requirements.txt` then `streamlit run app.py`

## Declaration
All core code written by our group. We used the following open-source libraries (declared):  
- streamlit, pandas, plotly, sqlite3 (built-in)  
No other external code copied.
