"""
MIDI Mirroring and Control Application
=======================================

This application is designed to interface with MIDI devices, enabling the mirroring of MIDI messages between two devices 
and providing additional functionality such as NRPN (Non-Registered Parameter Number) to CC (Control Change) conversion,
handling special key press combinations, and controlling on-air lights via serial communication.

Key Features:
-------------
- Mirror MIDI messages between two devices.
- Convert NRPN messages to CC and vice versa.
- Handle special key combinations based on GPIO triggers.
- Control on-air lights using serial communication.
- Process complex MIDI sequences with delay management and value thresholding.
- Multi-device support with DHD integration for enhanced control.

Components:
-----------
1. XML Configuration Parsing: Parses device configuration files in XML format.
2. MIDI Processing: Handles incoming MIDI messages, applies conversions, and outputs to specified devices.
3. GPIO Handling: Maps GPIO hex values to specific actions and MIDI messages.
4. On-Air Light Control: Toggles on-air lights based on button actions using serial communication.
5. Multi-Device Synchronization: Manages step mapping and message queuing for synchronizing actions across multiple devices.

Authors:
--------
This application was written by Matias Villalba in 2024.

License:
--------
This project is licensed under the MIT - see the LICENSE file for details.

"""

import sys
import threading
import xml.etree.ElementTree as ET
import os
import mido
import time
from collections import deque
from queue import Queue
from pynput.keyboard import Key, Controller
import serial
from serial.serialutil import SerialException


# Map GPIO hex values to corresponding fader button IDs and their toggle actions.
# Each GPIO hex value is mapped to a tuple consisting of:
#   - The fader button ID (an integer)
#   - The action to be performed ('toggle_on' or 'toggle_off')
gpio_to_fader_button_map = {
    "2A00": (1, 'toggle_on'),
    "2A01": (1, 'toggle_off'),
    "2B00": (2, 'toggle_on'),
    "2B01": (2, 'toggle_off'),
    "2C00": (3, 'toggle_on'),
    "2C01": (3, 'toggle_off'),
    "2D00": (4, 'toggle_on'),
    "2D01": (4, 'toggle_off')
}

# Initialize a Controller object from the pynput library to simulate keyboard input.
keyboard = Controller()

def trigger_key_press_id(id):
    """
    Trigger a specific key press combination based on the provided fader button ID.

    Args:
        id (int): The fader button ID for which the key press combination should be triggered.
                  Valid IDs are from 1 to 4.

    Key Press Combinations:
    - ID 1: Ctrl + Alt + F1
    - ID 2: Ctrl + Alt + F2
    - ID 3: Ctrl + Alt + F3
    - ID 4: Ctrl + Alt + F4

    The function simulates pressing and releasing the keys in sequence. If an invalid
    ID is provided, the function prints an error message.
    """
    
    # Define the key combinations for each fader button ID.
    Toggle_Key_presses = [
        [Key.ctrl, Key.alt, Key.f1],  # ID 1
        [Key.ctrl, Key.alt, Key.f2],  # ID 2
        [Key.ctrl, Key.alt, Key.f3],  # ID 3
        [Key.ctrl, Key.alt, Key.f4]   # ID 4
    ]
    
    # Initialize a new keyboard controller instance.
    keyboard = Controller()
    
    # Check if the provided ID is valid (within the range of available key combinations).
    if 0 <= id < len(Toggle_Key_presses):
        # Retrieve the key combination corresponding to the provided ID.
        key_combination = Toggle_Key_presses[id-1]
        
        print(f"Triggering key press combination for ID {id}: {key_combination}")

        # Simulate pressing each key in the combination.
        for key in key_combination:
            print(f"Pressing {key}")
            keyboard.press(key)
        
        # Simulate releasing each key in the combination.
        for key in key_combination:            
            keyboard.release(key)
    else:
        # Print an error message if the provided ID is invalid.
        print("Invalid ID. Please provide a valid ID between 0 and", len(Toggle_Key_presses) - 1)

def nrpn_to_nrpn(nrpn_number, data_value, input_channel, channel_map, nrpn_to_nrpn_map, threshold=20, min_interval=0.5, max_interval=0.7):
    """
    Convert an incoming NRPN (Non-Registered Parameter Number) message to another NRPN message with optional value change
    and timing thresholds. This function is used to map NRPN messages from one channel to another and optionally filter
    out insignificant changes to avoid overwhelming the MIDI output.

    Args:
        nrpn_number (int): The incoming NRPN number to be converted.
        data_value (int): The data value associated with the NRPN message.
        input_channel (int): The MIDI channel of the incoming NRPN message.
        channel_map (dict): A dictionary mapping input channels to output channels.
        nrpn_to_nrpn_map (dict): A mapping of incoming NRPN numbers to target NRPN numbers and default output channels.
        threshold (int, optional): The minimum change in data value required to trigger a new NRPN message. Default is 20.
        min_interval (float, optional): The minimum time interval (in seconds) between successive NRPN messages for the same target. Default is 0.5 seconds.
        max_interval (float, optional): The maximum time interval (in seconds) after which an NRPN message will be sent regardless of the value change. Default is 0.7 seconds.

    Returns:
        list: A list of MIDI messages to be sent out if the conversion is successful, or None if no message should be sent.
    """

    # Check if the incoming NRPN number is in the mapping table
    if nrpn_number in nrpn_to_nrpn_map:
        # Retrieve the target NRPN number and the default output channel from the mapping
        target_nrpn_number, default_output_channel = nrpn_to_nrpn_map[nrpn_number]
        
        # Determine the output channel based on the input channel, or use the default output channel
        output_channel = channel_map.get(input_channel, default_output_channel)

        # Initialize storage for last values and timestamps if not already set up
        if not hasattr(nrpn_to_nrpn, 'last_values'):
            nrpn_to_nrpn.last_values = {}
        if not hasattr(nrpn_to_nrpn, 'last_times'):
            nrpn_to_nrpn.last_times = {}

        # Create a key to uniquely identify the target NRPN on the output channel
        key = (output_channel, target_nrpn_number)
        current_time = time.time()

        # If this is the first time processing this NRPN, store its value and timestamp, then return None
        if key not in nrpn_to_nrpn.last_values:
            nrpn_to_nrpn.last_values[key] = data_value
            nrpn_to_nrpn.last_times[key] = current_time
            return None

        # Retrieve the last known value and time for this NRPN
        last_value = nrpn_to_nrpn.last_values[key]
        last_time = nrpn_to_nrpn.last_times[key]

        # Calculate the change in value and the time elapsed since the last message
        value_change = abs(data_value - last_value)
        time_elapsed = current_time - last_time

        # If the value change exceeds the threshold or the maximum interval has passed, send a new NRPN message
        if (value_change >= threshold or time_elapsed >= max_interval):
            # Update the stored value and timestamp
            nrpn_to_nrpn.last_values[key] = data_value
            nrpn_to_nrpn.last_times[key] = current_time

            # Split the data value into MSB (Most Significant Byte) and LSB (Least Significant Byte)
            msb = (data_value >> 7) & 0x7F
            lsb = data_value & 0x7F

            # Return a list of MIDI control change messages to represent the NRPN message
            return [
                mido.Message('control_change', control=99, value=(target_nrpn_number >> 7) & 0x7F, channel=output_channel),  # NRPN MSB
                mido.Message('control_change', control=98, value=target_nrpn_number & 0x7F, channel=output_channel),       # NRPN LSB
                mido.Message('control_change', control=6, value=msb, channel=output_channel),                              # Data Entry MSB
                mido.Message('control_change', control=38, value=lsb, channel=output_channel)                              # Data Entry LSB
            ]
        # If the minimum interval hasn't passed, skip sending a new message
        elif time_elapsed < min_interval:
            return None
    # If the NRPN number is not in the mapping table, return None
    return None

