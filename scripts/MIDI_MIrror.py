import sys
import threading
import queue
import xml.etree.ElementTree as ET
import os
import mido
import time
from collections import deque

def cc_to_nrpn(cc_number, data_value, input_channel, channel_map, cc_to_nrpn_map):
    print("cc_number",cc_number)
    print("cc_to_nrpn_map",cc_to_nrpn_map)
    # Validate data_value is within the MIDI range of 0-127
    if not (0 <= data_value <= 127):
        raise ValueError("data_value must be between 0 and 127")
        
    if cc_number in cc_to_nrpn_map:
        nrpn_number, nrpn_output_channel = cc_to_nrpn_map[cc_number]
        output_channel = channel_map.get(input_channel, nrpn_output_channel)

        # Compute NRPN number parts
        msb = (nrpn_number >> 7) & 0x7F
        lsb = nrpn_number & 0x7F

        print(f"Converting CC {cc_number} (value {data_value}) on channel {input_channel} to NRPN {nrpn_number} on channel {output_channel}")
        print(f"NRPN MSB: {msb}, NRPN LSB: {lsb}")

        # Create and return a list of MIDI messages to form the complete NRPN message
        return [
            mido.Message('control_change', control=99, value=msb, channel=output_channel),
            mido.Message('control_change', control=98, value=lsb, channel=output_channel),
            mido.Message('control_change', control=6, value=data_value, channel=output_channel),
            mido.Message('control_change', control=38, value=0, channel=output_channel)  # Setting LSB to 0
        ]
    else:
        print(f"No mapping found for CC {cc_number}")
    return None


def nrpn_to_cc(nrpn_number, data_value, input_channel, channel_map, nrpn_to_cc_map, threshold=20, min_interval=0.5, max_interval=0.7):
    print(f"nrpn_to_cc called with NRPN {nrpn_number}, Data Value {data_value}, Input Channel {input_channel}")
    if nrpn_number in nrpn_to_cc_map:
        cc_number, default_output_channel = nrpn_to_cc_map[nrpn_number]
        output_channel = channel_map.get(input_channel, default_output_channel)

        if not hasattr(nrpn_to_cc, 'last_values'):
            nrpn_to_cc.last_values = {}
        if not hasattr(nrpn_to_cc, 'last_times'):
            nrpn_to_cc.last_times = {}
        
        key = (output_channel, cc_number)
        current_time = time.time()

        # Initialize last value and time if not present
        if key not in nrpn_to_cc.last_values:
            nrpn_to_cc.last_values[key] = data_value
            nrpn_to_cc.last_times[key] = current_time
            return None  # Skip sending the first time to initialize

        last_value = nrpn_to_cc.last_values[key]
        last_time = nrpn_to_cc.last_times[key]

        value_change = abs(data_value - last_value)
        time_elapsed = current_time - last_time

        # Check if the message should be sent
        if (value_change >= threshold or time_elapsed >= max_interval):
            nrpn_to_cc.last_values[key] = data_value
            nrpn_to_cc.last_times[key] = current_time
            scaled_data_value = data_value >> 7  # Correct scaling
            print(f"Converting NRPN {nrpn_number} (value {data_value}) on channel {input_channel} to CC {cc_number} on channel {output_channel}")
            return mido.Message('control_change', control=cc_number, value=scaled_data_value, channel=output_channel)
        elif time_elapsed < min_interval:
            return None  # Do not send yet
    else:
        print(f"No mapping found for NRPN {nrpn_number}")

    return None


def is_nrpn_control(control):
    return control in [98, 99, 6, 38]

def process_nrpn_messages(nrpn_cache, message):
    if message.control == 99:  # NRPN MSB
        nrpn_cache['msb'] = message.value
    elif message.control == 98:  # NRPN LSB
        nrpn_cache['lsb'] = message.value
    elif message.control == 6:  # NRPN Data Entry MSB
        nrpn_cache['data_msb'] = message.value
    elif message.control == 38:  # NRPN Data Entry LSB
        nrpn_cache['data_lsb'] = message.value

    if 'msb' in nrpn_cache and 'lsb' in nrpn_cache and 'data_msb' in nrpn_cache and 'data_lsb' in nrpn_cache:
        nrpn_number = (nrpn_cache['msb'] << 7) + nrpn_cache['lsb']
        data_value = (nrpn_cache.get('data_msb', 0) << 7) + nrpn_cache.get('data_lsb', 0)
        nrpn_cache.clear()
        return nrpn_number, data_value
    return None

