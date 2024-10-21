import serial 
import time

# Adjust the COM port and baud rate according to your setup
COM_PORT = 'COM3'  # Replace with your ESP32's COM port
BAUD_RATE = 115200
TIMEOUT = 1  # Timeout for reading from the serial port

def communicate():
    # Initialize the serial connection
    try:
        esp32_serial = serial.Serial(COM_PORT, BAUD_RATE, timeout=TIMEOUT)
        print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.")
        time.sleep(2)  # Wait for ESP32 to reboot and establish the serial connection

        while True:
            # Check if data is available from the ESP32
            if esp32_serial.in_waiting > 0:
                received_data = esp32_serial.readline().decode('utf-8').strip()
                print(f"Received from ESP32: {received_data}")

                # If the ESP32 sends "Infrared trigger", send "Notif accepted"
                if received_data == "Infrared trigger":
                # Wait for user input from the command line
                    verified_msg = "Notif accepted"

                # Validate user input before sending
                    if verified_msg == "Notif accepted":
                        print(f"Sending 'Notif accepted' to ESP32...")
                        esp32_serial.write((verified_msg + "\n").encode('utf-8'))
                        time.sleep(1)  # Small delay to prevent overwhelming the serial port

                        # Wait for the ESP32 to respond after receiving the input
                        if esp32_serial.in_waiting > 0:
                            response = esp32_serial.readline().decode('utf-8').strip()
                            print(f"ESP32 responded with: {response}")

                            # Check if the response is "Notif accepted"
                            if response == "Notif accepted":
                                print("ESP32 accepted the notification.")
                                break
                            else:
                                print("The response from ESP32 was not 'Notif accepted'. Please try again.")
                    else:
                        print("Invalid input. Please type 'Notif accepted'.")

    except serial.SerialException as e:
        print(f"Error connecting to {COM_PORT}: {e}")
    except KeyboardInterrupt:
        print("Program terminated by user.")
    finally:
        if esp32_serial.is_open:
            esp32_serial.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    communicate()
