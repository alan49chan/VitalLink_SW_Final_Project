
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import hashlib
from streamlit_cookies_controller import CookieController
import time   # ← Added for more reliable logout

# ====================== IMPORTANT ======================
# 1. Make sure you have installed the cookie package:
#    pip install streamlit-cookies-controller
# 2. DELETE old vitalink.db for a clean test (schema has changed)

# ====================== VITAL THRESHOLDS ======================
VITAL_THRESHOLDS = {
    "heart_rate": {"normal_low": 60, "normal_high": 100, "mild_low": 50, "mild_high": 110, "unit": "bpm", "label": "Heart Rate"},
    "systolic_bp": {"normal_low": 90, "normal_high": 140, "mild_low": 80, "mild_high": 159, "unit": "mmHg", "label": "Systolic BP"},
    "diastolic_bp": {"normal_low": 60, "normal_high": 90, "mild_low": 50, "mild_high": 99, "unit": "mmHg", "label": "Diastolic BP"},
    "temperature": {"normal_low": 36.0, "normal_high": 37.5, "mild_low": 35.0, "mild_high": 38.5, "unit": "°C", "label": "Temperature"},
    "oxygen_sat": {"normal_low": 95, "normal_high": 100, "mild_low": 92, "mild_high": 94, "unit": "%", "label": "Oxygen Saturation"},
    "blood_glucose": {"normal_low": 3.9, "normal_high": 7.8, "mild_low": 2.8, "mild_high": 10.0, "unit": "mmol/L", "label": "Blood Glucose"}
}


ROOM_ID = "vitalink-demo-room"