def mirror_midi(input_device_name, output_device_name, channel_map, cc_to_nrpn_map, nrpn_to_cc_map, delay=0.001):
    message_queue = deque()
    last_send_time = time.time()
    nrpn_cache = {}

    def send_messages():
        nonlocal last_send_time
        while message_queue:
            msg = message_queue.popleft()
            print(f"Sending message: {msg}")
            outport.send(msg)
        last_send_time = time.time()

    with mido.open_input(input_device_name) as inport, mido.open_output(output_device_name) as outport:
        print(f"Mirroring MIDI from {input_device_name} to {output_device_name}...")
        for message in inport:
            now = time.time()
            if now - last_send_time > delay:
                send_messages()

            print(f"Received message: {message}")
            if message.type == 'control_change':
                if is_nrpn_control(message.control):
                    result = process_nrpn_messages(nrpn_cache, message)
                    if result:
                        nrpn_number, data_value = result
                        print(f"Processing NRPN message: NRPN {nrpn_number}, Data Value {data_value}")
                        transformed_message = nrpn_to_cc(nrpn_number, data_value, message.channel, channel_map, nrpn_to_cc_map)
                        if transformed_message:
                            print(f"Transformed NRPN to CC: {transformed_message}")
                            message_queue.append(transformed_message)
                    continue
                print("message control", message.control, "message value", message.value)
                transformed_message = cc_to_nrpn(message.control, message.value, message.channel, channel_map, cc_to_nrpn_map)
                if transformed_message:
                    for msg in transformed_message:
                        print(f"Transformed CC to NRPN message: {msg}")
                        message_queue.append(msg)
            else:
                message_queue.append(message)

    send_messages()  # Ensure any remaining messages are sent


def read_xml_config(file_name):
    configs_path = os.path.join(os.path.dirname(__file__), '..', 'configs', file_name)
    full_path = os.path.normpath(configs_path)
    
    try:
        tree = ET.parse(full_path)
        root = tree.getroot()
        print(f"Read XML config from {full_path}")
        return root
    except ET.ParseError as e:
        print(f"Error parsing XML file {full_path}: {e}")
    except FileNotFoundError:
        print(f"XML file not found: {full_path}")
    return None

def parse_config(xml_root):
    config = {
        'midi_in_name': xml_root.find('./midi/midi_in_name').text,
        'midi_out_name': xml_root.find('./midi/midi_out_name').text,
        'channel': int(xml_root.find('./midi/channel').text),
        'faders': {},
        'fader_buttons': {}
    }
    
    for fader in xml_root.findall('./faders/fader'):
        fader_id = int(fader.get('id'))
        fader_config = {
            'type': fader.get('type'),
            'value': int(fader.get('value')),
        }
        config['faders'][fader_id] = fader_config
        print(f"Fader {fader_id}: {fader_config}")

    for button in xml_root.findall('./fader_buttons/fader_button'):
        button_id = int(button.get('id'))
        button_config = {
            'type': button.get('type'),
            'value': int(button.get('value')),
        }
        config['fader_buttons'][button_id] = button_config
        print(f"Button {button_id}: {button_config}")

    return config

