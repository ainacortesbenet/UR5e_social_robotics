# Classroom DDS Network Test: Student PCs, Teacher PC and UR5e

This guide verifies the ROS 2 connection in small, safe steps. Run every DDS
test on the **classroom network** (`192.168.1.0/24`). The robot Ethernet
network (`192.168.0.0/24`) is only for the Teacher PC and the UR5e.

The recommended final configuration for this classroom is **Cyclone DDS
unicast with fixed IP addresses (or DHCP reservations)**. It avoids common
Wi-Fi access-point isolation and multicast/IGMP problems. Use multicast first:
it is simpler and is a useful test of the network. If it is stable on the
actual laboratory network, it is also a valid choice.

## 1. Expected architecture

```text
Student PC(s) -- 192.168.1.x -- Teacher PC (192.168.1.5)
                                         |
                                  Teacher PC (192.168.0.10)
                                         |
                                      UR5e (192.168.0.20)
```

Only the Teacher PC runs the UR driver, MoveIt, controllers, and
`ur5e_sequence_server`. Student PCs only publish behavior requests and call
the service indirectly through the Behavior Manager.

Do not configure DDS to use `192.168.0.10`. The ROS 2 traffic between students
and teacher must use `192.168.1.5`; the UR driver reaches `192.168.0.20`
independently.

For the examples below, replace these values with the real addresses:

| Role | Example address |
|---|---|
| Teacher classroom interface | `192.168.1.5` |
| Student 1 classroom interface | `192.168.1.15` |
| Student 2 classroom interface | `192.168.1.25` |
| Teacher robot interface | `192.168.0.10` |
| UR5e | `192.168.0.20` |

Each Student PC has a permanent domain: Student 1 uses `1`, Student 2 uses
`2`, Student 3 uses `3`, and Student 4 uses `4`. For one test, the Teacher
sets its `ROS_DOMAIN_ID` to the selected Student domain. It then cannot
discover nodes on the other Student domains.

## 2. Common checks before DDS

On every PC, first identify the classroom interface and its address:

```bash
ip -4 addr
ip route
```

From each Student PC, check the Teacher PC:

```bash
ping -c 4 192.168.1.5
```

From the Teacher host, check both independent links:

```bash
ping -c 4 192.168.1.15   # one selected Student PC
ping -c 4 192.168.0.20   # UR5e; only when connected and powered
```

If the first ping fails, fix the cabling, VLAN, Wi-Fi client isolation, IP
address, netmask, or firewall before testing ROS 2. Do not test robot motion
at this stage.

Every terminal that runs ROS commands needs this base environment:

```bash
source /opt/ros/humble/setup.bash
source ~/UR5e_social_robotics/install/setup.bash
# Use 1 for Student 1, 2 for Student 2, 3 for Student 3, or 4 for Student 4.
export ROS_DOMAIN_ID=<student_domain>
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

After changing DDS configuration, stop old nodes, then run this in each test
terminal before starting new nodes:

```bash
ros2 daemon stop
```

The ROS 2 daemon is useful for command-line discovery, but it cannot repair a
wrong DDS configuration.

## 3. Test A: multicast discovery (simplest DDS setup)

Use this test when the LAN and Wi-Fi are expected to allow multicast. Keep the
Teacher configuration in
`Documentation/Files/Docker/cyclonedds_teacher_multicast.xml`:
it explicitly binds Cyclone DDS to `192.168.1.5` and enables multicast.

### 3.1 Student PC `.bashrc` for multicast

Add this once on each Ubuntu Student PC. Change the repository path if needed.
There must be no old `CYCLONEDDS_URI` export later in `.bashrc`.

```bash
# ROS 2 classroom: multicast
source /opt/ros/humble/setup.bash
if [ -f "$HOME/Desktop/UR5e_social_robotics/install/setup.bash" ]; then
    source "$HOME/Desktop/UR5e_social_robotics/install/setup.bash"
fi
# Student 1: 1; Student 2: 2; Student 3: 3; Student 4: 4.
export ROS_DOMAIN_ID=1
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
unset CYCLONEDDS_URI
```

Reload it in a new terminal:

```bash
source ~/.bashrc
env | grep -E 'ROS_DOMAIN_ID|ROS_LOCALHOST_ONLY|RMW_IMPLEMENTATION|CYCLONEDDS_URI'
```

### 3.2 Teacher PC configuration for multicast

The Teacher ROS environment runs inside the Docker container. Its Compose file
already sets the required variables and mounts:

```text
CYCLONEDDS_URI=file:///root/UR5e_social_robotics/Documentation/Files/Docker/cyclonedds_teacher_multicast.xml
```

Therefore ensure that `.bashrc` contains:

```bash
# ROS 2 classroom: multicast
source /opt/ros/humble/setup.bash
if [ -f "$HOME/UR5e_social_robotics/install/setup.bash" ]; then
    source "$HOME/UR5e_social_robotics/install/setup.bash"
