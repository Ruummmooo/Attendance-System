# Multimodal Attendance & Engagement Agent
Beginner-friendly, offline-first classroom support application.

## 1. Requirements
- Python 3.10–3.12 recommended
- VS Code (recommended)
- Webcam
- Internet only for installing Python packages; app data processing is local

## 2. Open the project
Extract the ZIP file and open the `multimodal_attendance_agent` folder in VS Code.

## 3. Create a virtual environment

### Windows PowerShell
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:
```bat
.venv\Scripts\activate.bat
```

## 4. Install packages
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Run the application
```bash
streamlit run app.py
```
Streamlit opens the app in your browser, usually at `http://localhost:8501`.

## 6. How to use
1. Open **Students** and add student names and unique roll numbers.
2. Open **Webcam Attendance** and allow browser camera access.
3. Take a classroom photo.
4. The app highlights detected faces. Detection does not identify a person.
5. Select the correct student from the list and click **Confirm and mark attendance**.
6. Open **Engagement Lab**, enter teacher observations and save a session.
7. Open **Reports** to view and download CSV reports.

## 7. Project structure
```text
multimodal_attendance_agent/
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```
`attendance.db` is created automatically the first time the app runs.

## 8. Troubleshooting
- **Camera not showing:** Allow camera permission in your browser and use `localhost`.
- **ModuleNotFoundError:** Activate `.venv`, then run `pip install -r requirements.txt`.
- **Streamlit command not found:** Run `python -m streamlit run app.py`.
- **Face detector error:** Reinstall OpenCV with `pip install --force-reinstall opencv-python-headless`.
- **PowerShell activation issue:** Use Command Prompt activation shown above.

## 9. Privacy and project scope
This is a prototype. It detects faces but does not recognize identities. The teacher confirms identity manually. Camera images are processed in memory and are not written to the database. Student names and attendance are stored locally in SQLite. Obtain appropriate consent and institutional approval before using real student data.

The engagement indicator is a transparent arithmetic summary of teacher-entered classroom observations. It is not a validated measure of attention, emotion, learning, or student performance.

## 10. Future upgrades
- Continuous webcam monitoring with explicit consent and visible recording controls.
- Session-level attendance duration tracking.
- More detailed teacher-entered interaction timeline.
- Role-based teacher login.
- Optional export to PDF.
