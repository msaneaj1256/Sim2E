
import multiprocessing as mp
import time
from turtle import speed

from project.simulation.robot import Robot
from project.simulation.scene import *
from project.simulation.state_machine import UnitySensingStateMachine, States
from project.simulation.controller import Control
from project.simulation.utilities import *
from project.simulation.mjremote import mjremote


'''
These are the params that unity sends:
index:  values
    0: AppStatus - 1 unity is on, 0 to turnoff the app                        
    1: RobStatus - 0 sleep, 1 start_config, 2 targeting               
    2: Xpos - x position in cm                                                
    3: Ypos - y position in cm                                                
    4: Zpos - z position in cm (for future support)                           
    5: Speed - speed multiplication factor [50, 300]/100                      
    6: PosTh - positive threshold                                             
    7: NegTh - negative threshold                                             
    8: Attach - connect simulation to real robot - 1 attached, 0 not attached 
    9: Record - record data : 1 recording is on, 0 recording is turned off    
    10: Stereo - for stereoscopic vision : 1 else monoscopic 0
    11: Lighting - 0 to 1.5 multiplied by 100
    12: Target - 0 to 6 [cube, sphere, tetrahedron, torus, mug, spinner, capsule]
'''

def run(from_build=False, sim_params=None, sim_positions=None):
    unity_src = "./unity_builds/build0002.x86_64 &"
    unity = None
    if from_build:
        os.system(unity_src)
        time.sleep(7)
    unity = mjremote()
    while not unity._s:  
        print("conecting...")
        unity.connect() 
    print("SUCCESS")
    
    xml_path = "./project/models/vx300s/vx300s_face_down.xml"
    scene = Mujocoation(xml_path, unity)
    robot = Robot(scene.model, scene.simulation)
    control = Control(robot, scene.simulation)
    moore = UnitySensingStateMachine(robot, scene, control, orientation=1)
    robot_status = 0
    while True:
        if sim_params[0] == 0:
            return
        
        speed = sim_params[5]
        if robot_status != sim_params[1]:
            robot_status = sim_params[1]
            if robot_status == 0:
                control.phase = 0
                control.theta_d = robot.nap
            elif robot_status == 1:
                control.phase = 0
                control.theta_d = moore.start_config
            elif robot_status == 2:
                pos = [sim_params[2]/100, sim_params[3]/100, sim_params[4]/100]
                moore.set_external_target(pos)
                moore.curr_state = States.INIT
        if robot_status == 2:
            moore.eval()
        control.PID(speed)
        scene.show_step()
        if sim_positions is not None:
            pos = robot.get_joints_pos()
            for i, p in enumerate(pos):
                sim_positions[i] = p

    
if __name__ == '__main__':
    
    run(True)