def cc_to_cc(cc_number, data_value, input_channel, channel_map, cc_to_cc_map):
    """
    Convert an incoming Control Change (CC) message to another CC message based on a mapping.
    
    This function maps an incoming CC number to a target CC number, possibly changing the output channel.
    It scales the data value to the appropriate range for MIDI and returns a new MIDI message.

    Args:
        cc_number (int): The incoming CC number to be converted.
        data_value (int): The data value associated with the CC message.
        input_channel (int): The MIDI channel of the incoming CC message.
        channel_map (dict): A dictionary mapping input channels to output channels.
        cc_to_cc_map (dict): A mapping of incoming CC numbers to target CC numbers and default output channels.

    Returns:
        mido.Message: A new MIDI Control Change message with the mapped CC number and data value, or None if the CC number is not in the map.
    """

    # Check if the incoming CC number is in the mapping table.
    if cc_number not in cc_to_cc_map:
        return None  # If not, return None to indicate no conversion is needed.

    # Retrieve the target CC number and the default output channel from the mapping.
    target_cc_number, default_output_channel = cc_to_cc_map[cc_number]
    
    # Determine the output channel based on the input channel, or use the default output channel.
    output_channel = channel_map.get(input_channel, default_output_channel)

    # Scale the data value to ensure it fits within the 7-bit MIDI range (0-127).
    scaled_data_value = data_value & 0x7F

    # Return a new MIDI Control Change message with the mapped CC number, scaled data value, and output channel.
    return mido.Message('control_change', control=target_cc_number, value=scaled_data_value, channel=output_channel)


def cc_to_nrpn(cc_number, data_value, input_channel, channel_map, cc_to_nrpn_map):
    """
    Convert an incoming Control Change (CC) message to an NRPN (Non-Registered Parameter Number) message.

    This function maps an incoming CC number to a corresponding NRPN number and converts the data value accordingly.
    The output is a series of MIDI messages that represent the NRPN message.

    Args:
        cc_number (int): The incoming CC number to be converted.
        data_value (int): The data value associated with the CC message, must be in the range 0-127.
        input_channel (int): The MIDI channel of the incoming CC message.
        channel_map (dict): A dictionary mapping input channels to output channels.
        cc_to_nrpn_map (dict): A mapping of incoming CC numbers to NRPN numbers and default output channels.

    Returns:
        list: A list of MIDI messages representing the NRPN, or None if the CC number is not in the map.
    
    Raises:
        ValueError: If the data_value is not within the valid MIDI range (0-127).
    """

    # Ensure the data value is within the valid MIDI range (0-127).
    if not (0 <= data_value <= 127):
        raise ValueError("data_value must be between 0 and 127")
        
    # Check if the incoming CC number is in the CC to NRPN mapping table.
    if cc_number in cc_to_nrpn_map:
        # Retrieve the corresponding NRPN number and default output channel from the mapping.
        nrpn_number, nrpn_output_channel = cc_to_nrpn_map[cc_number]
        
        # Determine the output channel based on the input channel, or use the default NRPN output channel.
        output_channel = channel_map.get(input_channel, nrpn_output_channel)
        
        # Split the NRPN number into MSB (Most Significant Byte) and LSB (Least Significant Byte).
        msb = (nrpn_number >> 7) & 0x7F
        lsb = nrpn_number & 0x7F

        # Return a list of MIDI control change messages representing the NRPN message.
        return [
            mido.Message('control_change', control=99, value=msb, channel=output_channel),  # NRPN MSB
            mido.Message('control_change', control=98, value=lsb, channel=output_channel),  # NRPN LSB
            mido.Message('control_change', control=6, value=data_value, channel=output_channel),  # Data Entry MSB
            mido.Message('control_change', control=38, value=0, channel=output_channel)  # Data Entry LSB (always 0 in this case)
        ]
    else:
        # If the CC number is not found in the mapping, return None.
        pass
    return None


def nrpn_to_cc(nrpn_number, data_value, input_channel, channel_map, nrpn_to_cc_map, threshold=20, min_interval=0.5, max_interval=0.7):
    """
    Convert an incoming NRPN (Non-Registered Parameter Number) message to a Control Change (CC) message.
    
    This function maps an NRPN number to a CC number and converts the data value accordingly. It applies optional
    filtering based on value changes and timing to prevent sending excessive MIDI messages.

    Args:
        nrpn_number (int): The incoming NRPN number to be converted.
        data_value (int): The data value associated with the NRPN message.
        input_channel (int): The MIDI channel of the incoming NRPN message.
        channel_map (dict): A dictionary mapping input channels to output channels.
        nrpn_to_cc_map (dict): A mapping of incoming NRPN numbers to CC numbers and default output channels.
        threshold (int, optional): The minimum change in data value required to trigger a new CC message. Default is 20.
        min_interval (float, optional): The minimum time interval (in seconds) between successive CC messages for the same target. Default is 0.5 seconds.
        max_interval (float, optional): The maximum time interval (in seconds) after which a CC message will be sent regardless of the value change. Default is 0.7 seconds.

    Returns:
        mido.Message or None: A new MIDI Control Change message if the conditions are met, or None if no message should be sent.
    """

    # Check if the incoming NRPN number is in the NRPN to CC mapping table.
    if nrpn_number in nrpn_to_cc_map:
        # Retrieve the corresponding CC number and default output channel from the mapping.
        cc_number, default_output_channel = nrpn_to_cc_map[nrpn_number]
        
        # Determine the output channel based on the input channel, or use the default output channel.
        output_channel = channel_map.get(input_channel, default_output_channel)

        # Initialize storage for last values and timestamps if not already set up.
        if not hasattr(nrpn_to_cc, 'last_values'):
            nrpn_to_cc.last_values = {}
        if not hasattr(nrpn_to_cc, 'last_times'):
            nrpn_to_cc.last_times = {}

        # Create a key to uniquely identify the target CC on the output channel.
        key = (output_channel, cc_number)
        current_time = time.time()

        # If this is the first time processing this NRPN, store its value and timestamp, then return None.
        if key not in nrpn_to_cc.last_values:
            nrpn_to_cc.last_values[key] = data_value
            nrpn_to_cc.last_times[key] = current_time
            return None

        # Retrieve the last known value and time for this NRPN to CC conversion.
        last_value = nrpn_to_cc.last_values[key]
        last_time = nrpn_to_cc.last_times[key]

        # Calculate the change in value and the time elapsed since the last message.
        value_change = abs(data_value - last_value)
        time_elapsed = current_time - last_time

        # If the value change exceeds the threshold or the maximum interval has passed, send a new CC message.
        if (value_change >= threshold or time_elapsed >= max_interval):
            # Update the stored value and timestamp.
            nrpn_to_cc.last_values[key] = data_value
            nrpn_to_cc.last_times[key] = current_time

            # Scale the data value to fit within the 7-bit MIDI range (0-127).
            scaled_data_value = data_value >> 7

            # Return a new MIDI Control Change message with the mapped CC number, scaled data value, and output channel.
            return mido.Message('control_change', control=cc_number, value=scaled_data_value, channel=output_channel)
        elif time_elapsed < min_interval:
            # If the minimum interval hasn't passed, skip sending a new message.
            return None
    # If the NRPN number is not in the mapping table, return None.
    return None


