# hexapod

## LinkedIn post 2023

I am thrilled to announce that I have graduated from AGH University of Krakow with a Bachelor of Science in Automatic Control and Robotics. Below is a brief description of my diploma project concerning subject of  "Hexapod walking robot design and implementation of real-time gait generating algorithm".
 

The main objective of this project was to design and develop a six-legged walking robot as well as enabling the machine to realize real-time gait by developing and implementing a control system that includes a gait generator - an abstract module on software level, which task would be to synchronize actuators.

Key functionalities:
·       Walking on a flat surface
·       Configurable movement parameters - type of gait, direction, speed
·       Unsophistacted assembly and disassembly of the machine
·       Modularity of the system
·       Remote control 

The thesis contained a description of theoretical issues concerning the broad research area of mobile walking robots. Issues included in the document cover in-depth specification of a system which is the walking machine created during the implementation of the project. 

Particular components of the robot were made using 3D printing technology. Detachable, threaded connections of components were used due to strength and simplicity of assembly/disassembly. Increasing the coefficient of friction of legs’ ends was achieved with rubber caps.

The constructed walking robot carries out an electrically driven, statically stable gait, which is remotely controlled by the user from a host computer.  The motion can be executed along the axis of the crab - it is possible to change the direction vector of the of movement at any time. 

Implemented control system allows elimination of interference arising in response to the environment, resulting in the preservation of permissible deviations of the actual trajectory. The implementation of gait generator is based on geometric relationships present in the machine's design and the module performs inverse kinematics calculations. The motion algorithm is designed to the extent to which the machine can efficiently move on a flat surface. 

The developed prototype has a wide scope of possible improvements in the future due to its high modularity:
·       Inertial navigation system - maintaining spatial orientation, determining position and velocity by measuring accelerations and angular velocities acting on the robot
·       Adaptation and maneuverability in varied (uneven) terrain
·       Autonomy of overcoming obstacles
·       Voice control of the walking robot
·       Data acquisition in a time-series database
·       Graphical user interface
·       Software implementation using the Robot Operating System framework


![Hexapod](./assets/hexapod.jpg)