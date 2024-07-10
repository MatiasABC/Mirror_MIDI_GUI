import serial
import time

def send_data(data, COM_port,ser):
    try:
        
            print(f"Sending: {data}")
            ser.write(data.encode())  # Encode string to bytes
    except serial.SerialException as e:
        print(f"A SerialException occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

with serial.Serial('COM8', 9600, timeout=1) as ser:
    while True:
        # Send data '1' to turn the pin on
        send_data('1', 'COM8',ser)
        time.sleep(2)
        # Send data '0' to turn the pin off
        send_data('0', 'COM8',ser)
        time.sleep(2)
        a