fi
# Student 1: 1; Student 2: 2; Student 3: 3; Student 4: 4.
export ROS_DOMAIN_ID=1
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Inside the container, verify:

```bash
echo "$CYCLONEDDS_URI"
echo "$ROS_DOMAIN_ID"
echo "$RMW_IMPLEMENTATION"
```

We have selected the PC student we will connect to, in this case PC student 1


### 3.3 Prove data exchange with `demo_nodes_cpp`

On the **Teacher container**:

```bash
ros2 run demo_nodes_cpp talker
```

On one **Student PC**:

```bash
ros2 run demo_nodes_cpp listener
```

The Student must continuously print `I heard: [Hello World: ...]`. Stop both
nodes with `Ctrl+C`, then repeat in the opposite direction:

```bash
# Student PC
ros2 run demo_nodes_cpp talker

# Teacher container
ros2 run demo_nodes_cpp listener
```

Both directions matter: the handshake architecture needs student-to-teacher
requests and teacher-to-student replies. If one direction fails, multicast is
not reliable enough for the laboratory.

### 3.4 Multicast failure checklist

Confirm all of the following before moving to unicast:

- the Student and Teacher use Cyclone DDS and the same selected domain;
- `ROS_LOCALHOST_ONLY` is exactly `0`;
- the Teacher XML still names `192.168.1.5`, not `192.168.0.10`;
- no VPN, Docker bridge, or second ROS installation overrides the environment;
- the firewall permits local UDP traffic for DDS; and
- the Wi-Fi access point does not enable client isolation or multicast filtering.

If IP ping works but this test fails, it is normally a multicast policy or
interface-selection problem, not a UR5e problem.

## 4. Test B: unicast discovery with fixed peers

Use unicast when multicast is blocked or intermittent. Every PC needs a stable
classroom address. Prefer DHCP reservations or static addresses documented by
the instructor. If a Student IP changes, update its XML and restart its ROS 2
nodes.

Each Student XML needs only the Teacher as a peer. The supplied Teacher XML
lists all four Student addresses (`.15`, `.25`, `.35`, `.45`), so it can be
used without editing when another Student is selected. DDS domains still keep
all other Student PCs isolated.

### 4.1 Teacher unicast XML

The supplied file is
`Documentation/Files/Docker/cyclonedds_teacher_unicast.xml`. Its peers are
the four fixed Student addresses. Update the addresses only if the classroom
address plan changes.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain Id="any">
    <General>
      <Interfaces>
        <NetworkInterface address="192.168.1.5"/>
      </Interfaces>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <Peers>
        <Peer Address="192.168.1.15"/>
        <Peer Address="192.168.1.25"/>
        <Peer Address="192.168.1.35"/>
        <Peer Address="192.168.1.45"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

In `Documentation/Files/Docker/docker-compose.yaml`, change only the URI:

```yaml
- CYCLONEDDS_URI=file:///root/UR5e_social_robotics/Documentation/Files/Docker/cyclonedds_teacher_unicast.xml
```

Recreate the container using the command in section 3.2.

### 4.2 Student unicast XML

Copy `Documentation/Files/Docker/cyclonedds_student_unicast.xml` to each
Student repository (or keep the same relative path). In that file, replace
`192.168.1.15` in `NetworkInterface` with the IP address of that Student PC.
No other Student address is required; `192.168.1.5` remains the Teacher peer.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain Id="any">
    <General>
      <Interfaces>
        <!-- Replace with the IP address of this Student PC. -->
        <NetworkInterface address="192.168.1.15"/>
      </Interfaces>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <Peers>
        <Peer Address="192.168.1.5"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

### 4.3 Student PC `.bashrc` for unicast

Replace the multicast block with this block, or put it after the common ROS
settings so that it is the final DDS setting:

