# Windows execution Social Robotics Project

## Purpose

This guide describes how to verify your chosen social motion in successive stages:

1. locally, in RoboDK, using one computer at home;
2. in the laboratory, using your computer as the client and the teacher's computer as the server connected to the UR5e;
3. through voice commands, followed by face verification and voice commands.

Complete the stages in order. A successful simulation is required before requesting permission to move the real robot.

## Architecture

```text
Student interface                  Teacher PC                    UR5e
CLI / voice / face + voice
        |
        | complete YAML sequence
        | TCP port 5000
        +-------------------------> ur5e_motion_server.py
                                             |
                                             | URScript
                                             | TCP port 30002
                                             +---------------> robot
        <------------------------- OK or ERROR
```

The student computer never connects directly to the UR5e. All three client interfaces use the same `BehaviorManager` and send the selected YAML sequence to the teacher's server.

## Project files used in this activity

- `config.py`: client/server, robot, execution-mode, voice, and face settings;
- `lib/requirements*.txt`: core, voice, and face dependencies used to prepare `.venv-win`;
- `motions/<motion_name>.yaml`: the motion sequence;
- `ur5e_motion_server.py`: TCP server running on the teacher's computer;
    - Imports: `ur5e_robot_controller.py`: executes motions in RoboDK and/or on the real robot.
- `face_voice_motion_client.py`: face gate followed by the voice interface;
    - Imports: `voice_motion_client.py`: voice interface;
        - Imports: `command_interpreter.py`: maps spoken phrases to registered motion names;
        - Imports: `behavior_manager_client.py`: registers the motion name and sends its YAML;
- `motion_client.py`: command-line interface;
    - Imports: `behavior_manager_client.py`: registers the motion name and sends its YAML;

## 1. Prepare and register your motion

This first implementation runs directly on Windows with Python 3.10 and does
not require ROS 2. Create a dedicated virtual environment named `.venv-win`
inside the project directory:

```powershell
cd Python_sockets_Robotic_project
py -3.10 -m venv .venv-win
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r lib/requirements.txt
```

After activation, `python` is the interpreter from `.venv-win`

Activate `.venv-win` again in every new PowerShell terminal before using this
project:

```powershell
cd UR5e_social_robotics\Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
```

Create `motions/<motion_name>.yaml`. Use `init.yaml`, `handshake.yaml`, or `give5.yaml` as a structural example. A sequence must contain `steps`; each step must be either:

- `moveJ`, with six values in `joints_deg`; or
- `moveL`, with three values in both `target_xyz_mm` and `target_rpy_deg`.

Use a short lowercase command name without spaces, for example `wave`. Register the same name in `MOTIONS` in `behavior_manager_client.py`:

```python
MOTIONS = {
    "init": "motions/init.yaml",
    "handshake": "motions/handshake.yaml",
    "give5": "motions/give5.yaml",
    "wave": "motions/wave.yaml",
}
```

## 2. Verify locally on one computer in simulation

### 2.1 Review configuration parameters

In `config.py`, set:

```python
EXECUTION_MODE = "simulation_only"
```

In `config.py`, make the client connect to the server on the same computer:

```python
SERVER_IP = "127.0.0.1"
```

In `simulation_only` mode, the controller does not attempt to connect to the
real UR5e and no URScript is sent to it.

### 2.2 Start the local server

Open terminal 1 in the project directory:

```powershell
cd UR5e_social_robotics\Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python ur5e_motion_server.py
```

Expected evidence:

- RoboDK opens;
- `Social_UR5e.rdk` is loaded;
- the terminal reports `UR5e classroom server listening on 0.0.0.0:5000`. This means that the server is listening on all network interfaces.

### 2.3 Send the motion from a second terminal as a client

Open terminal 2 in the same directory:

```powershell
cd UR5e_social_robotics\Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python motion_client.py --list
python motion_client.py <motion_name>
```

For example:

```powershell
python motion_client.py wave
```

A successful test must show all of the following:

- your command appears in the `--list` output;
- the server prints the received YAML;
- RoboDK completes every step without an unreachable-target or collision problem;
- the client receives `OK: sequence executed`;
- the motion begins and ends in the intended safe poses and looks socially understandable.

Stop the server with `Ctrl+C` when finished.

## 3. Verify in the laboratory with two computers

### 3.1 Review configuration parameters

The classroom router uses the `192.168.1.0/24` network:

- the teacher PC always uses `192.168.1.5`;
- each student PC uses `192.168.1.x5`, where `x` is the group number (for example, group 1 uses `192.168.1.15`). Confirm the assigned address with the instructor before configuring it.

In `config.py`, set:

```python
EXECUTION_MODE = "simulation_only"
```

In `config.py` on the student PC, make the client connect to the server on the teacher PC:

```python
SERVER_IP = "192.168.1.5"
```

### 3.2 Start the local server in PC-Professor

Start the server on the teacher PC:

```powershell
cd UR5e_social_robotics/Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python ur5e_motion_server.py
```

### 3.3 Send the motion from a PC-Student

On the student computer:

```powershell
cd UR5e_social_robotics/Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python motion_client.py --list
python motion_client.py <motion_name>
```

Confirm that the YAML arrives at the teacher PC, the motion completes in RoboDK there, and the student client receives `OK: sequence executed`.

## 4. Execute real test on UR5e

First of all, verify that **Professor's PC**:

- has the fixed IP address: `192.168.0.10`
- can connect to the UR5e at `ROBOT_IP = "192.168.0.20"`:
    ````powershell
    Test-NetConnection 192.168.0.20 -Port 30002
    ````

On the teacher PC, set the execution mode in `config.py`:
```python
EXECUTION_MODE = "simulation_and_real"  # RoboDK and UR5e
```

Before restarting the server, confirm that the approved RoboDK simulation has
completed successfully, the configured TCP/tool is correct, the robot workspace
is clear, reduced speed is selected, and the emergency stop is accessible.

Restart the server on the teacher PC before sending a request from a student PC.
On each student PC, keep `SERVER_IP = "192.168.1.5"` in `config.py`.

From the **student's PC**:

- verify the connection to the teacher's server:
    ````powershell
    Test-NetConnection 192.168.1.5 -Port 5000
    ````

- Once restarted the server program, send the request from the student computer:

    ```powershell
    cd UR5e_social_robotics/Python_sockets_Robotic_project
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv-win\Scripts\Activate.ps1
    python motion_client.py <motion_name>
    ```

The server accepts only one motion at a time. If another request arrives while a
motion is running, it is rejected with `ERROR: Robot is busy. Try again later.`
Stop immediately with the robot emergency stop or protective stop procedure if
the trajectory differs from the approved simulation.


## 5. Add and verify voice identification

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

## 6. Add face verification before voice control

The face module is an access gate: it checks a face once and, when authorised, starts the same voice client. It does not continuously identify the user and it does not add robot safety guarantees.

Install the optional dependencies:

```powershell
cd UR5e_social_robotics/Python_sockets_Robotic_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv-win\Scripts\Activate.ps1
python -m pip install -r lib/requirements_face.txt
```

Installation of `dlib` may require operating-system build tools. Use the prepared laboratory environment if local installation fails. Be sure you have installed `Build Tools` following the guide on:
[Install dlib on Windows](https://github.com/manelpuig/UR5e_social_robotics/blob/1b461bcd0520dd3f2482ecfd178c4b1021cdb94a/Documentation/Files/Install_Social_Libraries/Install_python_dlib_win.md)

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
