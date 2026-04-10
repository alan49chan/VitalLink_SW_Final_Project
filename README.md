# SW_Final_Project

# Software Requirements Specification (SRS)  
**VitalLink – Remote Chronic Care Telemedicine App**

**Project Title:** VitalLink  
**Version:** 1.0 (Pilot / Demo Version with Login & History)  
**Date:** April 2026  
**Group Members:** [Insert your 4 names here]  
**Course:** COMP2116 Software Engineering  
**Macao Polytechnic University**

## 1. Introduction

### 1.1 Purpose
This document describes the functional and non-functional requirements of **VitalLink**, a Python-based telemedicine web application for patients with chronic illnesses (diabetes, hypertension). The system enables secure remote bio-stat monitoring, **login-protected access**, **live video consultation**, and digital prescriptions — eliminating frequent hospital visits.

### 1.2 Scope
**In Scope (Pilot Version):**  
- Patient-side mock sensor data collection and history visualization  
- Doctor-side real-time monitoring with alerts and trend analysis  
- **Login authentication** for both Patient and Doctor to protect privacy  
- **Live video and audio consultation** (Jitsi Meet WebRTC)  
- Electronic prescriptions with doctor suggestions/notes  
- **Patient can view full personal history** including all past prescriptions and doctor suggestions  
- Secure local database storage  

**Out of Scope (Future releases):**  
- Real IoT sensor integration  
- Cloud deployment and advanced authentication (e.g., JWT, OAuth)  
- AI predictive analytics  

### 1.3 Definitions, Acronyms, and Abbreviations
- **Bio-stat**: Blood glucose, blood pressure (systolic/diastolic), heart rate.  
- **Mock Sensor**: Simulated data entry.  
- **Live Video Consultation**: Real-time WebRTC via Jitsi Meet iframe.  
- **SRS**: Software Requirements Specification.

## 2. Overall Description

### 2.1 Product Perspective
VitalLink replaces physical clinic visits with a secure, privacy-protected remote system using login, live video, and full historical records of doctor suggestions.

### 2.2 Product Functions
- Login for privacy protection  
- Patient: input sensor data, view full history (bio-stats + prescriptions + doctor suggestions)  
- Doctor: monitor patients, conduct live video calls, issue prescriptions with suggestions  
- Persistent storage of all data

### 2.3 User Classes and Characteristics
| User Class     | Description                                      | Characteristics                          |
|----------------|--------------------------------------------------|------------------------------------------|
| Patient        | Chronic illness patient                          | Non-technical users needing privacy      |
| Doctor         | Registered physician                             | Medical professional                     |

### 2.4 Operating Environment
- **Platform**: Web browser with WebRTC support  
- **Programming Language**: Python 3.10+  
- **Framework**: Streamlit  
- **Database**: SQLite (`vitalink.db`)  
- **Video Call**: Embedded Jitsi Meet  
- **Hardware**: Standard laptop with webcam/microphone

### 2.5 Design and Implementation Constraints
- Entirely in **Python**  
- Simple login (username/password) for demo privacy protection  
- All data stored locally  
- Runnable with `streamlit run app.py`

### 2.6 Assumptions and Dependencies
- Demo credentials only (no real medical data)  
- Users have webcam/microphone for video call

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Authentication Module (New)
| ID     | Requirement                                                                 | Priority |
|--------|-----------------------------------------------------------------------------|----------|
| FR-A1  | Both Patient and Doctor must log in with username & password               | Must     |
| FR-A2  | Login protects access to personal data and consultation features            | Must     |
| FR-A3  | Session-based login (remains active during the app session)                 | Must     |

#### 3.1.2 Patient Module
| ID     | Requirement                                                                 | Priority |
|--------|-----------------------------------------------------------------------------|----------|
| FR-P1  | After login, enter mock sensor data                                         | Must     |
| FR-P2  | View personal bio-stat history                                              | Must     |
| FR-P3  | **View full history of past prescriptions and doctor suggestions**          | Must     |
| FR-P4  | Join live video consultation                                                | Must     |

#### 3.1.3 Doctor Module
| ID     | Requirement                                                                 | Priority |
|--------|-----------------------------------------------------------------------------|----------|
| FR-D1  | After login, view all patients                                              | Must     |
| FR-D2  | Generate health alerts and trend charts                                     | Must     |
| FR-D3  | Conduct live video consultation                                             | Must     |
| FR-D4  | Create prescription including medicine, dosage, **and suggestions/notes**   | Must     |

#### 3.1.4 Live Video Consultation Module
| ID     | Requirement                                                                 | Priority |
|--------|-----------------------------------------------------------------------------|----------|
| FR-V1  | Both roles can join the same Jitsi Meet room after login                   | Must     |

#### 3.1.5 System Functions
| ID     | Requirement                                                                 | Priority |
|--------|-----------------------------------------------------------------------------|----------|
| FR-S1  | All bio-stats and prescriptions stored persistently                         | Must     |
| FR-S2  | Patient can retrieve complete personal history                              | Must     |

### 3.2 Non-Functional Requirements
| Category          | Requirement                                                                 | Target       |
|-------------------|-----------------------------------------------------------------------------|--------------|
| Security          | Simple login to protect privacy (demo level)                                | High         |
| Usability         | Clear login screen + intuitive dashboards                                   | High         |
| Reliability       | All history data saved and retrievable                                      | Must         |
| Performance       | Login < 2s, charts and video load instantly                                 | High         |

### 3.3 Algorithm Requirements
- Health alerts (same as before)  
- History retrieval using SQL queries filtered by logged-in patient name

## 4. Appendix

### 4.1 Graphical Abstract
*(Update your image to show: Login screen → Patient/Doctor dashboard → Live video + History tab with prescriptions & suggestions)*

### 4.2 Traceability
All new requirements (FR-A1~A3, FR-P3) are implemented in `app.py` v1.0.

---

**End of SRS Document v1.2**