def is_nrpn_control(control):
    """
    Check if a given control number is part of the NRPN (Non-Registered Parameter Number) control set.
    
    NRPN messages typically use the following control change numbers:
    - 98: NRPN LSB (Least Significant Byte)
    - 99: NRPN MSB (Most Significant Byte)
    - 6: Data Entry MSB
    - 38: Data Entry LSB

    Args:
        control (int): The control number to check.

    Returns:
        bool: True if the control number is part of the NRPN set, False otherwise.
    """
    return control in [98, 99, 6, 38]

def process_nrpn_messages(nrpn_cache, message):
    """
    Process incoming MIDI messages related to NRPN (Non-Registered Parameter Number) and assemble
    them into a complete NRPN message.

    This function stores parts of the NRPN message in a cache as they arrive, and once all necessary
    parts (MSB, LSB, data MSB, data LSB) are received, it assembles and returns the complete NRPN number 
    and data value.

    Args:
        nrpn_cache (dict): A dictionary used to store parts of the NRPN message as they are received.
        message (mido.Message): The incoming MIDI message to process.

    Returns:
        tuple: A tuple containing the assembled NRPN number and data value if all parts are received, or
               None if the message is incomplete.
    """
    
    # Check if the message is an NRPN control change and store the corresponding value in the cache.
    if message.control == 99:
        nrpn_cache['msb'] = message.value  # Store the NRPN MSB (Most Significant Byte).
    elif message.control == 98:
        nrpn_cache['lsb'] = message.value  # Store the NRPN LSB (Least Significant Byte).
    elif message.control == 6:
        nrpn_cache['data_msb'] = message.value  # Store the Data Entry MSB.
    elif message.control == 38:
        nrpn_cache['data_lsb'] = message.value  # Store the Data Entry LSB.

    # Check if all parts of the NRPN message (MSB, LSB, data MSB, data LSB) have been received.
    if 'msb' in nrpn_cache and 'lsb' in nrpn_cache and 'data_msb' in nrpn_cache and 'data_lsb' in nrpn_cache:
        # Assemble the NRPN number and data value from the cached parts.
        nrpn_number = (nrpn_cache['msb'] << 7) + nrpn_cache['lsb']
        data_value = (nrpn_cache.get('data_msb', 0) << 7) + nrpn_cache.get('data_lsb', 0)
        
        # Clear the cache as the NRPN message has been fully assembled.
        nrpn_cache.clear()
        
        # Return the assembled NRPN number and data value as a tuple.
        return nrpn_number, data_value
    
    # If the NRPN message is incomplete, return None.
    return None


def radio_assist_midi(device, input_device_name, output_device_name, step_map, DHD_enabled, stdin_queue_device, Radio_Assist_Faders_Location, On_air_lights_enabled, ser, delay=0.0001):
    """
    Handle MIDI processing and triggering of associated actions for radio assist devices.

    This function reads MIDI messages from an input device, processes them according to a provided mapping,
    and sends the appropriate messages to an output device. It also manages special actions like triggering
    on-air lights and handling custom messages based on button presses.

    Args:
        device (str): The name or identifier of the device being controlled.
        input_device_name (str): The name of the MIDI input device.
        output_device_name (str): The name of the MIDI output device.
        step_map (dict): A mapping of button IDs to actions and associated MIDI steps.
        DHD_enabled (bool): Flag to enable or disable Digital Hybrid Device (DHD) integration.
        stdin_queue_device (Queue): Queue for processing incoming standard input messages.
        Radio_Assist_Faders_Location (dict): Mapping of fader button IDs to specific cart stack numbers.
        On_air_lights_enabled (str): Flag to enable or disable on-air light control.
        ser (serial.Serial): Serial connection object for controlling on-air lights.
        delay (float, optional): Delay time between processing steps, default is 0.0001 seconds.
    """
    
    # Initialize a queue to store messages to be sent and a buffer to track recent messages.
    message_queue = deque()
    message_buffer = deque(maxlen=4)

    def handle_on_air_lights(On_air_lights_enabled, button_id, action, ser):
        """
        Handle the control of on-air lights based on button actions.

        Args:
            On_air_lights_enabled (str): Flag indicating if on-air lights are enabled.
            button_id (int): The ID of the button being pressed.
            action (str): The action being performed ('toggle_on' or 'toggle_off').
            ser (serial.Serial): Serial connection object for controlling on-air lights.
        """
        if On_air_lights_enabled == "True" and button_id == 1:
            try:
                if action.lower() == 'toggle_on':
                    print("Light ON!")
                    ser.write(b'1')
                elif action.lower() == 'toggle_off':
                    print("Light OFF!")
                    ser.write(b'0')
            except SerialException as e:
                print(f"An error occurred: {e}")

    def handle_special_message(button_id):
        """
        Handle special messages associated with specific button IDs.

        Args:
            button_id (int): The ID of the button being pressed.

        Returns:
            int or None: The cart stack number associated with the button ID, or None if not found.
        """
        for Cart_Stack_number, allocated_button in Radio_Assist_Faders_Location.items():
            if allocated_button == button_id:
                print(f"Special message detected for button {button_id}")
                return Cart_Stack_number
        return None

    def send_messages():
        """
        Send all messages currently in the message queue to the output device.
        """
        while message_queue:
            msg = message_queue.popleft()
            outport.send(msg)

    def process_stdin_messages():
        """
        Process messages received via standard input and send them to the MIDI output device.

        This function continuously reads from the stdin queue, converts the messages into MIDI format,
        and queues them for sending to the output device.
        """
        try:
            while True:
                step, device_in_queue = stdin_queue_device.get()
                try:
                    if " AND " in step:
                        steps_list = step.split(" AND ")
                        for s in steps_list:
                            message = mido.Message.from_str(s)
                            message_queue.append(message)
                            print("sending message:", message)
                    else:
                        message = mido.Message.from_str(step)
                        message_queue.append(message)
                        print("sending message:", message)
                    send_messages()
                    print("output device", output_device_name)
                except Exception as e:
                    print(f"Error converting message from string for {device_in_queue}: {e}")
                finally:
                    stdin_queue_device.task_done()
        except Exception as e:
            print(f"Error processing stdin messages: {e}")

    # Open MIDI input and output ports and start processing messages.
    with mido.open_input(input_device_name) as inport, mido.open_output(output_device_name) as outport:
        print(f"Processing MIDI for {input_device_name} to {output_device_name}...")

        # Start a separate thread to handle messages coming from stdin.
        stdin_thread = threading.Thread(target=process_stdin_messages)
        stdin_thread.start()

        while True:
            if DHD_enabled:
                stdin_queue_device.join()

            # Read all pending MIDI messages from the input device.
            messages = list(inport.iter_pending())
            if messages:
                for message in messages:
                    message_buffer.append(message)
                    
                    # Iterate over the step map to match incoming messages with actions.
                    for button_id, actions in step_map.items():
                        for action, steps in actions.items():
                            for step in steps:
                                # Handle sequences of messages (e.g., AND conditions).
                                if " AND " in step[device]:
                                    steps_list = step[device].split(" AND ")
                                    if all(any(str(msg) == s for msg in message_buffer) for s in steps_list):
                                        print(f"Complete sequence matches for button {button_id}, action {action}")
                                        special_message_result = handle_special_message(button_id)
                                        if On_air_lights_enabled == "True":
                                            handle_on_air_lights(On_air_lights_enabled, button_id, action, ser)
                                        if special_message_result and DHD_enabled:
                                            trigger_key_press_id(special_message_result)
                                        message_buffer.clear()
                                        break
                                # Handle single message matches.
                                elif str(message) == step[device]:
                                    print(f"Message {message} matches step_map for button {button_id}, action {action}")
                                    special_message_result = handle_special_message(button_id)
                                    if On_air_lights_enabled == "True":
                                        handle_on_air_lights(On_air_lights_enabled, button_id, action, ser)
                                    if special_message_result and DHD_enabled:
                                        trigger_key_press_id(special_message_result)
                                    message_buffer.clear()
                                    break

                # Send all messages queued for output.
                send_messages()


            
