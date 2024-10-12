import pyvesc
from pyvesc.VESC.messages import GetValues, SetDutyCycle
import serial
import time
import threading

serialports = ['/dev/ttyACM0', '/dev/ttyACM1']

def vesc_communication(port):
    with serial.Serial(port, baudrate=115200, timeout=0.05) as ser:
        try:
            while True:
                ser.write(pyvesc.encode(SetDutyCycle(0.03)))
                ser.write(pyvesc.encode_request(GetValues))

                if ser.in_waiting > 61:
                    (response, consumed) = pyvesc.decode(ser.read(61))
                    print(f"Port {port}:", response, consumed)

                    try:
                        print(f"Port {port} RPM:", response.rpm)
                    except:
                        pass

                time.sleep(0.1)

        except KeyboardInterrupt:
            ser.write(pyvesc.encode(SetDutyCycle(0)))

def get_values_example():
    threads = []
    for port in serialports:
        thread = threading.Thread(target=vesc_communication, args=(port,))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping all VESCs...")

if __name__ == "__main__":
    get_values_example()