def get_video_html_code(role):
    remote_title = "🧑‍🦰 Patient Video" if role == "Doctor" else "👨‍⚕️ Doctor Video"

    html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
                <style>
                    video {{ width: 100%; max-height: 420px; background: #111; border-radius: 8px; }}
                    .container {{ display: flex; gap: 15px; flex-wrap: wrap; margin-top: 20px; }}
                    button {{ padding: 12px 30px; font-size: 18px; margin: 10px 0; }}
                    .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                    .status-info {{ background: #e3f2fd; color: #0d47a1; }}
                    .status-error {{ background: #ffebee; color: #c62828; }}
                    .status-success {{ background: #e8f5e9; color: #2e7d32; }}
                </style>
            </head>
            <body>
                <div>
                    <button id="joinBtn">🎥 Join Video Call</button>
                    <button id="leaveBtn" style="display:none;">❌ Leave Call</button>
                    <div id="connectionStatus" class="status status-info">⚪ Not connected</div>
                </div>
                <div class="container">
                    <div style="flex:1">
                        <h4>📷 My Camera</h4>
                        <video id="localVideo" autoplay muted playsinline></video>
                    </div>
                    <div style="flex:1">
                        <h4>{remote_title}</h4>
                        <video id="remoteVideo" autoplay playsinline></video>
                    </div>
                </div>

                <script>
                    // Configuration
                    const SOCKET_URL = "https://jojo988.com";
                    const socket = io(SOCKET_URL, {{
                        transports: ['websocket', 'polling'],
                        reconnection: true,
                        reconnectionAttempts: 5
                    }});

                    let localStream = null;
                    let peerConnection = null;
                    let currentTargetSocketId = null;
                    let isInitiator = false;

                    const roomId = "{ROOM_ID}";
                    const userName = "{role}";

                    const iceServers = [
                        {{ urls: 'stun:stun.l.google.com:19302' }},
                        {{ urls: 'stun:stun1.l.google.com:19302' }},
                        {{ urls: 'stun:stun2.l.google.com:19302' }},
                        {{ urls: 'stun:stun3.l.google.com:19302' }},
                        {{ urls: 'stun:stun4.l.google.com:19302' }},
                        {{
                            urls: 'turn:turn.jojo988.com:3478',
                            username: 'paul',
                            credential: '66801224'
                        }},
                        {{
                            urls: 'turns:jojo988.com:5349',
                            username: 'paul',
                            credential: '66801224'
                        }}
                    ];

                    function updateStatus(message, type = 'info') {{
                        const statusDiv = document.getElementById('connectionStatus');
                        statusDiv.textContent = message;
                        statusDiv.className = `status status-${{type}}`;
                        console.log(`[Status] ${{message}}`);
                    }}

                    function createPeerConnection() {{
                        if (peerConnection) {{
                            peerConnection.close();
                        }}

                        peerConnection = new RTCPeerConnection({{ iceServers }});

                        // Handle ICE candidates
                        peerConnection.onicecandidate = (event) => {{
                            if (event.candidate && currentTargetSocketId) {{
                                console.log('📡 Sending ICE candidate');
                                socket.emit("ice-candidate", {{
                                    targetSocketId: currentTargetSocketId,
                                    candidate: event.candidate
                                }});
                            }}
                        }};

                        // Handle remote stream
                        peerConnection.ontrack = (event) => {{
                            console.log('🎥 Received remote stream');
                            const remoteVideo = document.getElementById("remoteVideo");
                            remoteVideo.srcObject = event.streams[0];
                            updateStatus('Connected to peer!', 'success');
                        }};

                        // Handle connection state changes
                        peerConnection.onconnectionstatechange = () => {{
                            console.log(`🔌 Connection state: ${{peerConnection.connectionState}}`);
                            if (peerConnection.connectionState === 'connected') {{
                                updateStatus('✅ Video call connected!', 'success');
                            }} else if (peerConnection.connectionState === 'failed') {{
                                updateStatus('❌ Connection failed - check TURN server', 'error');
                            }} else if (peerConnection.connectionState === 'disconnected') {{
                                updateStatus('⚠️ Connection lost', 'error');
                            }}
                        }};

                        // Handle ICE connection state
                        peerConnection.oniceconnectionstatechange = () => {{
                            console.log(`🧊 ICE state: ${{peerConnection.iceConnectionState}}`);
                            if (peerConnection.iceConnectionState === 'connected') {{
                                console.log('✅ ICE connected - direct or TURN');
                            }} else if (peerConnection.iceConnectionState === 'failed') {{
                                console.log('❌ ICE failed');
                            }}
                        }};

                        // Add local stream tracks if available
                        if (localStream) {{
                            localStream.getTracks().forEach(track => {{
                                peerConnection.addTrack(track, localStream);
                            }});
                        }}

                        return peerConnection;
                    }}

                    async function initCall() {{
                        const joinBtn = document.getElementById("joinBtn");
                        const leaveBtn = document.getElementById("leaveBtn");

                        joinBtn.disabled = true;
                        joinBtn.textContent = "🎥 Requesting camera...";
                        updateStatus('Requesting camera/microphone access...', 'info');

                        try {{
                            // Get user media
                            localStream = await navigator.mediaDevices.getUserMedia({{
                                video: true,
                                audio: true
                            }});
                            document.getElementById("localVideo").srcObject = localStream;
                            updateStatus('✅ Camera ready, joining room...', 'success');

                            // Create peer connection
                            createPeerConnection();

                            // Join room
                            socket.emit("join-room", {{ roomId, userName }});
                            updateStatus('📡 Connecting to signaling server...', 'info');

                            joinBtn.style.display = 'none';
                            leaveBtn.style.display = 'inline-block';

                        }} catch (err) {{
                            console.error('Camera error:', err);
                            updateStatus('❌ Cannot access camera/microphone. Please check permissions.', 'error');
                            joinBtn.disabled = false;
                            joinBtn.textContent = '🎥 Join Video Call';
                        }}
                    }}

                    function leaveCall() {{
                        updateStatus('Disconnecting...', 'info');

                        if (peerConnection) {{
                            peerConnection.close();
                            peerConnection = null;
                        }}

                        if (localStream) {{
                            localStream.getTracks().forEach(track => track.stop());
                            localStream = null;
                        }}

                        document.getElementById("localVideo").srcObject = null;
                        document.getElementById("remoteVideo").srcObject = null;

                        socket.emit("leave-room");

                        const joinBtn = document.getElementById("joinBtn");
                        const leaveBtn = document.getElementById("leaveBtn");
                        joinBtn.style.display = 'inline-block';
                        leaveBtn.style.display = 'none';
                        joinBtn.disabled = false;
                        joinBtn.textContent = '🎥 Join Video Call';

                        currentTargetSocketId = null;
                        isInitiator = false;
                        updateStatus('⚪ Disconnected', 'info');
                    }}

                    // Socket event handlers
                    socket.on('connect', () => {{
                        console.log('✅ Connected to signaling server');
                        updateStatus('Connected to server', 'success');
                    }});

                    socket.on('disconnect', () => {{
                        console.log('❌ Disconnected from signaling server');
                        updateStatus('Disconnected from server', 'error');
                    }});

                    socket.on('existing-users', async (users) => {{
                        console.log('Existing users in room:', users);
                        if (users.length > 0 && peerConnection && !currentTargetSocketId) {{
                            // Connect to the first user
                            currentTargetSocketId = users[0].socketId;
                            isInitiator = true;
                            updateStatus('Creating connection to peer...', 'info');

                            try {{
                                const offer = await peerConnection.createOffer();
                                await peerConnection.setLocalDescription(offer);
                                socket.emit("offer", {{
                                    targetSocketId: currentTargetSocketId,
                                    offer: peerConnection.localDescription
                                }});
                                updateStatus('Offer sent, waiting for answer...', 'info');
                            }} catch (err) {{
                                console.error('Error creating offer:', err);
                                updateStatus('Error creating connection', 'error');
                            }}
                        }}
                    }});

                    socket.on('user-joined', async (data) => {{
                        console.log('New user joined:', data);
                        if (!currentTargetSocketId && peerConnection && isInitiator) {{
                            currentTargetSocketId = data.socketId;
                            updateStatus('New peer joined, connecting...', 'info');

                            try {{
                                const offer = await peerConnection.createOffer();
                                await peerConnection.setLocalDescription(offer);
                                socket.emit("offer", {{
                                    targetSocketId: currentTargetSocketId,
                                    offer: peerConnection.localDescription
                                }});
                            }} catch (err) {{
                                console.error('Error creating offer for new user:', err);
                            }}
                        }}
                    }});

                    socket.on('offer', async (data) => {{
                        console.log('📞 Received offer from:', data.senderSocketId);
                        if (!peerConnection) {{
                            createPeerConnection();
                        }}

                        currentTargetSocketId = data.senderSocketId;
                        isInitiator = false;

                        try {{
                            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
                            const answer = await peerConnection.createAnswer();
                            await peerConnection.setLocalDescription(answer);
                            socket.emit("answer", {{
                                targetSocketId: currentTargetSocketId,
                                answer: peerConnection.localDescription
                            }});
                            updateStatus('Answer sent, establishing connection...', 'info');
                        }} catch (err) {{
                            console.error('Error handling offer:', err);
                            updateStatus('Error handling connection', 'error');
                        }}
                    }});

                    socket.on('answer', async (data) => {{
                        console.log('📞 Received answer from:', data.senderSocketId);
                        try {{
                            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
                            updateStatus('Connection established!', 'success');
                        }} catch (err) {{
                            console.error('Error handling answer:', err);
                        }}
                    }});

                    socket.on('ice-candidate', async (data) => {{
                        console.log('🧊 Received ICE candidate');
                        if (peerConnection && data.candidate) {{
                            try {{
                                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
                            }} catch (err) {{
                                console.error('Error adding ICE candidate:', err);
                            }}
                        }}
                    }});

                    socket.on('user-left', (data) => {{
                        console.log('User left:', data);
                        if (currentTargetSocketId === data.socketId) {{
                            updateStatus('Peer disconnected', 'info');
                            currentTargetSocketId = null;
                            isInitiator = false;

                            // Reset remote video
                            document.getElementById("remoteVideo").srcObject = null;
                        }}
                    }});

                    // Setup button handlers
                    document.getElementById("joinBtn").addEventListener("click", initCall);
                    document.getElementById("leaveBtn").addEventListener("click", leaveCall);
                </script>
            </body>
            </html>
            """
    return html_code

def get_separate_vital_alerts(df):
    if df.empty:
        return []
    alerts = []
    df = df.copy()
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])

    for _, row in df.iterrows():
        ts_str = row['recorded_at'].strftime("%Y-%m-%d %H:%M")
        for col, config in VITAL_THRESHOLDS.items():
            if col in row and pd.notna(row[col]):
                value = float(row[col])
                normal_low = config["normal_low"]
                normal_high = config["normal_high"]
                mild_low = config["mild_low"]
                mild_high = config["mild_high"]
                unit = config["unit"]
                label = config["label"]

                if value < normal_low or value > normal_high:
                    severity = "severe" if (value < mild_low or value > mild_high) else "mild"
                    emoji = "🔴" if severity == "severe" else "🟡"
                    message = f"{emoji} **{ts_str}** — **{label}**: {value} {unit} "
                    message += f"(LOW — normal {normal_low}-{normal_high})" if value < normal_low else f"(HIGH — normal {normal_low}-{normal_high})"
                    alerts.append({"timestamp": ts_str, "severity": severity, "message": message})

    alerts.sort(key=lambda x: x["timestamp"], reverse=True)
    return alerts

# ====================== DATABASE SETUP ======================
conn = sqlite3.connect('vitalink.db', check_same_thread=False)
c = conn.cursor()
c.execute("PRAGMA foreign_keys = ON;")

c.execute('''CREATE TABLE IF NOT EXISTS auth_users (
    username TEXT PRIMARY KEY, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Patient', 'Doctor')),
    profile_complete INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS doctors (
    username TEXT PRIMARY KEY, full_name TEXT NOT NULL, specialty TEXT, license_number TEXT UNIQUE,
    email TEXT UNIQUE NOT NULL, phone TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES auth_users(username) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE IF NOT EXISTS clients (
    username TEXT PRIMARY KEY, full_name TEXT NOT NULL, date_of_birth DATE,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')), email TEXT UNIQUE NOT NULL,
    phone TEXT, address TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES auth_users(username) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE IF NOT EXISTS medicines (
    medicine_id INTEGER PRIMARY KEY AUTOINCREMENT, drug_name TEXT NOT NULL, generic_name TEXT,
    dosage_form TEXT, strength TEXT, manufacturer TEXT, stock_quantity INTEGER DEFAULT 0,
    unit_price REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS history (
    doctor_username TEXT NOT NULL, client_username TEXT NOT NULL, visit_date DATE NOT NULL,
    line_number INTEGER NOT NULL DEFAULT 1, diagnosis TEXT, symptoms TEXT, notes TEXT,
    medicine_id INTEGER, quantity INTEGER, instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doctor_username, client_username, visit_date, line_number),
    FOREIGN KEY (doctor_username) REFERENCES doctors(username),
    FOREIGN KEY (client_username) REFERENCES clients(username),
    FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS vitals (
    vital_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_username TEXT NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    height_cm REAL,
    weight_kg REAL,
    heart_rate INTEGER,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    temperature REAL,
    oxygen_sat INTEGER,
    blood_glucose REAL,
    notes TEXT,
    FOREIGN KEY (client_username) REFERENCES clients(username)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_username TEXT NOT NULL, doctor_username TEXT NOT NULL,
    requested_date DATE NOT NULL, status TEXT DEFAULT 'Pending',
    notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_username) REFERENCES clients(username),
    FOREIGN KEY (doctor_username) REFERENCES doctors(username)
)''')

conn.commit()

# ====================== HELPERS ======================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# ====================== COOKIE CONTROLLER ======================
cookie_controller = CookieController()

st.set_page_config(page_title="VitalLink", page_icon="🩺", layout="wide")
st.title("🩺 VitalLink - Remote Chronic Care")

# ====================== ROBUST COOKIE AUTO-LOGIN ======================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    username_from_cookie = cookie_controller.get('vitalink_username')
    if username_from_cookie:
        c.execute('SELECT role, profile_complete FROM auth_users WHERE username = ?',
                  (username_from_cookie,))
        data = c.fetchone()
        if data:
            st.session_state.logged_in = True
            st.session_state.username = username_from_cookie
            st.session_state.user_role = data[0]
            st.session_state.profile_complete = bool(data[1])
            st.rerun()

# ====================== LOGIN / REGISTER ======================
if not st.session_state.get('logged_in', False):
    st.sidebar.subheader("🔐 Login / Registration")
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Select Action", menu)

    if choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute('SELECT password, role, profile_complete FROM auth_users WHERE username = ?',
                      (username,))
            data = c.fetchone()
            if data and check_hashes(password, data[0]):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_role = data[1]
                st.session_state.profile_complete = bool(data[2])

                expires_date = datetime.now() + timedelta(days=30)
                cookie_controller.set('vitalink_username', username, expires=expires_date)

                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    elif choice == "Register":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Patient", "Doctor"])

        if st.button("Register"):
            c.execute('SELECT * FROM auth_users WHERE username = ?', (new_user,))
            if c.fetchone():
                st.warning("Username already exists.")
            else:
                c.execute('INSERT INTO auth_users (username, password, role, profile_complete) VALUES (?,?,?,0)',
                          (new_user, make_hashes(new_password), role))
                conn.commit()

                st.session_state.logged_in = True
                st.session_state.username = new_user
                st.session_state.user_role = role
                st.session_state.profile_complete = False

                expires_date = datetime.now() + timedelta(days=30)
                cookie_controller.set('vitalink_username', new_user, expires=expires_date)

                st.success(f"✅ Account created successfully! Welcome, {new_user}!")
                st.info("Please complete your profile below.")
                st.rerun()

else:
    # ====================== LOGGED IN ======================
    username = st.session_state.username
    role = st.session_state.user_role

    st.sidebar.write(f"Logged in as: **{username}** ({role})")

    expires_date = datetime.now() + timedelta(days=30)
    cookie_controller.set('vitalink_username', username, expires=expires_date)

    # ====================== FIXED LOGOUT (This solves the issue) ======================
    if st.sidebar.button("🚪 Logout", type="secondary"):
        # 1. Remove cookie immediately
        cookie_controller.remove('vitalink_username')

        # 2. Clear ALL session state
        st.session_state.clear()

        # 3. Show success message
        st.success("✅ You have been logged out successfully!")

        # 4. Small delay so browser can process cookie removal
        time.sleep(0.3)

        # 5. Force rerun — now the top-level auto-login will NOT find the cookie
        st.rerun()

    # ====================== PROFILE COMPLETION ======================
    if not st.session_state.profile_complete:
        st.header("Complete Your Profile")
        if role == "Doctor":
            full_name = st.text_input("Full Name")
            specialty = st.text_input("Specialty")
            license_number = st.text_input("License Number")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            if st.button("Save Doctor Profile"):
                c.execute('''INSERT INTO doctors (username, full_name, specialty, license_number, email, phone)
                             VALUES (?,?,?,?,?,?)''',
                          (username, full_name, specialty, license_number, email, phone))
                c.execute('UPDATE auth_users SET profile_complete = 1 WHERE username = ?', (username,))
                conn.commit()
                st.session_state.profile_complete = True
                st.success("Doctor profile saved!")
                st.rerun()
        else:
            full_name = st.text_input("Full Name")
            dob = st.date_input("Date of Birth", value=date(1990, 1, 1))
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            address = st.text_area("Address")
            if st.button("Save Patient Profile"):
                c.execute('''INSERT INTO clients (username, full_name, date_of_birth, gender, email, phone, address)
                             VALUES (?,?,?,?,?,?,?)''',
                          (username, full_name, dob, gender, email, phone, address))
                c.execute('UPDATE auth_users SET profile_complete = 1 WHERE username = ?', (username,))
                conn.commit()
                st.session_state.profile_complete = True
                st.success("Patient profile saved!")
                st.rerun()
        st.stop()

    # ====================== PATIENT & DOCTOR DASHBOARDS (unchanged) ======================
    # ... [All the rest of your dashboard code remains exactly the same as the previous version] ...
    # (I kept it identical to the last working version you had)

    if role == "Patient":
        st.header(f"🧑‍🦰 Patient Dashboard - Welcome, {username}")
        tab1, tab2, tab3, tab4 = st.tabs(["👨‍⚕️ Choose Doctor & Request Meeting",
                                          "📡 Input Vitals",
                                          "📋 My Appointments",
                                          "📈 My Health History"])

        with tab1:
            st.subheader("Choose Doctor and Request Meeting")
            doctors_df = pd.read_sql("SELECT username, full_name, specialty FROM doctors ORDER BY full_name", conn)
            if doctors_df.empty:
                st.warning("No doctors registered yet.")
            else:
                doctor_options = [f"{row['full_name']} ({row['specialty']})" for _, row in doctors_df.iterrows()]
                doctor_map = dict(zip(doctor_options, doctors_df['username']))
                selected = st.selectbox("Select Doctor", doctor_options)
                doctor_username_sel = doctor_map[selected]

                req_date = st.date_input("Preferred Date", date.today())
                req_notes = st.text_area("Reason for consultation (optional)")

                if st.button("Request Video Meeting", type="primary"):
                    try:
                        c.execute("""INSERT INTO appointments (client_username, doctor_username, requested_date, notes)
                                     VALUES (?,?,?,?)""",
                                  (username, doctor_username_sel, req_date, req_notes))
                        conn.commit()
                        st.success("✅ Appointment request sent successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

                html_code = get_video_html_code(role)
                            # Display WebRTC component
                st.components.v1.html(html_code, height=700, width='stretch')

        with tab2:
            st.subheader("📡 Input Vitals")
            col1, col2 = st.columns(2)
            with col1:
                height = st.number_input("Height (cm)", 100.0, 250.0, 170.0)
                weight = st.number_input("Weight (kg)", 30.0, 300.0, 70.0)
                glucose = st.number_input("Blood Glucose (mmol/L)", 1.0, 25.0, 5.0)
            with col2:
                hr = st.number_input("Heart Rate (bpm)", 40, 200, 75)
                sys = st.number_input("Systolic BP", 80, 220, 130)
                dia = st.number_input("Diastolic BP", 50, 140, 85)
                temp = st.number_input("Temperature (°C)", 35.0, 42.0, 36.5)
                o2 = st.number_input("Oxygen Saturation (%)", 70, 100, 98)
            v_notes = st.text_area("Notes (optional)")
            if st.button("Submit Vitals"):
                ts = datetime.now()
                c.execute('''INSERT INTO vitals (client_username, recorded_at, height_cm, weight_kg, heart_rate,
                             systolic_bp, diastolic_bp, temperature, oxygen_sat, blood_glucose, notes)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                          (username, ts, height, weight, hr, sys, dia, temp, o2, glucose, v_notes))
                conn.commit()
                st.success("Vitals recorded!")

        with tab3:
            st.subheader("My Appointments")
            apps = pd.read_sql(f'''
                SELECT a.requested_date, d.full_name as doctor, a.status, a.notes
                FROM appointments a
                JOIN doctors d ON a.doctor_username = d.username
                WHERE a.client_username = '{username}'
                ORDER BY a.created_at DESC
            ''', conn)
            st.dataframe(apps if not apps.empty else pd.DataFrame())

        with tab4:
            st.subheader("My Health History")
            vitals_df = pd.read_sql(f"SELECT * FROM vitals WHERE client_username='{username}' ORDER BY recorded_at DESC", conn)
            history_df = pd.read_sql(f'''
                SELECT h.visit_date, h.diagnosis, m.drug_name, h.quantity, h.instructions
                FROM history h
                LEFT JOIN medicines m ON h.medicine_id = m.medicine_id
                WHERE h.client_username = '{username}'
                ORDER BY h.visit_date DESC
            ''', conn)
            if not vitals_df.empty:
                st.dataframe(vitals_df, use_container_width=True)
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True)
            if vitals_df.empty and history_df.empty:
                st.info("No records yet.")

            st.subheader("🚨 Vital Alerts")
            alerts = get_separate_vital_alerts(vitals_df)
            if alerts:
                for alert in alerts:
                    if alert["severity"] == "severe":
                        st.error(alert["message"])
                    else:
                        st.warning(alert["message"])
            else:
                st.success("✅ All recent vitals are within normal range.")

            st.subheader("📈 Vital Signs Trends")
            if not vitals_df.empty:
                plot_df = vitals_df.copy()
                plot_df['recorded_at'] = pd.to_datetime(plot_df['recorded_at'])
                view_mode = st.selectbox("View graph by", ["Daily", "Monthly", "Yearly"], key="patient_graph")
                key_vitals = ['weight_kg', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'blood_glucose', 'temperature']
                # if view_mode == "Daily":
                #     # Find the last record date
                #     last_record_date = plot_df['recorded_at'].max()
                #     # Calculate the date 30 days before the last record
                #     cutoff_date = last_record_date - pd.Timedelta(days=30)
                #     # Filter data to last 30 days
                #     plot_df_filtered = plot_df[plot_df['recorded_at'] >= cutoff_date].copy()

                #     grouped = plot_df_filtered.groupby(plot_df_filtered['recorded_at'].dt.date)[key_vitals].mean()
                #     grouped.index = pd.to_datetime(grouped.index)
                # elif view_mode == "Monthly":
                #     grouped = plot_df.groupby(plot_df['recorded_at'].dt.to_period('M'))[key_vitals].mean()
                #     grouped.index = grouped.index.to_timestamp()
                # elif view_mode == "Yearly":
                #     grouped = plot_df.groupby(plot_df['recorded_at'].dt.to_period('Y'))[key_vitals].mean()
                #     grouped.index = grouped.index.to_timestamp()
                # st.line_chart(grouped, use_container_width=True, height=400)
                if view_mode == "Daily":
                    # Find the last record date
                    last_record_date = plot_df['recorded_at'].max()
                    # Calculate the date 30 days before the last record
                    cutoff_date = last_record_date - pd.Timedelta(days=30)
                    # Filter data to last 30 days
                    plot_df_filtered = plot_df[plot_df['recorded_at'] >= cutoff_date].copy()

                    grouped = plot_df_filtered.groupby(plot_df_filtered['recorded_at'].dt.date)[key_vitals].mean()
                    grouped.index = pd.to_datetime(grouped.index)

                    # Format x-axis to show MM-DD
                    grouped_display = grouped.copy()
                    grouped_display.index = grouped_display.index.strftime('%m-%d')
                    st.line_chart(grouped_display, use_container_width=True, height=400)

                elif view_mode == "Monthly":
                    # Find the last record date
                    last_record_date = plot_df['recorded_at'].max()
                    # Calculate the date 12 months before the last record
                    cutoff_date = last_record_date - pd.DateOffset(months=12)
                    # Filter data to last 12 months
                    plot_df_filtered = plot_df[plot_df['recorded_at'] >= cutoff_date].copy()

                    # Group by month and calculate mean
                    grouped = plot_df_filtered.groupby(plot_df_filtered['recorded_at'].dt.to_period('M'))[key_vitals].mean()
                    grouped.index = grouped.index.to_timestamp()

                    # Format x-axis to show YYYY-MM
                    grouped_display = grouped.copy()
                    grouped_display.index = grouped_display.index.strftime('%Y-%m')
                    st.line_chart(grouped_display, use_container_width=True, height=400)

                elif view_mode == "Yearly":
                    # Find the last record date
                    last_record_date = plot_df['recorded_at'].max()
                    # Calculate the date 5 years before the last record (or use all data)
                    cutoff_date = last_record_date - pd.DateOffset(years=5)
                    # Filter data to last 5 years
                    plot_df_filtered = plot_df[plot_df['recorded_at'] >= cutoff_date].copy()

                    # Group by year and calculate mean
                    grouped = plot_df_filtered.groupby(plot_df_filtered['recorded_at'].dt.to_period('Y'))[key_vitals].mean()
                    grouped.index = grouped.index.to_timestamp()

                    # Format x-axis to show YYYY
                    grouped_display = grouped.copy()
                    grouped_display.index = grouped_display.index.strftime('%Y')
                    st.line_chart(grouped_display, use_container_width=True, height=400)

    else:  # Doctor
        st.header(f"👨‍⚕️ Doctor Dashboard - Dr. {username}")
        tab1, tab2, tab3, tab4 = st.tabs(["📬 Appointment Requests",
                                          "👥 My Patients & Prescribe",
                                          "💊 Manage Medicines",
                                          "📹 Video Consultation"])

        with tab1:
            st.subheader("Pending Appointment Requests")
            pending = pd.read_sql(f'''
                SELECT a.appointment_id, c.full_name as patient, a.requested_date, a.notes
                FROM appointments a
                JOIN clients c ON a.client_username = c.username
                WHERE a.doctor_username = '{username}' AND a.status = 'Pending'
            ''', conn)
            if not pending.empty:
                for _, row in pending.iterrows():
                    with st.expander(f"{row['patient']} - {row['requested_date']}"):
                        st.write(f"**Notes:** {row.get('notes', 'None')}")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Accept", key=f"acc_{row['appointment_id']}"):
                            c.execute("UPDATE appointments SET status='Accepted' WHERE appointment_id=?", (row['appointment_id'],))
                            conn.commit()
                            st.success("Accepted!")
                            st.rerun()
                        if c2.button("❌ Reject", key=f"rej_{row['appointment_id']}"):
                            c.execute("UPDATE appointments SET status='Rejected' WHERE appointment_id=?", (row['appointment_id'],))
                            conn.commit()
                            st.success("Rejected.")
                            st.rerun()
            else:
                st.info("No pending requests.")

        with tab2:
            st.subheader("My Patients")
            patients_df = pd.read_sql(f'''
                SELECT DISTINCT c.username, c.full_name
                FROM clients c
                JOIN appointments a ON c.username = a.client_username
                WHERE a.doctor_username = '{username}'
            ''', conn)
            if not patients_df.empty:
                selected_patient = st.selectbox("Select Patient", patients_df['full_name'])
                client_username_sel = patients_df[patients_df['full_name'] == selected_patient]['username'].iloc[0]

                vitals_df = pd.read_sql(f"SELECT * FROM vitals WHERE client_username='{client_username_sel}' ORDER BY recorded_at DESC LIMIT 30", conn)
                if not vitals_df.empty:
                    st.dataframe(vitals_df, use_container_width=True)

                    st.subheader("🚨 Patient Vital Alerts")
                    alerts = get_separate_vital_alerts(vitals_df)
                    if alerts:
                        for alert in alerts:
                            if alert["severity"] == "severe":
                                st.error(alert["message"])
                            else:
                                st.warning(alert["message"])
                    else:
                        st.success("✅ All recent vitals are within normal range.")

                    st.subheader("📈 Patient Vital Signs Trends (Monthly)")
                    plot_df = vitals_df.copy()
                    plot_df['recorded_at'] = pd.to_datetime(plot_df['recorded_at'])
                    key_vitals = ['weight_kg', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'blood_glucose', 'temperature']
                    grouped = plot_df.groupby(plot_df['recorded_at'].dt.to_period('M'))[key_vitals].mean()
                    grouped.index = grouped.index.to_timestamp()
                    st.line_chart(grouped, use_container_width=True, height=400)

                st.subheader("📋 Patient Prescription History")
                time_option = st.selectbox("Show prescriptions from:",
                                         ["All records", "Last 30 days", "Last 90 days", "Last 6 months", "This year"],
                                         key="doctor_history_filter")
                base_query = '''
                    SELECT h.visit_date, h.diagnosis, h.symptoms, m.drug_name, h.quantity, h.instructions, h.notes
                    FROM history h LEFT JOIN medicines m ON h.medicine_id = m.medicine_id
                    WHERE h.client_username = ?
                '''
                params = [client_username_sel]
                if time_option == "Last 30 days": base_query += " AND h.visit_date >= date('now', '-30 days')"
                elif time_option == "Last 90 days": base_query += " AND h.visit_date >= date('now', '-90 days')"
                elif time_option == "Last 6 months": base_query += " AND h.visit_date >= date('now', '-6 months')"
                elif time_option == "This year": base_query += " AND strftime('%Y', h.visit_date) = strftime('%Y', 'now')"
                base_query += " ORDER BY h.visit_date DESC"
                history_df = pd.read_sql(base_query, conn, params=params)
                if not history_df.empty:
                    st.dataframe(history_df, use_container_width=True)
                else:
                    st.info("No prescription records found.")

                st.divider()
                st.subheader("💊 New Consultation & Prescription")
                visit_date = st.date_input("Visit Date", datetime.now().date())
                diagnosis = st.text_input("Diagnosis")
                symptoms = st.text_area("Symptoms")
                notes = st.text_area("Notes")

                meds_df = pd.read_sql("SELECT medicine_id, drug_name FROM medicines ORDER BY drug_name", conn)
                med_options = ["[Free Text]"] + list(meds_df['drug_name']) if not meds_df.empty else ["[Free Text]"]
                selected_med = st.selectbox("Medicine", med_options)

                if selected_med == "[Free Text]":
                    med_name = st.text_input("Medicine Name")
                    med_id = None
                else:
                    med_name = selected_med
                    med_map = dict(zip(meds_df['drug_name'], meds_df['medicine_id']))
                    med_id = med_map.get(selected_med)

                qty = st.number_input("Quantity", min_value=1, value=30)
                instructions = st.text_input("Instructions")

                if st.button("Save Consultation & Prescription"):
                    if not diagnosis or not med_name:
                        st.error("Diagnosis and medicine name are required.")
                        st.stop()

                    c.execute("SELECT 1 FROM doctors WHERE username = ?", (username,))
                    if not c.fetchone():
                        st.error("❌ Your doctor profile is missing.")
                        st.stop()

                    c.execute("SELECT 1 FROM clients WHERE username = ?", (client_username_sel,))
                    if not c.fetchone():
                        st.error("❌ Selected patient profile not found.")
                        st.stop()

                    if med_id is not None:
                        c.execute("SELECT medicine_id FROM medicines WHERE drug_name = ?", (med_name,))
                        row = c.fetchone()
                        if row:
                            med_id = row[0]
                        else:
                            st.error(f"❌ Medicine '{med_name}' no longer exists in the database.")
                            st.stop()

                    try:
                        c.execute('''INSERT INTO history
                                     (doctor_username, client_username, visit_date, line_number,
                                      diagnosis, symptoms, notes, medicine_id, quantity, instructions)
                                     VALUES (?,?,?,?,?,?,?,?,?,?)''',
                                  (username, client_username_sel, visit_date, 1,
                                   diagnosis, symptoms, notes, med_id, qty, instructions))
                        conn.commit()
                        st.success(f"✅ Prescription for {med_name} saved successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"❌ Database error: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)}")

        with tab3:
            st.subheader("💊 Manage Medicines")
            with st.expander("➕ Add New Medicine"):
                with st.form("add_med"):
                    drug = st.text_input("Drug Name *")
                    generic = st.text_input("Generic Name")
                    form = st.text_input("Dosage Form")
                    strength = st.text_input("Strength")
                    manu = st.text_input("Manufacturer")
                    stock = st.number_input("Stock Quantity", 0, 10000, 100)
                    price = st.number_input("Unit Price", 0.0, format="%.2f")
                    if st.form_submit_button("Add Medicine"):
                        if drug:
                            c.execute('''INSERT INTO medicines (drug_name, generic_name, dosage_form, strength, manufacturer, stock_quantity, unit_price)
                                         VALUES (?,?,?,?,?,?,?)''',
                                      (drug, generic, form, strength, manu, stock, price))
                            conn.commit()
                            st.success(f"{drug} added!")
                            st.rerun()

            meds_df = pd.read_sql("SELECT * FROM medicines ORDER BY drug_name", conn)
            if not meds_df.empty:
                edited = st.data_editor(meds_df, use_container_width=True, hide_index=True)
                if st.button("Save Changes"):
                    for _, row in edited.iterrows():
                        c.execute('''UPDATE medicines SET drug_name=?, generic_name=?, dosage_form=?, strength=?, manufacturer=?, stock_quantity=?, unit_price=? WHERE medicine_id=?''',
                                  (row['drug_name'], row['generic_name'], row['dosage_form'], row['strength'], row['manufacturer'], row['stock_quantity'], row['unit_price'], row['medicine_id']))
                    conn.commit()
                    st.success("Changes saved!")
        with tab4:
            st.subheader("📹 Live Video Consultation")
            st.info("Please join the Video Meeting....")

            html_code = get_video_html_code(role)
            # Display WebRTC component
            st.components.v1.html(html_code, height=700, width='stretch')

    # st.caption("VitalLink - Logout issue is now FIXED")