def mirror_midi(device, input_device_name, output_device_name, channel_map, cc_to_cc_map_device1, nrpn_to_nrpn_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map, step_map, DHD_enabled, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location, convert_func, On_air_lights_enabled, ser, delay=0.0001):
    """
    Mirror MIDI messages between two devices, applying necessary conversions and handling special actions.

    This function listens to MIDI messages from an input device, processes them according to a mapping, and sends the
    appropriate messages to an output device. It can convert between different types of MIDI messages (e.g., CC to NRPN),
    handle special actions like triggering on-air lights, and synchronize messages across devices.

    Args:
        device (str): The name or identifier of the current device.
        input_device_name (str): The name of the MIDI input device.
        output_device_name (str): The name of the MIDI output device.
        channel_map (dict): A dictionary mapping input channels to output channels.
        cc_to_cc_map_device1 (dict): Mapping of CC numbers for device 1.
        nrpn_to_nrpn_map_device1 (dict): Mapping of NRPN numbers for device 1.
        cc_to_cc_map_device2 (dict): Mapping of CC numbers for device 2.
        nrpn_to_nrpn_map_device2 (dict): Mapping of NRPN numbers for device 2.
        nrpn_to_cc_map (dict): Mapping of NRPN numbers to CC numbers.
        cc_to_nrpn_map (dict): Mapping of CC numbers to NRPN numbers.
        step_map (dict): A mapping of button IDs to actions and associated MIDI steps.
        DHD_enabled (bool): Flag to enable or disable Digital Hybrid Device (DHD) integration.
        stdin_queue_device1 (Queue): Queue for processing standard input messages for device 1.
        stdin_queue_device2 (Queue): Queue for processing standard input messages for device 2.
        Radio_Assist_Faders_Location (dict): Mapping of fader button IDs to specific cart stack numbers.
        convert_func (function): Function used for converting MIDI messages (e.g., cc_to_cc, nrpn_to_nrpn).
        On_air_lights_enabled (str): Flag to enable or disable on-air light control.
        ser (serial.Serial): Serial connection object for controlling on-air lights.
        delay (float, optional): Delay time between processing steps, default is 0.0001 seconds.
    """

    # Initialize a queue to store messages to be sent, and a buffer to track recent messages.
    message_queue = deque()
    last_send_time = time.time()
    nrpn_cache = {}
    message_buffer = deque(maxlen=4)

    def handle_on_air_lights(On_air_lights_enabled, button_id, action, ser):
        """
        Handle the control of on-air lights based on button actions.

        Args:
            On_air_lights_enabled (str): Flag indicating if on-air lights are enabled.
            button_id (int): The ID of the button being pressed.
            action (str): The action being performed ('toggle_on' or 'toggle_off').
            ser (serial.Serial): Serial connection object for controlling on-air lights.
        """
        if On_air_lights_enabled == "True" and button_id == 1:
            try:
                if action.lower() == 'toggle_on':
                    print("Light ON!")
                    ser.write((b'1'))
                elif action.lower() == 'toggle_off':
                    print("Light OFF!")
                    ser.write((b'0'))
            except SerialException as e:
                print(f"An error occurred with the on Air Light: {e}")

    def handle_special_message(button_id):
        """
        Handle special messages associated with specific button IDs.

        Args:
            button_id (int): The ID of the button being pressed.

        Returns:
            int or None: The cart stack number associated with the button ID, or None if not found.
        """
        for Cart_Stack_number, allocated_button in Radio_Assist_Faders_Location.items():
            if allocated_button == button_id:
                print(f"Special message detected for button {button_id}")
                return Cart_Stack_number
        return None

    def send_messages():
        """
        Send all messages currently in the message queue to the output device.
        """
        nonlocal last_send_time
        while message_queue:
            msg = message_queue.popleft()
            outport.send(msg)
        last_send_time = time.time()

    def process_stdin_messages_device1():
        """
        Process messages received via standard input for device 1 and send them to the MIDI output device.

        This function continuously reads from the stdin queue for device 1, converts the messages into MIDI format,
        and queues them for sending to the output device.
        """
        try:
            while True:
                step, device_in_queue = stdin_queue_device1.get()
                try:
                    if " AND " in step:
                        steps_list = step.split(" AND ")
                        for s in steps_list:
                            message = mido.Message.from_str(s)
                            message_queue.append(message)
                            print("sending message:", message)
                    else:
                        message = mido.Message.from_str(step)
                        message_queue.append(message)
                        print("sending message:", message)
                    send_messages()
                    print("output device", output_device_name)
                except Exception as e:
                    print(f"Error converting message from string for {device_in_queue}: {e}")
                finally:
                    stdin_queue_device1.task_done()
        except Exception as e:
            print(f"Error processing stdin messages: {e}")

    def process_stdin_messages_device2():
        """
        Process messages received via standard input for device 2 and send them to the MIDI output device.

        This function continuously reads from the stdin queue for device 2, converts the messages into MIDI format,
        and queues them for sending to the output device.
        """
        try:
            while True:
                step, device_in_queue = stdin_queue_device2.get()
                try:
                    if " AND " in step:
                        steps_list = step.split(" AND ")
                        for s in steps_list:
                            message = mido.Message.from_str(s)
                            message_queue.append(message)
                            print("sending message:", message)
                    else:
                        message = mido.Message.from_str(step)
                        message_queue.append(message)
                        print("sending message:", message)
                    send_messages()
                    print("output device", output_device_name)
                except Exception as e:
                    print(f"Error converting message from string for {device_in_queue}: {e}")
                finally:
                    stdin_queue_device2.task_done()
        except Exception as e:
            print(f"Error processing stdin messages: {e}")

    # Open MIDI input and output ports and start processing messages.
    with mido.open_input(input_device_name) as inport, mido.open_output(output_device_name) as outport:
        print(f"Mirroring MIDI from {input_device_name} to {output_device_name}...")
        opposite_device = "device1" if device == "device2" else "device2"
        
        # Start a separate thread to handle messages coming from the stdin queue of the opposite device.
        if device == "device1":
            stdin_thread = threading.Thread(target=process_stdin_messages_device2)
            stdin_thread.start()
        elif device == "device2":
            stdin_thread = threading.Thread(target=process_stdin_messages_device1)
            stdin_thread.start()

        while True:
            if DHD_enabled:
                stdin_queue_device1.join()
                stdin_queue_device2.join()

            # Read all pending MIDI messages from the input device.
            messages = list(inport.iter_pending())
            if messages:
                for message in messages:
                    print(f"Received MIDI message: {message}")
                    message_buffer.append(message)

                    converted_message = None
                    
                    # Handle Control Change (CC) messages and apply conversions if necessary.
                    if message.type == 'control_change':
                        if convert_func == cc_to_cc:
                            converted_message = cc_to_cc(message.control, message.value, message.channel, channel_map, cc_to_cc_map_device1)
                        elif convert_func == nrpn_to_nrpn and is_nrpn_control(message.control):
                            nrpn_data = process_nrpn_messages(nrpn_cache, message)
                            if nrpn_data:
                                nrpn_number, data_value = nrpn_data
                                converted_message = nrpn_to_nrpn(nrpn_number, data_value, message.channel, channel_map, nrpn_to_nrpn_map_device1)
                        elif convert_func == cc_to_nrpn:
                            converted_message = cc_to_nrpn(message.control, message.value, message.channel, channel_map, cc_to_nrpn_map)
                        elif convert_func == nrpn_to_cc and is_nrpn_control(message.control):
                            nrpn_data = process_nrpn_messages(nrpn_cache, message)
                            if nrpn_data:
                                nrpn_number, data_value = nrpn_data
                                converted_message = nrpn_to_cc(nrpn_number, data_value, message.channel, channel_map, nrpn_to_cc_map)
                    
                    # If a converted message exists, add it to the message queue.
                    if converted_message:
                        if isinstance(converted_message, list):
                            message_queue.extend(converted_message)
                            message_buffer.clear()
                        else:
                            message_queue.append(converted_message)
                        continue

                    # If no conversion is needed and no NRPN data is being cached, handle message matching.
                    if converted_message is None and not nrpn_cache:
                        for button_id, actions in step_map.items():
                            for action, steps in actions.items():
                                for step in steps:
                                    if " AND " in step[device]:
                                        steps_list = step[device].split(" AND ")
                                        if all(any(str(msg) == s for msg in message_buffer) for s in steps_list):
                                            print(f"Complete sequence matches for button {button_id}, action {action}")
                                            special_message_result = handle_special_message(button_id)
                                            print("special message", special_message_result)
                                            if On_air_lights_enabled == "True":
                                                handle_on_air_lights(On_air_lights_enabled, button_id, action, ser)
                                            if special_message_result and DHD_enabled:
                                                trigger_key_press_id(special_message_result)
                                            else:
                                                for opposite_step in step_map[button_id][action]:
                                                    for step_msg in opposite_step[opposite_device].split(" AND "):
                                                        try:
                                                            msg = mido.Message.from_str(step_msg)
                                                            message_queue.append(msg)
                                                            print(f"Appending mirrored step to queue for {opposite_device}: {msg}")
                                                        except Exception as e:
                                                            print(f"Error converting mirrored step from string: {e}")
                                            message_buffer.clear()
                                            break
                                    elif str(message) == step[device]:
                                        print(f"Message {message} matches step_map for button {button_id}, action {action}")
                                        special_message_result = handle_special_message(button_id)
                                        if On_air_lights_enabled == "True":
                                            handle_on_air_lights(On_air_lights_enabled, button_id, action, ser)
                                        if special_message_result and DHD_enabled:
                                            trigger_key_press_id(special_message_result)
                                        else:
                                            for step_msg in step_map[button_id][action][0][opposite_device].split(" AND "):
                                                try:
                                                    msg = mido.Message.from_str(step_msg)
                                                    message_queue.append(msg)
                                                    print(f"Appending mirrored step to queue for {opposite_device}: {msg}")
                                                except Exception as e:
                                                    print(f"Error converting mirrored step from string: {e}")
                                        message_buffer.clear()
                                        break

                # Send all messages queued for output.
                send_messages()
            