def build_mappings(device1_config, device2_config):
    cc_to_nrpn_map = {}
    nrpn_to_cc_map = {}

    # Map faders from device 1 to device 2
    for fader_id, fader in device1_config['faders'].items():
        if fader['type'] == 'NRPN':
            if fader_id in device2_config['faders'] and device2_config['faders'][fader_id]['type'] == 'control_change':
                nrpn_to_cc_map[fader['value']] = (device2_config['faders'][fader_id]['value'], device2_config['channel'])
                print(f"Mapping NRPN {fader['value']} to CC {device2_config['faders'][fader_id]['value']} for device 1")

    # Map faders from device 2 to device 1
    for fader_id, fader in device2_config['faders'].items():
        if fader['type'] == 'control_change':
            if fader_id in device1_config['faders'] and device1_config['faders'][fader_id]['type'] == 'NRPN':
                cc_to_nrpn_map[fader['value']] = (device1_config['faders'][fader_id]['value'], device1_config['channel'])
                print(f"Mapping CC {fader['value']} to NRPN {device1_config['faders'][fader_id]['value']} for device 2")

    return nrpn_to_cc_map,cc_to_nrpn_map



def get_conversion_function(config1, config2):
    # Check if both are NRPN
    if all(fader['type'] == 'NRPN' for fader in config1['faders'].values()) and \
       all(fader['type'] == 'NRPN' for fader in config2['faders'].values()):
        return nrpn_to_cc, nrpn_to_cc
    # Check if both are non-NRPN
    elif all(fader['type'] == 'control_change' for fader in config1['faders'].values()) and \
         all(fader['type'] == 'control_change' for fader in config2['faders'].values()):
        return cc_to_nrpn, cc_to_nrpn
    # Mixed NRPN and non-NRPN
    else:
        return cc_to_nrpn, nrpn_to_cc

def main():
    if len(sys.argv) != 5:
        print("Usage: MIDI_mirror.py <device1> <device2> <dhd_enabled> <dhd_device>")
        sys.exit(1)

    device1 = sys.argv[1]
    device2 = sys.argv[2]
    dhd_enabled = sys.argv[3] == 'True'
    dhd_device = sys.argv[4]

    device1_config = read_xml_config(f"{device1}.xml")
    device2_config = read_xml_config(f"{device2}.xml")

    if device1_config is None or device2_config is None:
        print("Error: Unable to read configuration files.")
        sys.exit(1)

    device1_config = parse_config(device1_config)
    device2_config = parse_config(device2_config)

    # Check if MIDI devices are available
    available_inputs = mido.get_input_names()
    available_outputs = mido.get_output_names()

    if device1_config['midi_in_name'] not in available_inputs:
        print(f"Error: Input device '{device1_config['midi_in_name']}' for device1 not found.")
        sys.exit(1)
    if device1_config['midi_out_name'] not in available_outputs:
        print(f"Error: Output device '{device1_config['midi_out_name']}' for device1 not found.")
        sys.exit(1)
    if device2_config['midi_in_name'] not in available_inputs:
        print(f"Error: Input device '{device2_config['midi_in_name']}' for device2 not found.")
        sys.exit(1)
    if device2_config['midi_out_name'] not in available_outputs:
        print(f"Error: Output device '{device2_config['midi_out_name']}' for device2 not found.")
        sys.exit(1)

    cc_to_nrpn_map, nrpn_to_cc_map = build_mappings(device1_config, device2_config)

    convert_func1, convert_func2 = get_conversion_function(device1_config, device2_config)

    if dhd_enabled:
        input_queue = queue.Queue()
        stdin_listener_thread = threading.Thread(target=listen_to_stdin, args=(input_queue,))
        stdin_listener_thread.daemon = True
        stdin_listener_thread.start()

        print("DHD is enabled. Listening for updates...")

        try:
            while True:
                if not input_queue.empty():
                    data = input_queue.get()
                    print(f"Received update: {data}")
                pass
        except KeyboardInterrupt:
            print("Exiting...")

    else:
        print("DHD is not enabled. Proceeding without listening for updates.")

    threading.Thread(target=mirror_midi, args=(
        device1_config['midi_in_name'], device2_config['midi_out_name'], 
        {device1_config['channel']: device2_config['channel']}, nrpn_to_cc_map, cc_to_nrpn_map)).start()
    
    threading.Thread(target=mirror_midi, args=(
        device2_config['midi_in_name'], device1_config['midi_out_name'], 
        {device2_config['channel']: device1_config['channel']}, nrpn_to_cc_map, cc_to_nrpn_map)).start()
        
if __name__ == "__main__":
    main()
