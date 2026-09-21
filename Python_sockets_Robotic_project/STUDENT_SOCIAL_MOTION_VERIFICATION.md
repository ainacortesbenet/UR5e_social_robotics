# Student Guide: Verifying a UR5e Social Motion

## Purpose

This guide describes how to verify your chosen social motion in three stages:

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

- `motions/<motion_name>.yaml`: the motion sequence;
- `behavior_manager_client.py`: registers the motion name and sends its YAML;
- `motion_client.py`: command-line interface;
- `voice_motion_client.py`: voice interface;
- `face_voice_motion_client.py`: face gate followed by the voice interface;
- `command_interpreter.py`: maps spoken phrases to registered motion names;
- `config.py`: client/server, robot, execution-mode, voice, and face settings;
- `ur5e_motion_server.py`: TCP server running on the teacher's computer;
- `ur5e_robot_controller.py`: executes motions in RoboDK and/or on the real robot.

Do not start `ur5e_robot_controller.py` directly. It is created by `ur5e_motion_server.py`.

## 1. Prepare and register your motion

Work from the project directory:

```bash
cd UR5e_social_robotics/Python_sockets_Robotic_project
```

Install the core dependencies in your Python environment:

```bash
py -3.12 -m pip install -r requirements.txt
```

On MAC, use `python3.12` instead.

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

Check the following before running it:

- the first pose is safe and reachable;
- intermediate poses do not cross the table, robot base, tool, people, or other obstacles;
- speed and acceleration are low for initial tests;
- the last step returns to a safe pose;
- all `moveJ` lists have six joint values;
- all Cartesian positions use millimetres and all angles use degrees.

## 2. Verify locally on one computer at home

### 2.1 Select simulation-only execution

In `config.py`, set:

```python
EXECUTION_MODE = "simulation_only"
```

In `config.py`, make the client connect to the server on the same computer:

```python
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
```

The controller may report that it cannot connect to the real robot. This is expected at home. In `simulation_only` mode, no URScript is sent to a real UR5e.

### 2.2 Start the local server

Open terminal 1 in the project directory:

```bash
py -3.12 ur5e_motion_server.py
```

Expected evidence:

- RoboDK opens;
- `Social_UR5e.rdk` is loaded;
- the terminal reports `UR5e classroom server listening on 0.0.0.0:5000`.

### 2.3 Send the motion from a second terminal

Open terminal 2 in the same directory:

```bash
py -3.12 motion_client.py --list
py -3.12 motion_client.py <motion_name>
```

For example:

```bash
py -3.12 motion_client.py wave
```

A successful test must show all of the following:

- your command appears in the `--list` output;
- the server prints the received YAML;
- RoboDK completes every step without an unreachable-target or collision problem;
- the client receives `OK: sequence executed`;
- the motion begins and ends in the intended safe poses and looks socially understandable.

An `OK` response only means that the sequence completed; it is not proof that the motion is safe. Inspect the complete trajectory visually, not only its final pose. Correct the YAML and repeat the test until the whole motion is safe and smooth.

Stop the server with `Ctrl+C` when finished.

## 3. Verify in the laboratory with two computers

### 3.1 Determine the correct laboratory addresses

The classroom router uses the `192.168.1.0/24` network. The teacher PC address follows this pattern:

```text
192.168.1.x5
```

Here, `x` is the workstation or group digit; do not type the letter `x` literally.

| Workstation/group `x` | Teacher PC address |
|---:|---|
| 1 | `192.168.1.15` |
| 2 | `192.168.1.25` |
| 3 | `192.168.1.35` |
| 4 | `192.168.1.45` |

Confirm your assigned value with the instructor. Also confirm the UR5e IP separately. The repository currently contains `ROBOT_IP = "192.168.0.20"`; this is not the teacher PC address and may need to be changed on the teacher PC for the laboratory station.

### 3.2 Check client-to-server connectivity

Connect both computers to the same laboratory router. On the student computer:

```bash
ping <TEACHER_PC_IP>
```

For group 2, for example:

```bash
ping 192.168.1.25
```

If this fails, check the selected workstation, cable/Wi-Fi connection, subnet, and local firewall before continuing.

In `config.py` on the student computer, replace the local address with the assigned teacher PC address:

```python
SERVER_IP = "192.168.1.25"  # Example for x = 2
SERVER_PORT = 5000
```

Do not change `SERVER_IP` in `ur5e_motion_server.py`; `0.0.0.0` is intentional because it makes the server listen on the teacher PC's network interfaces.

### 3.3 Perform a two-computer simulation first

On the teacher PC, keep this setting in `config.py`:

```python
EXECUTION_MODE = "simulation_only"
```

Then start the server on the teacher PC:

```bash
cd UR5e_social_robotics/Python_sockets_Robotic_project
py -3.12 ur5e_motion_server.py
```

If needed, allow inbound TCP port `5000` through the teacher PC firewall only for the private laboratory network.

On the student computer:

```bash
cd UR5e_social_robotics/Python_sockets_Robotic_project
py -3.12 motion_client.py --list
py -3.12 motion_client.py <motion_name>
```

Confirm that the YAML arrives at the teacher PC, the motion completes in RoboDK there, and the student client receives `OK: sequence executed`.

If the client reports `Connection refused`, verify that the server is running and listening on port `5000`. If it times out, recheck the IP, router connection, and firewall.

### 3.4 Obtain approval and prepare the real robot