def read_xml_config(file_name):
    """
    Read and parse an XML configuration file.

    This function constructs the full path to the XML configuration file based on the given file name,
    attempts to read and parse the file, and returns the root element of the XML tree.

    Args:
        file_name (str): The name of the XML configuration file to read.

    Returns:
        ElementTree.Element or None: The root element of the parsed XML tree if successful, or None if an error occurs.
    """

    # Construct the full path to the XML configuration file located in the 'configs' directory.
    configs_path = os.path.join(os.path.dirname(__file__), '..', 'configs', file_name)
    full_path = os.path.normpath(configs_path)
    
    try:
        # Attempt to parse the XML file and get the root element of the XML tree.
        tree = ET.parse(full_path)
        root = tree.getroot()
        print(f"Read XML config from {full_path}")
        return root
    except ET.ParseError as e:
        # Handle errors that occur if the XML file is malformed or cannot be parsed.
        print(f"Error parsing XML file {full_path}: {e}")
    except FileNotFoundError:
        # Handle the case where the XML file cannot be found at the specified path.
        print(f"XML file not found: {full_path}")
    
    # Return None if the file could not be read or parsed.
    return None

def parse_config(xml_root):
    """
    Parse the XML root element and extract the MIDI configuration.

    This function processes the XML tree, extracting information about MIDI input/output devices,
    channels, faders, and fader buttons. It returns a dictionary containing the configuration details.

    Args:
        xml_root (ElementTree.Element): The root element of the parsed XML tree.

    Returns:
        dict: A dictionary containing the parsed MIDI configuration, including:
            - 'midi_in_name': The name of the MIDI input device.
            - 'midi_out_name': The name of the MIDI output device.
            - 'channel': The MIDI channel to be used.
            - 'faders': A dictionary of fader configurations.
            - 'fader_buttons': A dictionary of fader button configurations.
    """

    # Initialize the configuration dictionary with basic MIDI settings.
    config = {
        'midi_in_name': xml_root.find('./midi/midi_in_name').text,   # MIDI input device name
        'midi_out_name': xml_root.find('./midi/midi_out_name').text, # MIDI output device name
        'channel': int(xml_root.find('./midi/channel').text),        # MIDI channel
        'faders': {},                                                # Dictionary for fader configurations
        'fader_buttons': {}                                           # Dictionary for fader button configurations
    }
    
    # Parse the fader configurations from the XML and add them to the config dictionary.
    for fader in xml_root.findall('./faders/fader'):
        fader_id = int(fader.get('id'))  # Unique ID for each fader
        fader_config = {
            'type': fader.get('type'),   # Type of the fader (e.g., control change, NRPN)
            'value': int(fader.get('value')),  # Value associated with the fader
        }
        config['faders'][fader_id] = fader_config  # Add the fader configuration to the dictionary

    # Parse the fader button configurations from the XML and add them to the config dictionary.
    for button in xml_root.findall('./fader_buttons/fader_button'):
        button_id = int(button.get('id'))          # Unique ID for each fader button
        button_type = button.get('type')           # Type of the button (e.g., toggle, momentary)
        button_value = int(button.get('value'))    # Value associated with the button

        # Initialize the button configuration with its type, value, and toggle actions.
        button_config = {
            'type': button_type,
            'value': button_value,
            'toggle_on': [],   # List to store toggle on actions
            'toggle_off': []   # List to store toggle off actions
        }

        # If the toggle_on element is present, parse its actions and add them to the config.
        toggle_on = button.find('toggle_on')
        if toggle_on is not None:
            button_config['toggle_on'] = [msg.strip() for msg in toggle_on.text.strip().split(';')]

        # If the toggle_off element is present, parse its actions and add them to the config.
        toggle_off = button.find('toggle_off')
        if toggle_off is not None:
            button_config['toggle_off'] = [msg.strip() for msg in toggle_off.text.strip().split(';')]

        # Add the fader button configuration to the dictionary.
        config['fader_buttons'][button_id] = button_config

    return config  # Return the fully constructed configuration dictionary