```bash
# ROS 2 classroom: unicast fixed peers
source /opt/ros/humble/setup.bash
if [ -f "$HOME/UR5e_social_robotics/install/setup.bash" ]; then
    source "$HOME/UR5e_social_robotics/install/setup.bash"
fi
# Student 1: 1; Student 2: 2; Student 3: 3; Student 4: 4.
export ROS_DOMAIN_ID=1
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI="file://$HOME/UR5e_social_robotics/Documentation/Files/Docker/cyclonedds_student_unicast.xml"
```

Reload `.bashrc`, stop the ROS daemon, and repeat the two directional talker /
listener tests from section 3.3. On the Teacher, select the same domain and
set `CYCLONEDDS_URI` in Compose to `cyclonedds_teacher_unicast.xml`. Do not mix
one multicast endpoint with one unicast endpoint during this test: configure
both participants alike.

## 5. Test C: handshake with fake UR5e

This is the required final network test before a real robot test. Use fake
hardware; no connection to the UR5e is made.

On the **Teacher container**, open three terminals with the same DDS profile:

```bash
# Terminal 1: fake driver
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 \
  use_fake_hardware:=true launch_rviz:=false
```

```bash
# Terminal 2: MoveIt
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e launch_rviz:=true
```

```bash
# Terminal 3: sequence server
ros2 run ur5e_motion_server ur5e_sequence_server
```

On the **Student PC**, open two terminals. Both must load the Student's DDS
profile from `.bashrc`, including its permanent domain and unicast XML.

```bash
# Student terminal 1: Behavior Manager Client
cd ~/UR5e_social_robotics
source install/setup.bash
ros2 launch social_robot_behaviors social_behavior.launch.py
```

Paste this directly in **Student terminal 2** to request the defined
handshake:

```bash
cd ~/UR5e_social_robotics
source install/setup.bash
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: 'handshake'}"
```

Expected evidence:

1. Student receives `/social_behavior` with `handshake`.
2. Teacher receives `RunSequence(handshake)`.
3. Teacher loads `handshake.yaml`.
4. IK and fake trajectories finish successfully.
5. Student logs `Sequence accepted`.

## 6. Test D: handshake with the real UR5e

Perform this test only after Test C succeeds, with an approved `handshake.yaml`,
the instructor present, a clear workspace, reduced robot speed, and an
accessible emergency stop. Student PCs never run the real driver or send direct
controller commands.

Before starting ROS, on the Teacher host confirm the dedicated robot link:

```bash
ping -c 4 192.168.0.20
```

On the Teacher container, open three new terminals. In **each one**, select the
same Student domain as the Student PC being tested. This example uses Student
1:

```bash
ros2 daemon stop
export ROS_DOMAIN_ID=1
```

Then start the real execution stack on the Teacher only:

```bash
# Teacher terminal 1: real UR driver
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 \
  use_fake_hardware:=false launch_rviz:=false
```

On the teach pendant, load the approved program containing **External Control**
for the Teacher PC `192.168.0.10`, then press **Play**. Continue only when the
driver reports a healthy robot connection.

```bash
# Teacher terminal 2: MoveIt and RViz
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e launch_rviz:=true
```

```bash
# Teacher terminal 3: sequence server
ros2 run ur5e_motion_server ur5e_sequence_server
```

On the selected Student PC, keep the configured matching domain. In Student
terminal 1 launch the Behavior Manager; in Student terminal 2 paste the
handshake request:

```bash
ros2 launch social_robot_behaviors social_behavior.launch.py
```

```bash
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: 'handshake'}"
```

The expected result is `Sequence accepted` on the Student and controlled
execution of `handshake.yaml` under Teacher supervision. Stop immediately using
the approved robot safety procedure if actual motion differs from the approved
fake-hardware test.

## 7. Operational recommendation

Use this policy for practical sessions:

1. Assign stable `192.168.1.x` addresses to the Teacher and all Student PCs.
2. Keep the Teacher's robot NIC fixed at `192.168.0.10`; do not route student
   DDS traffic through it.
3. Give Student 1, 2, 3 and 4 permanent domains `1`, `2`, `3` and `4`.
   Select the required Student domain in every Teacher ROS terminal.
4. Run Test A once after any switch or Wi-Fi configuration change.
5. If multicast is not demonstrably stable in both directions, use the
   fixed-peer unicast configuration in Test B for all sessions.
6. Before robot use, run Test C with fake hardware, then Test D under
   supervision.

For a small, fixed laboratory, unicast fixed peers is more predictable. For a
well-managed wired LAN with multicast enabled, multicast is easier to maintain
because no XML peer list needs updating. Avoid a mixed configuration: it makes
failures difficult to reproduce.