Only the instructor may approve the transition to real motion. Before execution:

- show the complete RoboDK simulation to the instructor;
- verify the station's actual UR5e address and set `ROBOT_IP` in `ur5e_robot_controller.py` on the teacher PC;
- verify the tool and TCP configured in RoboDK and on the robot;
- clear the robot workspace and keep all people outside it;
- ensure the emergency stop is accessible and identify who will operate it;
- use reduced speed on the teach pendant for the first run;
- start from the same physical configuration used by the simulation;
- never hold the robot or stand at the handshake/high-five target during the first real test.

The teacher should restart the server after changing the controller configuration and confirm that it prints a successful connection to the correct UR5e address.

### 3.5 Execute the approved real test

On the teacher PC, set one of these modes in `config.py` as directed by the instructor:

```python
EXECUTION_MODE = "simulation_and_real"
```

This mode keeps the RoboDK execution while also sending URScript to the UR5e. `real_only` is also available, but should only be selected by the instructor. These are the only three accepted values in `config.py`:

```python
EXECUTION_MODE = "simulation_only"      # RoboDK only
EXECUTION_MODE = "simulation_and_real"  # RoboDK and UR5e
EXECUTION_MODE = "real_only"            # UR5e only
```

Keep only one assignment active. An invalid value makes the server stop with a clear error before loading RoboDK or moving the robot.

Restart the server on the teacher PC, then send the request from the student computer:

```bash
py -3.12 motion_client.py <motion_name>
```

The server serialises access, so only one student should send a motion at a time. Stop immediately with the robot emergency stop or protective stop procedure if the trajectory differs from the approved simulation. Do not repeatedly resend a failed motion until the cause has been identified.

Record the following evidence:

- the motion name and YAML version used;
- the assigned teacher PC IP;
- successful server connection and response;
- simulation result;
- instructor approval and real-robot result;
- any corrections made after the first test.

## 4. Add and verify voice identification

Voice recognition runs on the student computer and selects the same registered motion. It uses Google's speech-recognition service, so Internet access is required.

Install the optional dependencies:

```bash
py -3.12 -m pip install -r requirements_voice.txt
```

On Ubuntu, microphone and speech support may also require:

```bash
sudo apt install portaudio19-dev python3-pyaudio espeak-ng
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

Keep the correct `SERVER_IP` for the stage being tested: `127.0.0.1` at home or the teacher PC's `192.168.1.x5` address in the laboratory. Start the motion server first, then run on the student computer:

```bash
py -3.12 voice_motion_client.py
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

## 5. Add face verification before voice control

The face module is an access gate: it checks a face once and, when authorised, starts the same voice client. It does not continuously identify the user and it does not add robot safety guarantees.

Install the optional dependencies:

```bash
py -3.12 -m pip install -r requirements_face.txt
```

Installation of `dlib` may require operating-system build tools. Use the prepared laboratory environment if local installation fails.

Create a clear reference photograph containing one front-facing authorised face. Store it inside `resources/Pictures/`, then update `config.py` with its real filename. For example:

```python
REFERENCE_FACE_IMAGE = "resources/Pictures/student_reference.png"
CAMERA_INDEX = 0
FACE_MATCH_TOLERANCE = 0.6
```

The repository includes `resources/Pictures/Manel_ref.png`, but the current default setting points to `resources/Pictures/authorised_user.jpg`. Either provide that file or change `REFERENCE_FACE_IMAGE`; otherwise verification will always fail.

With the server running in `simulation_only` mode, execute:

```bash
py -3.12 face_voice_motion_client.py
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

## 6. Final acceptance checklist

- [ ] The custom YAML is valid and registered in `MOTIONS`.
- [ ] The command appears in `motion_client.py --list`.
- [ ] The entire trajectory is safe and smooth in local RoboDK simulation.
- [ ] The local client receives `OK: sequence executed`.
- [ ] The assigned teacher PC address replaces `x` correctly in `192.168.1.x5`.
- [ ] The student can ping the teacher PC and reach TCP port `5000`.
- [ ] The two-computer test succeeds in `simulation_only` mode.
- [ ] The instructor has reviewed and approved the motion.
- [ ] The teacher PC uses the verified UR5e IP and reports a robot connection.
- [ ] The first real run uses reduced speed and a clear workspace.
- [ ] Valid, missing-activation-word, unknown, and exit voice cases behave correctly.
- [ ] Authorised and unauthorised face cases behave correctly.
- [ ] The final face-to-voice-to-YAML-to-motion chain succeeds in simulation before any real execution.

## Troubleshooting summary

| Symptom | Likely check |
|---|---|
| Motion is absent from `--list` | Register the exact key and relative YAML path in `MOTIONS`. |
| `Unknown motion` | Use the registered key, not the YAML filename unless they are identical. |
| `Connection refused` | Start the server and verify port `5000`. |
| Connection timeout | Check `SERVER_IP`, router/subnet, ping, and firewall. |
| `Robot is busy` | Wait for the active sequence to finish; do not resend repeatedly. |
| RoboDK target error | Correct unreachable poses, reference frame, tool, or orientation. |
| Real robot does not move | Confirm execution mode, robot IP, TCP port `30002`, and the server's connection message. |
| Voice is ignored | Begin with `robot`, use an accepted phrase, check microphone and Internet access. |
| Face is always denied | Check the configured path, one visible reference face, camera index, and lighting. |