def build_fader_mappings(device1_config, device2_config):
    """
    Build mappings between faders on two different MIDI devices.

    This function creates mappings to convert MIDI Control Change (CC) and Non-Registered Parameter Number (NRPN)
    messages between two devices. It maps faders from `device1` to their corresponding faders on `device2`, and vice versa.

    Args:
        device1_config (dict): Configuration dictionary for the first device, including fader types and values.
        device2_config (dict): Configuration dictionary for the second device, including fader types and values.

    Returns:
        tuple: A tuple containing six dictionaries:
            - cc_to_cc_map_device1: Maps CC messages from device 1 to corresponding CC messages on device 2.
            - cc_to_cc_map_device2: Maps CC messages from device 2 to corresponding CC messages on device 1.
            - nrpn_to_nrpn_map_device1: Maps NRPN messages from device 1 to corresponding NRPN messages on device 2.
            - nrpn_to_nrpn_map_device2: Maps NRPN messages from device 2 to corresponding NRPN messages on device 1.
            - nrpn_to_cc_map: Maps NRPN messages on one device to CC messages on the other.
            - cc_to_nrpn_map: Maps CC messages on one device to NRPN messages on the other.
    """

    # Initialize empty dictionaries to store the mappings.
    cc_to_cc_map_device1 = {}
    nrpn_to_nrpn_map_device1 = {}
    cc_to_cc_map_device2 = {}
    nrpn_to_nrpn_map_device2 = {}
    cc_to_nrpn_map = {}
    nrpn_to_cc_map = {}

    # Iterate over the faders in the configuration of device 1.
    for fader_id, fader in device1_config['faders'].items():
        target_fader = device2_config['faders'][fader_id]  # Get the corresponding fader on device 2.

        # Map NRPN to NRPN between the two devices if both faders use NRPN.
        if fader['type'] == 'NRPN' and target_fader['type'] == 'NRPN':
            nrpn_to_nrpn_map_device1[fader['value']] = (target_fader['value'], device2_config['channel'])
        # Map CC to CC between the two devices if both faders use Control Change.
        elif fader['type'] == 'control_change' and target_fader['type'] == 'control_change':
            cc_to_cc_map_device1[fader['value']] = (target_fader['value'], device2_config['channel'])
        # Map NRPN on device 1 to CC on device 2.
        elif fader['type'] == 'NRPN' and target_fader['type'] == 'control_change':
            nrpn_to_cc_map[fader['value']] = (target_fader['value'], device2_config['channel'])
        # Map CC on device 1 to NRPN on device 2.
        elif fader['type'] == 'control_change' and target_fader['type'] == 'NRPN':
            cc_to_nrpn_map[fader['value']] = (target_fader['value'], device1_config['channel'])

    # Iterate over the faders in the configuration of device 2 to complete the reverse mappings.
    for fader_id, fader in device2_config['faders'].items():
        target_fader = device1_config['faders'][fader_id]  # Get the corresponding fader on device 1.

        # Map NRPN to NRPN between the two devices if both faders use NRPN.
        if fader['type'] == 'NRPN' and target_fader['type'] == 'NRPN':
            nrpn_to_nrpn_map_device2[fader['value']] = (target_fader['value'], device1_config['channel'])
        # Map CC to CC between the two devices if both faders use Control Change.
        elif fader['type'] == 'control_change' and target_fader['type'] == 'control_change':
            cc_to_cc_map_device2[fader['value']] = (target_fader['value'], device1_config['channel'])
        # Map NRPN on device 2 to CC on device 1.
        elif fader['type'] == 'NRPN' and target_fader['type'] == 'control_change':
            nrpn_to_cc_map[fader['value']] = (target_fader['value'], device1_config['channel'])
        # Map CC on device 2 to NRPN on device 1.
        elif fader['type'] == 'control_change' and target_fader['type'] == 'NRPN':
            cc_to_nrpn_map[fader['value']] = (target_fader['value'], device2_config['channel'])

    # Return all the mappings as a tuple of dictionaries.
    return (
        cc_to_cc_map_device1, 
        cc_to_cc_map_device2, 
        nrpn_to_nrpn_map_device1, 
        nrpn_to_nrpn_map_device2, 
        nrpn_to_cc_map, 
        cc_to_nrpn_map
    )


def build_toggle_mappings(device1_config, device2_config):
    """
    Build mappings for toggle actions between fader buttons on two different MIDI devices.

    This function creates mappings that link the toggle actions (on and off) of fader buttons from
    `device1` to their corresponding fader buttons on `device2`. It ensures that the toggle actions
    are synchronized between the two devices.

    Args:
        device1_config (dict): Configuration dictionary for the first device, including fader button settings.
        device2_config (dict): Configuration dictionary for the second device, including fader button settings.

    Returns:
        dict: A dictionary (`steps_button_map`) where each key is a button ID, and the value is a dictionary with:
            - 'toggle_on': A list of dictionaries mapping toggle-on steps from device 1 to device 2.
            - 'toggle_off': A list of dictionaries mapping toggle-off steps from device 1 to device 2.
    """

    # Initialize an empty dictionary to store the mappings of toggle actions between devices.
    steps_button_map = {}

    # Iterate over the fader buttons in the configuration of device 1.
    for button_id, button in device1_config['fader_buttons'].items():
        # Check if the corresponding button exists in the configuration of device 2.
        if button_id in device2_config['fader_buttons']:
            button2 = device2_config['fader_buttons'][button_id]  # Get the corresponding button from device 2.

            # Initialize the mapping structure for the current button ID with empty lists for toggle actions.
            steps_button_map[button_id] = {
                'toggle_on': [],  # List to store mappings for toggle-on actions.
                'toggle_off': []  # List to store mappings for toggle-off actions.
            }

            # Map the toggle-on actions between the two devices.
            for i, step in enumerate(button['toggle_on']):
                if i < len(button2['toggle_on']):
                    steps_button_map[button_id]['toggle_on'].append({
                        'device1': step,               # Toggle-on action from device 1.
                        'device2': button2['toggle_on'][i]  # Corresponding toggle-on action from device 2.
                    })

            # Map the toggle-off actions between the two devices.
            for i, step in enumerate(button['toggle_off']):
                if i < len(button2['toggle_off']):
                    steps_button_map[button_id]['toggle_off'].append({
                        'device1': step,               # Toggle-off action from device 1.
                        'device2': button2['toggle_off'][i]  # Corresponding toggle-off action from device 2.
                    })

    # Return the completed mapping of toggle actions between the two devices.
    return steps_button_map




