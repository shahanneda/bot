import time
import serial
import odrive.enums
from sshkeyboard import listen_keyboard, stop_listening
import subprocess
from threading import Thread


class ODESC:
    AXIS_STATE_CLOSED_LOOP_CONTROL = 8
    ERROR_DICT = {k: v for k, v in odrive.enums.__dict__ .items() if k.startswith("AXIS_ERROR_")}

    def __init__(self, port, axis_num=0, dir=1):
        self.bus = serial.Serial(
            port=port,
            # baudrate=115200,
            baudrate=460800,
            # baudrate=921600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        self.axis_num = axis_num
        self.dir = dir

        # Clear the ASCII UART buffer
        self.bus.reset_input_buffer()
        self.bus.reset_output_buffer()

    def send_command(self, command: str):
        self.bus.reset_input_buffer()
        self.bus.write(f"{command}\n".encode())
        # Wait for the response if it's a read command
        if command.startswith('r'):
            # Read until a newline character is encountered
            response = self.bus.readline().decode('ascii').strip()
            # If the response is empty, print a debug message
            if response == '':
                print(f"No response received for command: {command}")
            return response

    def get_errors(self):
        error_code = -1
        error_name = 'Unknown error'
        # Get error code
        error_response = self.send_command(f'r axis{self.axis_num}.error')
        try:
            cleaned_response = ''.join(c for c in error_response if c.isdigit())
            error_code = int(cleaned_response)
            error_name = self.ERROR_DICT.get(error_code,error_name)
        except ValueError:
            print(f"Unexpected error response format: {error_response}")
            
        return error_code, error_name
        
    def enable_torque_mode(self):
        self.send_command(f'w axis{self.axis_num}.controller.config.control_mode 1')
        self.send_command(f'w axis{self.axis_num}.controller.config.input_mode 1')
        print(f"Axis {self.axis_num} set to torque control mode")

    def enable_velocity_mode(self):
        self.send_command(f'w axis{self.axis_num}.controller.config.control_mode 2')
        self.send_command(f'w axis{self.axis_num}.controller.config.input_mode 1')
        print(f"Axis {self.axis_num} set to velocity control mode")

    def start(self):
        self.send_command(f'w axis{self.axis_num}.requested_state 8')

    def set_speed_rpm(self, rpm):
        rps = rpm / 60
        self.send_command(f'w axis{self.axis_num}.controller.input_vel {rps * self.dir:.4f}')

    def set_torque_nm(self, nm):
        torque_bias = 0.05  # Small torque bias in Nm
        adjusted_torque = nm * self.dir + (torque_bias * self.dir * (1 if nm >= 0 else -1))
        self.send_command(f'w axis{self.axis_num}.controller.input_torque {adjusted_torque:.4f}')

    def get_speed_rpm(self):
        response = self.send_command(f'r axis{self.axis_num}.encoder.vel_estimate')
        return float(response) * self.dir * 60

    def get_position_turns(self):
        response = self.send_command(f'r axis{self.axis_num}.encoder.pos_estimate')
        return float(response) * self.dir

    def stop(self):
        self.send_command(f'w axis{self.axis_num}.controller.input_vel 0')
        self.send_command(f'w axis{self.axis_num}.controller.input_torque 0')
        self.send_command(f'w axis{self.axis_num}.requested_state 1')

    def check_errors(self):
        response = self.send_command(f'r axis{self.axis_num}.error')
        try:
            # Remove any non-numeric characters (like 'd' for decimal)
            cleaned_response = ''.join(c for c in response if c.isdigit())
            # print(f"Cleaned response: {cleaned_response}")
            return int(cleaned_response) != 0
        except ValueError:
            print(response)
            print(f"Unexpected response format: {response}")
            return True  # Assume there's an error if we can't parse the response

    def clear_errors(self):
        self.send_command(f'w axis{self.axis_num}.error 0')
        self.send_command(f'w axis{self.axis_num}.requested_state {self.AXIS_STATE_CLOSED_LOOP_CONTROL}')

def play_sound():
    try:
        result = subprocess.run(
            ['sudo', '-u', 'nedabot', 'aplay', '/home/nedabot/bot/vine.wav'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print("Sound Error:")
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
    except Exception as e:
        print(f"Exception playing sound: {str(e)}")

if __name__ == '__main__':
    motor1 = ODESC('/dev/ttyAMA1', axis_num=0, dir=-1)
    motor2 = ODESC('/dev/ttyAMA1', axis_num=1, dir=1)
    motor1.start()
    motor2.start()

    SPEED = 40
    last_sound_time = 0  # To prevent sound spam
    SOUND_COOLDOWN = 0.5  # Minimum seconds between sounds

    def press(key):
        global last_sound_time
        current_time = time.time()
        
        if key in ['w', 'a', 's', 'd']:
            if current_time - last_sound_time > SOUND_COOLDOWN:
                print("Playing sound")
                # play_sound()
                last_sound_time = current_time
        
        if key == 'w':
            print("Forward")
            motor1.set_speed_rpm(-SPEED)
            motor2.set_speed_rpm(-SPEED)
        elif key == 's':
            print("Backward")
            motor1.set_speed_rpm(SPEED)
            motor2.set_speed_rpm(SPEED)
        elif key == 'a':
            print("Left")
            motor1.set_speed_rpm(SPEED)
            motor2.set_speed_rpm(-SPEED)
        elif key == 'd':
            print("Right")
            motor1.set_speed_rpm(-SPEED)
            motor2.set_speed_rpm(SPEED)
        elif key == 'q':  # Add quit functionality
            print("Quit")
            stop_listening()

    def release(key):  # Added key parameter
        motor1.set_speed_rpm(0)
        motor2.set_speed_rpm(0)

    try:
        print("Use WASD to control the robot. Press 'q' to quit.")
        listen_keyboard(
            on_press=press,
            on_release=release,
            sequential=False
        )

    except Exception as e:
        print(e)
    finally:
        motor1.stop()
        motor2.stop()
