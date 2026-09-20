# Roxstar Voice Assistant - Minimal LiveKit Agent

A minimal Python worker agent built with the [LiveKit Agents SDK](https://github.com/livekit/agents) to verify connectivity to LiveKit Cloud and monitor room participants.

## Features

- Loads LiveKit credentials (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`) securely from `.env`.
- Connects to a LiveKit room (e.g., `test-room`).
- Logs a clear confirmation message upon successful connection.
- Listens for and logs human participant join and leave events in real-time.

---

## Setup Instructions

### 1. Activate Virtual Environment
Ensure your Python virtual environment is activated:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
Install the required packages listed in `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### 3. Verify Environment File (`.env`)
Make sure `.env` exists in the project root containing your LiveKit credentials:

```env
LIVEKIT_URL=wss://roxstar-assistant-oynefiz7.livekit.cloud
LIVEKIT_API_KEY=APInZckG7T7Ap2K
LIVEKIT_API_SECRET=8sEteD8eBmCxg2ePah5sLxhcX6XwzKzn6Gsgebw245hB
```

---

## Running the Agent

### Option A: Development / Worker Mode (Recommended)
Run the agent in `dev` mode to connect to LiveKit Cloud and wait for room dispatches:

```powershell
python agent.py dev
```

### Option B: Connect Directly to `test-room`
To explicitly dispatch and connect the agent directly to the `test-room`:

```powershell
python agent.py connect --room test-room
```

---

## Verifying Connection & Events

1. Start the agent using one of the run commands above.
2. Look for the startup log:
   ```text
   INFO - Loaded credentials for LiveKit Server: wss://roxstar-assistant-oynefiz7.livekit.cloud
   INFO - ✅ Successfully connected to LiveKit room: 'test-room'
   ```
3. Open the [LiveKit Cloud Agents Playground](https://cloud.livekit.io) or join the `test-room` using a LiveKit web client.
4. When a user joins, the agent will log:
   ```text
   INFO - 🟢 Human participant joined! Identity: 'user-name' (SID: PA_...)
   ```