def build_toggle_mappings_single_device(device_config):
    """
    Build mappings for toggle actions within a single MIDI device.

    This function creates mappings that link the toggle actions (on and off) of fader buttons
    within a single device. It ensures that each button's toggle actions are properly mapped
    for easy access and control.

    Args:
        device_config (dict): Configuration dictionary for the device, including fader button settings.

    Returns:
        dict: A dictionary (`steps_button_map`) where each key is a button ID, and the value is a dictionary with:
            - 'toggle_on': A list of dictionaries mapping toggle-on steps for the device.
            - 'toggle_off': A list of dictionaries mapping toggle-off steps for the device.
    """

    # Initialize an empty dictionary to store the mappings of toggle actions for the device.
    steps_button_map = {}

    # Iterate over the fader buttons in the device's configuration.
    for button_id, button in device_config['fader_buttons'].items():
        # Initialize the mapping structure for the current button ID with empty lists for toggle actions.
        steps_button_map[button_id] = {
            'toggle_on': [],  # List to store mappings for toggle-on actions.
            'toggle_off': []  # List to store mappings for toggle-off actions.
        }

        # Map the toggle-on actions within the device.
        for step in button['toggle_on']:
            steps_button_map[button_id]['toggle_on'].append({
                'device': step  # Toggle-on action for the current device.
            })

        # Map the toggle-off actions within the device.
        for step in button['toggle_off']:
            steps_button_map[button_id]['toggle_off'].append({
                'device': step  # Toggle-off action for the current device.
            })

    # Return the completed mapping of toggle actions for the single device.
    return steps_button_map



def get_conversion_function(config1, config2):
    """
    Determine the appropriate conversion functions based on the fader types in two device configurations.

    This function compares the types of faders (e.g., NRPN, Control Change) in two device configurations
    and returns the corresponding functions needed to convert MIDI messages between the two devices.

    Args:
        config1 (dict): Configuration dictionary for the first device, including fader types.
        config2 (dict): Configuration dictionary for the second device, including fader types.

    Returns:
        tuple: A tuple containing two conversion functions that map faders between the two devices.
               Returns (None, None) if no appropriate conversion functions are found.
    """

    # Extract the set of fader types from both device configurations.
    config1_types = set(fader['type'] for fader in config1['faders'].values())
    config2_types = set(fader['type'] for fader in config2['faders'].values())

    # Check if both devices use NRPN faders and return the corresponding conversion functions.
    if config1_types == {'NRPN'} and config2_types == {'NRPN'}:
        return nrpn_to_nrpn, nrpn_to_nrpn
    
    # Check if both devices use Control Change (CC) faders and return the corresponding conversion functions.
    elif config1_types == {'control_change'} and config2_types == {'control_change'}:
        return cc_to_cc, cc_to_cc
    
    # Check if device 1 uses NRPN and device 2 uses Control Change, and return the corresponding conversion functions.
    elif config1_types == {'NRPN'} and config2_types == {'control_change'}:
        return nrpn_to_cc, cc_to_nrpn
    
    # Check if device 1 uses Control Change and device 2 uses NRPN, and return the corresponding conversion functions.
    elif config1_types == {'control_change'} and config2_types == {'NRPN'}:
        return cc_to_nrpn, nrpn_to_cc
    
    # If no appropriate conversion functions are found, return (None, None).
    else:
        return None, None


def convert_to_dict(s):
    """
    Convert a semicolon-separated string of key-value pairs into a dictionary.

    This function takes a string where key-value pairs are separated by semicolons,
    and each key and value is separated by a colon. It parses the string and returns
    a dictionary with the keys and values as integers.

    Args:
        s (str): A string containing key-value pairs separated by semicolons, with keys and values separated by colons.
                 Example: "1:100;2:200;3:300"

    Returns:
        dict: A dictionary where the keys and values are integers parsed from the input string.
    """

    # Split the string into individual key-value pairs based on semicolons.
    pairs = s.split(';')
    
    # Initialize an empty dictionary to store the results.
    result = {}

    # Iterate over each key-value pair.
    for pair in pairs:
        # Split the pair into key and value using the colon as a delimiter, and convert them to integers.
        key, value = pair.split(':')
        result[int(key)] = int(value)

    # Return the constructed dictionary.
    return result


def listen_to_stdin_mirror(step_map, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location):
    """
    Listen to standard input (stdin) for actions, process them, and distribute tasks to device queues.

    This function continuously reads input from stdin, expecting hex actions, which are then mapped
    to specific fader buttons and actions. It distributes these actions to the appropriate queues for
    two devices, enabling synchronized processing of tasks.

    Args:
        step_map (dict): A mapping of actions to their corresponding steps for each device.
        stdin_queue_device1 (Queue): Queue for processing actions related to device 1.
        stdin_queue_device2 (Queue): Queue for processing actions related to device 2.
        Radio_Assist_Faders_Location (dict): A mapping of cart stack numbers to fader button IDs.

    Exceptions:
        Any exceptions during the processing are caught, and the error is printed.
    """

    try:
        # Continuously read lines from standard input.
        for line in sys.stdin:
            if line.strip():  # Check if the line is not empty.
                print(f"Received from C#: {line.strip()}")
                sys.stdout.flush()

                # Strip the line and treat it as a hexadecimal action identifier.
                hex_action = line.strip()

                # Check if the action is in the gpio_to_fader_button_map.
                if hex_action in gpio_to_fader_button_map:
                    # Retrieve the corresponding cart stack and action from the map.
                    Cart_stack_triggered, action = gpio_to_fader_button_map[hex_action]
                    steps = step_map[Radio_Assist_Faders_Location[Cart_stack_triggered]]

                    # Put the associated steps for device 1 into the device 1 queue.
                    for step in steps[action]:
                        stdin_queue_device1.put((step["device1"], "device1"))
                        print("put in queue", step["device1"])

                    # Put the associated steps for device 2 into the device 2 queue.
                    for step in steps[action]:
                        stdin_queue_device2.put((step["device2"], "device2"))
                        print("put in queue", step["device2"])
                else:
                    # Handle unknown or malformed actions.
                    print(f"Unknown or malformed action received: {line.strip()}")
            else:
                # Handle empty lines.
                print("Received an empty line")
                sys.stdout.flush()
    except Exception as e:
        # Catch and print any exceptions that occur during processing.
        print(f"Exception: {e}")
        sys.stdout.flush()

        
def listen_to_stdin_single(single_steps, stdin_queue_device, Radio_Assist_Faders_Location):
    """
    Listen to standard input (stdin) for actions, process them, and distribute tasks to a single device queue.

    This function continuously reads input from stdin, expecting hex actions, which are then mapped
    to specific fader buttons and actions. It distributes these actions to the appropriate queue for
    a single device, enabling synchronized processing of tasks.

    Args:
        single_steps (dict): A mapping of actions to their corresponding steps for the device.
        stdin_queue_device (Queue): Queue for processing actions related to the device.
        Radio_Assist_Faders_Location (dict): A mapping of cart stack numbers to fader button IDs.

    Exceptions:
        Any exceptions during the processing are caught, and the error is printed.
    """

    try:
        # Continuously read lines from standard input.
        for line in sys.stdin:
            if line.strip():  # Check if the line is not empty.
                print(f"Received from C#: {line.strip()}")
                sys.stdout.flush()

                # Strip the line and treat it as a hexadecimal action identifier.
                hex_action = line.strip()

                # Check if the action is in the gpio_to_fader_button_map.
                if hex_action in gpio_to_fader_button_map:
                    # Retrieve the corresponding cart stack and action from the map.
                    Cart_stack_triggered, action = gpio_to_fader_button_map[hex_action]
                    steps = single_steps[Radio_Assist_Faders_Location[Cart_stack_triggered]]

                    # Put the associated steps for the device into the device queue.
                    for step in steps[action]:
                        stdin_queue_device.put((step["device"], "device"))
                        print("put in queue", step["device"])
                else:
                    # Handle unknown or malformed actions.
                    print(f"Unknown or malformed action received: {line.strip()}")
            else:
                # Handle empty lines.
                print("Received an empty line")
                sys.stdout.flush()
    except Exception as e:
        # Catch and print any exceptions that occur during processing.
        print(f"Exception: {e}")
        sys.stdout.flush()


