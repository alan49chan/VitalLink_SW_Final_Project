import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import hashlib

# Database setup
conn = sqlite3.connect('vitalink.db', check_same_thread=False)
c = conn.cursor()

# 创建所需的表
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS patients
             (id INTEGER PRIMARY KEY, name TEXT, glucose REAL, bp_systolic REAL, bp_diastolic REAL, heart_rate REAL, timestamp TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS prescriptions
             (id INTEGER PRIMARY KEY, patient_name TEXT, medicine TEXT, dosage TEXT, notes TEXT, timestamp TEXT)''')
conn.commit()

# 辅助函数：密码加密
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 辅助函数：验证密码
def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

st.set_page_config(page_title="VitalLink", page_icon="🩺", layout="wide")
st.title("🩺 VitalLink - Remote Chronic Care")

# ====================== 1. 注册及登录功能 ======================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# 如果用户未登录，显示登录界面
if not st.session_state['logged_in']:
    st.sidebar.subheader("Login / Registration")
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Select Action", menu)

    if choice == "Login":
        st.subheader("Login Section")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type='password', placeholder="Enter your password")
        
        if st.button("Login"):
            # 在数据库中查找用户
            c.execute('SELECT password, role FROM users WHERE username = ?', (username,))
            data = c.fetchone()
            if data:
                hashed_pw, role = data
                if check_hashes(password, hashed_pw):
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = role
                    st.session_state['username'] = username
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("User not found.")

    elif choice == "Register":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        role = st.selectbox("Role", ["Patient", "Doctor"])
        
        if st.button("Register"):
            # 检查用户名是否已存在
            c.execute('SELECT * FROM users WHERE username = ?', (new_user,))
            if c.fetchone():
                st.warning("Username already exists.")
            else:
                c.execute('INSERT INTO users(username, password, role) VALUES (?,?,?)', 
                          (new_user, make_hashes(new_password), role))
                conn.commit()
                st.success("Account created successfully! Please log in from the sidebar.")

# 如果已登录，显示仪表板内容
else:
    # 退出登录按钮
    st.sidebar.write(f"Logged in as: **{st.session_state['username']}** ({st.session_state['user_role']})")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.session_state['username'] = None
        st.rerun()

    role = st.session_state['user_role']
    name = st.session_state['username']
    
    # 房间 ID
    ROOM_ID = "vitalink-demo-room"

    if role == "Patient":
        st.header(f"🧑‍🦰 Patient Dashboard - Welcome {name}")
        
        # 使用 Tab 优化界面布局 (需求 4)
        tab_vitals, tab_history, tab_records = st.tabs(["📡 Input Vitals", "📈 Health Trends", "💊 Medical Records"])

        with tab_vitals:
            st.subheader("📡 Mock Sensor Data")
            col1, col2, col3 = st.columns(3)
            with col1: glucose = st.number_input("Blood Glucose (mg/dL)", 70, 300, 120)
            with col2:
                bp_s = st.number_input("BP Systolic", 90, 180, 130)
                bp_d = st.number_input("BP Diastolic", 60, 120, 85)
            with col3: hr = st.number_input("Heart Rate (bpm)", 50, 120, 75)

            if st.button("📡 Send Sensor Data"):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO patients (name, glucose, bp_systolic, bp_diastolic, heart_rate, timestamp) VALUES (?,?,?,?,?,?)",
                          (name, glucose, bp_s, bp_d, hr, ts))
                conn.commit()
                st.success(f"✅ Data sent at {ts}")

        with tab_history:
            # ====================== 3. 数据的图表显示 (配合 README 预警阈值) ======================
            st.subheader("Your Bio-Stat History")
            df = pd.read_sql(f"SELECT * FROM patients WHERE name='{name}' ORDER BY timestamp DESC", conn)
            
            if not df.empty:
                # 顶部 KPI 卡片 (优化布局需求 4)
                latest = df.iloc[0]
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("Latest Glucose", f"{latest['glucose']} mg/dL")
                kpi2.metric("Latest BP", f"{latest['bp_systolic']}/{latest['bp_diastolic']}")
                kpi3.metric("Latest Heart Rate", f"{latest['heart_rate']} bpm")

                # 图表显示
                fig = px.line(df, x='timestamp', y=['glucose', 'bp_systolic', 'heart_rate'], title="Health Trend Over Time")
                # 添加 README 要求的预警阈值线
                fig.add_hline(y=180, line_dash="dash", line_color="red", annotation_text="Glucose Alert (180)")
                fig.add_hline(y=140, line_dash="dash", line_color="orange", annotation_text="BP Systolic Alert (140)")
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(df)
            else:
                st.info("No data yet. Please input your vitals first.")

        with tab_records:
            # ====================== 2. 病人查阅医疗记录 ======================
            st.subheader("Your Prescription History")
            pres_df = pd.read_sql(f"SELECT medicine, dosage, notes, timestamp FROM prescriptions WHERE patient_name='{name}' ORDER BY timestamp DESC", conn)
            if not pres_df.empty:
                for idx, row in pres_df.iterrows():
                    with st.expander(f"💊 Prescription - {row['timestamp']}"):
                        st.write(f"**Medicine:** {row['medicine']}")
                        st.write(f"**Dosage:** {row['dosage']}")
                        st.info(f"**Doctor's Notes:** {row['notes']}")
            else:
                st.info("No prescriptions found.")

    elif role == "Doctor":
        st.header(f"👨‍⚕️ Doctor Dashboard - Dr. {name}")
        df_all = pd.read_sql("SELECT * FROM patients ORDER BY timestamp DESC", conn)
        
        if not df_all.empty:
            # 侧边栏搜索病人
            st.sidebar.subheader("Search Patient")
            patient_list = df_all['name'].unique()
            patient_name = st.sidebar.selectbox("Select Patient to Review", patient_list)
            
            # 显示所选病人的概览
            patient_df = df_all[df_all['name'] == patient_name]
            
            col_list, col_chart = st.columns([1, 2])
            
            with col_list:
                st.subheader(f"Data for {patient_name}")
                # 根据 README 阈值自动标记
                patient_df['status'] = patient_df.apply(lambda row: "🔴 ALERT" if row['glucose'] > 180 or row['bp_systolic'] > 140 else "✅ Normal", axis=1)
                st.dataframe(patient_df[['timestamp', 'glucose', 'bp_systolic', 'status']])

            with col_chart:
                fig_doc = px.line(patient_df, x='timestamp', y=['glucose', 'bp_systolic', 'heart_rate'], title=f"Trend: {patient_name}")
                fig_doc.add_hline(y=180, line_dash="dash", line_color="red")
                st.plotly_chart(fig_doc, use_container_width=True)

            st.divider()
            
            # 处方功能
            st.subheader(f"💊 Prescribe Medicine for {patient_name}")
            col_m, col_d = st.columns(2)
            with col_m: medicine = st.text_input("Medicine Name")
            with col_d: dosage = st.text_input("Dosage (e.g., 500mg, twice daily)")
            notes = st.text_area("Doctor's Notes")
            
            if st.button("💊 Send Prescription"):
                if medicine and dosage:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO prescriptions (patient_name, medicine, dosage, notes, timestamp) VALUES (?,?,?,?,?)",
                              (patient_name, medicine, dosage, notes, ts))
                    conn.commit()
                    st.success(f"✅ Prescription successfully sent to {patient_name}!")
                else:
                    st.error("Please fill in at least the medicine name and dosage.")
        else:
            st.info("No patient data available in the system.")

    # ====================== 视频通话功能 (保持原有) ======================
    with st.expander("📹 Start Live Video Consultation"):
        st.caption(f"Room ID: **{ROOM_ID}**")

        # Status placeholder for Python-side updates
        status_placeholder = st.empty()

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
            <h4>📷 Your Camera</h4>
            <video id="localVideo" autoplay muted playsinline></video>
        </div>
        <div style="flex:1">
            <h4>👤 Remote Video</h4>
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
        st.components.v1.html(html_code, height=700, width='stretch')

    # Add WebRTC debugging info in sidebar
    st.sidebar.success("✅ Using your Node.js Signaling Server + TURN (paul / 66801224)")
    st.sidebar.info("""
    **📋 WebRTC Connection Checklist:**
    1. Both users must click "Join Video Call"
    2. Allow camera/microphone permissions
    3. Check browser console (F12) for ICE/TURN logs
    4. If connection fails, TURN server is working as fallback
    """)

    st.caption("COMP2116 Final Project - Full custom WebRTC | Fixed: ICE candidates, connection states, and error handling")