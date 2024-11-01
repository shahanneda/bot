import numpy as np
import matplotlib.pyplot as plt
from madgwick_py.madgwickahrs import MadgwickAHRS, Quaternion

import time
import board
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3


class FilteredLSM6DS3():
    
    def __init__(self):
        self.sensor = LSM6DS3(board.I2C())
        self.ahrs = MadgwickAHRS(beta=0.008, zeta=0.)
        self.gyro_bias = np.array([0.,0.,0.])

    def calibrate(self):
        try:
           self.gyro_bias = np.loadtxt('gyro_bias.txt') 
        except FileNotFoundError:
            self.gyro_bias = np.array([0.,0.,0.])
            for _ in range(50):
                self.gyro_bias += np.array(self.sensor.gyro) / 50
                time.sleep(0.01)
            print('Calculated gyro bias:', self.gyro_bias)
            np.savetxt('gyro_bias.txt', self.gyro_bias)

        self.accel = np.array(self.sensor.acceleration)
        self.gyro = np.array(self.sensor.gyro) - self.gyro_bias
        self.t = time.time()

        self.quat = self._calculate_initial_q(self.accel)
        self.grav = self.quat_rotate(self.quat.conj(), [0, 0, 1])
        self.ahrs.quaternion = self.quat

    def robot_angle(self):
        self.update()
        # pitch = angle of robot, it's actually about x axis so technically roll
        gx, gy, gz = self.grav
        return np.degrees(np.atan2(gz, np.sqrt(gx**2 + gy**2)))
    
    def robot_angle_RAW(self):
        gx, gy, gz = self.grav_RAW
        return np.degrees(np.arctan2(gz, np.sqrt(gx**2 + gy**2)))


    def _calculate_initial_q(self, accel):
        acc_norm = accel / np.linalg.norm(accel)

        # Estimate initial roll and pitch from accelerometer
        initial_roll = np.arctan2(acc_norm[1], acc_norm[2])
        initial_pitch = np.arctan2(-acc_norm[0], np.sqrt(acc_norm[1]**2 + acc_norm[2]**2))
        initial_yaw = 0
        # print('Initial roll, pitch, yaw:', np.degrees(initial_roll), np.degrees(initial_pitch), np.degrees(initial_yaw))

        # Initialize quaternion using the from_angle_axis function
        initial_q = Quaternion.from_angle_axis(initial_roll, 1, 0, 0)
        initial_q = initial_q * Quaternion.from_angle_axis(initial_pitch, 0, 1, 0)
        initial_q = initial_q * Quaternion.from_angle_axis(initial_yaw, 0, 0, 1)
        return initial_q

    def update(self):
        # sensor readings
        self.accel = np.array(self.sensor.acceleration)
        self.gyro = np.array(self.sensor.gyro) - self.gyro_bias
        t = time.time()

        # store imu data
        self.accel_RAW = self.accel
        self.gyro_RAW = self.gyro
        self.quat_RAW = self._calculate_initial_q(self.accel_RAW)
        self.grav_RAW = self.quat_rotate(self.quat_RAW.conj(), [0, 0, 1])

        # filtering
        self.ahrs.samplePeriod = t - self.t
        self.ahrs.update_imu(self.gyro, self.accel)
        self.t = t

        # setting vars
        quat = self.ahrs.quaternion
        self.quat = quat.q
        self.grav = self.quat_rotate(quat.conj(), [0, 0, 1])

    def quat_rotate(self, q, v):
        """Rotate a vector v by a quaternion q"""
        qv = np.concatenate(([0], v))
        return (q * Quaternion(qv) * q.conj()).q[1:]


if __name__ == '__main__':
    imu = FilteredLSM6DS3()
    imu.calibrate()
    start_time = time.time()
    times = []
    quats = []
    accels = []
    gyros = []
    gravs = []
    pitches = []
    while time.time() < start_time + 10:
        pitch = imu.robot_angle()
        t = time.time()
        pitches.append(pitch)
        times.append(t)
        quats.append(imu.quat)
        accels.append(imu.accel)
        gyros.append(imu.gyro)
        gravs.append(imu.grav)

    times = np.array(times)-times[0]
    print('Average Hz:', 1/(np.mean(times[1:]-times[:-1])))

    plt.figure()
    gyros = np.stack(gyros)
    sx, sy, sz = np.std(gyros, axis=0)
    plt.title(f'Gyro, std=({sx:.4f}, {sy:.4f}, {sz:.4f})')
    plt.plot(times, gyros)
    plt.savefig('gyro.png')

    plt.figure()
    accels = np.stack(accels)
    sx, sy, sz = np.std(accels, axis=0)
    plt.title(f'Accel, std=({sx:.4f}, {sy:.4f}, {sz:.4f})')
    plt.plot(times, accels)
    plt.savefig('accel.png')


    def grav2pitch(gravs):
        return np.degrees(np.atan2(gravs[...,2], np.sqrt(gravs[...,0]**2 + gravs[...,1]**2)))
    
    plt.figure()
    plt.plot(times, grav2pitch(accels), label='noisy', alpha=0.4)
    plt.plot(times, pitches, label='filtered')
    plt.legend()
    plt.savefig('pitch.png')