def main():
    """
    Main function to initialize and run the MIDI control application.

    This function parses command-line arguments, loads device configurations, sets up MIDI input/output,
    and starts threads to handle MIDI message processing, including mirroring between devices, handling
    DHD (Digital Hybrid Device) integration, and controlling on-air lights.

    It manages different scenarios based on the provided devices and configurations and ensures
    proper synchronization between devices.
    """

    # Ensure the correct number of command-line arguments are provided.
    if len(sys.argv) != 8:
        sys.exit(1)

    # Parse command-line arguments.
    device1 = sys.argv[1]
    device2 = sys.argv[2]
    dhd_enabled = sys.argv[3] == 'True'
    dhd_device = sys.argv[4]
    GPIO_fader_position = sys.argv[5]
    On_air_lights_enabled = sys.argv[6]
    COM_port = sys.argv[7]    

    # Initialize necessary variables and queues.
    Radio_Assist_Faders_Location = {}
    step_map = {}
    
    stdin_queue_device1 = Queue()
    stdin_queue_device2 = Queue()
    stdin_queue_single  = Queue()
    
    # Set up the serial port for controlling on-air lights if enabled.
    if On_air_lights_enabled == "True":
        try:
            ser = serial.Serial(COM_port, 9600, timeout=1)
            print(f"Serial port {COM_port} opened.")
        except SerialException as e:
            raise Exception(f"Error: Cannot find port: {e}")
    else:
        ser = ""

    # Load and configure DHD device if specified.
    if dhd_device != "None":
        dhd_config = read_xml_config(f"{dhd_device}.xml")
        dhd_config = parse_config(dhd_config)
        
        # Retrieve available MIDI input and output devices.
        available_inputs = mido.get_input_names()
        available_outputs = mido.get_output_names()

        # Check if the configured MIDI input device is available.
        if dhd_config['midi_in_name'] not in available_inputs:
            print(f"Error: Input device '{dhd_config['midi_in_name']}' for device1 not found.")
            raise Exception(f"Error: {dhd_config['midi_in_name']} device not found. Available Inputs are: {available_inputs}. Please check configuration file.")
            sys.exit(1)

        # Check if the configured MIDI output device is available.
        if dhd_config['midi_out_name'] not in available_outputs:
            print(f"Error: Output device '{dhd_config['midi_out_name']}' for device1 not found.")
            raise Exception(f"Error: {dhd_config['midi_out_name']} device not found. Available Outputs are: {available_outputs}. Please check configuration file.")  
            sys.exit(1)
            
        # Convert GPIO fader positions to a dictionary and build toggle mappings for DHD.
        Radio_Assist_Faders_Location = convert_to_dict(GPIO_fader_position)
        single_mappings = build_toggle_mappings_single_device(dhd_config)
        
        # Start a thread to listen for stdin actions and process them for the DHD device.
        stdin_thread = threading.Thread(target=listen_to_stdin_single, args=(single_mappings, stdin_queue_single, Radio_Assist_Faders_Location))
        stdin_thread.start()
        print("DHD is enabled. Listening for updates...")
        
        # Start the radio assist MIDI processing thread for the DHD device.
        threading.Thread(target=radio_assist_midi, args=(
            "device", dhd_config['midi_in_name'], dhd_config['midi_out_name'], single_mappings, dhd_enabled, stdin_queue_single, Radio_Assist_Faders_Location, On_air_lights_enabled, ser)).start()

    # If both devices are specified, configure and start MIDI mirroring between them.
    if device1 != "None" and device2 != "None":
        # Load and parse the device configurations.
        device1_config = read_xml_config(f"{device1}.xml")
        device2_config = read_xml_config(f"{device2}.xml")
        device1_config = parse_config(device1_config)
        device2_config = parse_config(device2_config)     
        
        # Retrieve available MIDI input and output devices.
        available_inputs = mido.get_input_names()
        available_outputs = mido.get_output_names()

        # Check if the configured MIDI input and output devices for device1 are available.
        if device1_config['midi_in_name'] not in available_inputs:
            print(f"Error: Input device '{device1_config['midi_in_name']}' for device1 not found.")
            raise Exception(f"Error: {device1_config['midi_in_name']} device not found. Available Inputs are: {available_inputs}. Please check configuration file.")
            sys.exit(1)
        if device1_config['midi_out_name'] not in available_outputs:
            print(f"Error: Output device '{device1_config['midi_out_name']}' for device1 not found.")
            raise Exception(f"Error: {device1_config['midi_out_name']} device not found. Available Outputs are: {available_outputs}. Please check configuration file.")  
            sys.exit(1)

        # Check if the configured MIDI input and output devices for device2 are available.
        if device2_config['midi_in_name'] not in available_inputs:
            print(f"Error: Input device '{device2_config['midi_in_name']}' for device2 not found.")
            raise Exception(f"Error: {device2_config['midi_in_name']} device not found. Available Inputs are: {available_inputs}. Please check configuration file.")
            sys.exit(1)
        if device2_config['midi_out_name'] not in available_outputs:
            print(f"Error: Output device '{device2_config['midi_out_name']}' for device2 not found.")
            raise Exception(f"Error: {device2_config['midi_out_name']} device not found. Available Outputs are: {available_outputs}. Please check configuration file.")        
            sys.exit(1)

        # Convert GPIO fader positions to a dictionary if DHD is enabled.
        if dhd_enabled:
            Radio_Assist_Faders_Location = convert_to_dict(GPIO_fader_position)

        # Build mappings for CC and NRPN conversions between the devices.
        cc_to_cc_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device1, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map = build_fader_mappings(device1_config, device2_config)
        step_map = build_toggle_mappings(device1_config, device2_config)
        convert_func1, convert_func2 = get_conversion_function(device1_config, device2_config)
        
        # Start threads to mirror MIDI between device1 and device2.
        threading.Thread(target=mirror_midi, args=(
            "device1", device1_config['midi_in_name'], device2_config['midi_out_name'], 
            {device1_config['channel']: device2_config['channel']}, cc_to_cc_map_device1, nrpn_to_nrpn_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map, step_map, dhd_enabled, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location, convert_func1, On_air_lights_enabled, ser)).start()

        threading.Thread(target=mirror_midi, args=(
            "device2", device2_config['midi_in_name'], device1_config['midi_out_name'], 
            {device2_config['channel']: device1_config['channel']}, cc_to_cc_map_device1, nrpn_to_nrpn_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map, step_map, dhd_enabled, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location, convert_func2, On_air_lights_enabled, ser)).start()
        
        # If DHD is enabled, start listening for updates using the mirror stdin function.
        if dhd_enabled:
            Radio_Assist_Faders_Location = convert_to_dict(GPIO_fader_position)
            stdin_thread = threading.Thread(target=listen_to_stdin_mirror, args=(step_map, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location))
            stdin_thread.start()
            print("DHD is enabled. Listening for updates...")

# Run the main function when the script is executed.
if __name__ == "__main__":
    main()
