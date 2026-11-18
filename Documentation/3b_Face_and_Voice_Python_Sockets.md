# Face and voice with Python sockets

Start with the [socket session in simulation](3a_Python_Sockets_Session.md#2-simulation).
The voice client selects a registered motion. Face verification can gate access
to that client.

## 1. Add and verify voice control

Voice recognition runs on the student computer and selects the same registered motion. It uses Google's speech-recognition service, so Internet access is required.

Install the optional dependencies:

```powershell
cd UR5e_social_robotics/Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python -m pip install -r lib/requirements_voice.txt
```

`lib/requirements_voice.txt` contains the Python packages and is used on Windows, macOS, and Ubuntu. Some operating systems also need native audio packages, which cannot be installed by `pip` and must not be added to this requirements file.

On Windows, the command above is normally sufficient. Allow desktop applications to access the microphone in Windows privacy settings if prompted.

On macOS, the command above is normally sufficient. If `PyAudio` cannot be installed, install PortAudio first and repeat the `pip` command:

```bash
brew install portaudio
```

Also grant microphone access to Terminal or the application running Python in **System Settings > Privacy & Security > Microphone**.

On Ubuntu, install the native microphone and speech components first, then run the same `pip` command:

```bash
sudo apt update
sudo apt install portaudio19-dev espeak-ng
python -m pip install -r lib/requirements_voice.txt
```

In `config.py`, verify:

```python
ACTIVATION_WORD = "robot"
LANGUAGE = "en-US"
```

Add phrases for your motion in `VoiceInterpreter.interpret()` in `command_interpreter.py`. Every accepted phrase must return exactly the key registered in `MOTIONS`. For a registered `wave` motion, for example:

```python
if any(k in text for k in ["wave", "wave hello", "say hello"]):
    return "wave"
```

Keep the correct `SERVER_IP` for the stage being tested: `127.0.0.1` when client and server run on the same computer, or `192.168.1.5` when the server runs on the teacher PC in the laboratory. Start the motion server first, then run on the student computer:

```powershell
cd UR5e_social_robotics/Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python voice_motion_client.py
```

Say the activation word followed by the command, for example:

```text
robot wave
```

Verify these cases while the server is in `simulation_only` mode:

1. a valid phrase triggers the correct motion;
2. a phrase without `robot` triggers no motion;
3. an unknown command produces `Command not understood`;
4. `robot exit` closes the voice client;
5. background speech does not trigger an unintended sequence.

Only repeat the voice test with the real robot after the command-line version has been approved. A person must still supervise the robot; speech recognition is not a safety system.

## 2. Add face verification before voice control

The face module is an access gate: it checks a face once and, when authorised, starts the same voice client. It does not continuously identify the user and it does not add robot safety guarantees.

Install the optional dependencies:

```powershell
cd UR5e_social_robotics/Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python -m pip install -r lib/requirements_face.txt
```

Installation of `dlib` may require operating-system build tools. Use the prepared laboratory environment if local installation fails. Be sure you have installed `Build Tools` following the guide on:
[Install dlib on Windows](Files/Install_Social_Libraries/Install_python_dlib_win.md)

Create a clear reference photograph containing one front-facing authorised face. Store it inside `resources/Pictures/`, then update `config.py` with its real filename. For example:

```python
REFERENCE_FACE_IMAGE = "resources/Pictures/student_reference.png"
CAMERA_INDEX = 0
FACE_MATCH_TOLERANCE = 0.6
```

The repository includes both `resources/Pictures/Manel_ref.png` and the default
`resources/Pictures/authorised_user.png`. Replace the default image or change
`REFERENCE_FACE_IMAGE` when a different authorised user must be verified.

With the server running in `simulation_only` mode, execute:

```powershell
python face_voice_motion_client.py
```

Verify the complete chain:

```text
reference image loaded
        -> camera detects and matches the authorised face
        -> voice client starts
        -> "robot <motion_name>" is interpreted
        -> YAML is sent to the teacher server
        -> RoboDK executes the expected motion
        -> client receives OK
```

Also test the negative cases:

- missing reference image: access is denied;
- image with no detectable face: access is denied;
- unavailable or incorrect camera index: access is denied;
- non-matching person: voice control does not start;
- pressing `Q` cancels verification.

Do not weaken `FACE_MATCH_TOLERANCE` merely to make a poor photograph pass. Improve lighting, camera position, and the reference image first. Treat face matching as a classroom demonstration, not as secure biometric authentication.

After all negative and positive cases pass in simulation, repeat the authorised face-and-voice chain with the real UR5e only under instructor supervision and using the already approved motion.
