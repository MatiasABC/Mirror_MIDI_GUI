import sys
import threading
import xml.etree.ElementTree as ET
import os
import mido
import time
from collections import deque


def cc_to_nrpn(cc_number, data_value, input_channel, channel_map, cc_to_nrpn_map):
    if not (0 <= data_value <= 127):
        raise ValueError("data_value must be between 0 and 127")
        
    if cc_number in cc_to_nrpn_map:
        nrpn_number, nrpn_output_channel = cc_to_nrpn_map[cc_number]
        output_channel = channel_map.get(input_channel, nrpn_output_channel)
        msb = (nrpn_number >> 7) & 0x7F
        lsb = nrpn_number & 0x7F

        return [
            mido.Message('control_change', control=99, value=msb, channel=output_channel),
            mido.Message('control_change', control=98, value=lsb, channel=output_channel),
            mido.Message('control_change', control=6, value=data_value, channel=output_channel),
            mido.Message('control_change', control=38, value=0, channel=output_channel)
        ]
    else:
        print(f"No mapping found for CC {cc_number}")
    return None


def nrpn_to_cc(nrpn_number, data_value, input_channel, channel_map, nrpn_to_cc_map, threshold=20, min_interval=0.5, max_interval=0.7):
    if nrpn_number in nrpn_to_cc_map:
        cc_number, default_output_channel = nrpn_to_cc_map[nrpn_number]
        output_channel = channel_map.get(input_channel, default_output_channel)

        if not hasattr(nrpn_to_cc, 'last_values'):
            nrpn_to_cc.last_values = {}
        if not hasattr(nrpn_to_cc, 'last_times'):
            nrpn_to_cc.last_times = {}
        
        key = (output_channel, cc_number)
        current_time = time.time()

        if key not in nrpn_to_cc.last_values:
            nrpn_to_cc.last_values[key] = data_value
            nrpn_to_cc.last_times[key] = current_time
            return None

        last_value = nrpn_to_cc.last_values[key]
        last_time = nrpn_to_cc.last_times[key]

        value_change = abs(data_value - last_value)
        time_elapsed = current_time - last_time

        if (value_change >= threshold or time_elapsed >= max_interval):
            nrpn_to_cc.last_values[key] = data_value
            nrpn_to_cc.last_times[key] = current_time
            scaled_data_value = data_value >> 7
            return mido.Message('control_change', control=cc_number, value=scaled_data_value, channel=output_channel)
        elif time_elapsed < min_interval:
            return None
    else:
        print(f"No mapping found for NRPN {nrpn_number}")

    return None


def is_nrpn_control(control):
    return control in [98, 99, 6, 38]


def process_nrpn_messages(nrpn_cache, message):
    if message.control == 99:
        nrpn_cache['msb'] = message.value
    elif message.control == 98:
        nrpn_cache['lsb'] = message.value
    elif message.control == 6:
        nrpn_cache['data_msb'] = message.value
    elif message.control == 38:
        nrpn_cache['data_lsb'] = message.value

    if 'msb' in nrpn_cache and 'lsb' in nrpn_cache and 'data_msb' in nrpn_cache and 'data_lsb' in nrpn_cache:
        nrpn_number = (nrpn_cache['msb'] << 7) + nrpn_cache['lsb']
        data_value = (nrpn_cache.get('data_msb', 0) << 7) + nrpn_cache.get('data_lsb', 0)
        nrpn_cache.clear()
        return nrpn_number, data_value
    return None


def mirror_midi(input_device_name, output_device_name, channel_map, cc_to_nrpn_map, nrpn_to_cc_map, button_map, step_map,DHD_enabled, delay=0.001):
    message_queue = deque()
    last_send_time = time.time()
    nrpn_cache = {}

    def send_messages():
        nonlocal last_send_time
        while message_queue:
            msg = message_queue.popleft()
            #print(f"Sending mirrored message: {msg}")  # Print statement for sending mirrored message
            outport.send(msg)
        last_send_time = time.time()

    with mido.open_input(input_device_name) as inport, mido.open_output(output_device_name) as outport:
        print(f"Mirroring MIDI from {input_device_name} to {output_device_name}...")
        for message in inport:            
            now = time.time()
            if now - last_send_time > delay:
                send_messages()
            #### FADER LOGIC    
            if message.type == 'control_change':
                if is_nrpn_control(message.control):
                    result = process_nrpn_messages(nrpn_cache, message)
                    if result:
                        nrpn_number, data_value = result
                        transformed_message = nrpn_to_cc(nrpn_number, data_value, message.channel, channel_map, nrpn_to_cc_map)
                        if transformed_message: #if this hits the conversion is nrpn_to_cc
                            message_queue.append(transformed_message)
                        else:
                            #transformed_message = nrpn_to_nrpn(nrpn_number, data_value, message.channel, channel_map, nrpn_to_nrpn_map)
                            #if transformed_message:
                            #    message_queue.append(transformed_message)
                            pass                           
                    continue
                transformed_message = cc_to_nrpn(message.control, message.value, message.channel, channel_map, cc_to_nrpn_map)
                if transformed_message:
                    for msg in transformed_message:
                        message_queue.append(msg)
                    continue
                else:
                    #transformed_message = cc_to_cc(message.control, message.value, message.channel, channel_map, cc_to_cc_map)
                    #if transformed_message:
                    #   for msg in transformed_message:
                    #       message_queue.append(msg)
                    #   continue
                    pass

            ### FADER BUTTONS LOGIC
            if not DHD_enabled:
                if message.type in ['note_on', 'note_off']:       
                    all_notes = {note for pair in button_map.keys() | button_map.values() for note in pair}            
                    if message.note in all_notes:
                    # Find the corresponding button ID
                        button_id = None
                        for key, value in button_map.items():
                            if message.note in key or message.note in value:
                                button_id = key[0]
                                break
                    if button_id is not None:
                        print(f"Button ID: {button_id}")
                        steps = step_map[button_id]
                        print(steps)



    send_messages()




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

    for button in xml_root.findall('./fader_buttons/fader_button'):
        button_id = int(button.get('id'))
        button_type = button.get('type')
        button_value = int(button.get('value'))

        button_config = {
            'type': button_type,
            'value': button_value,
            'toggle_on': [],
            'toggle_off': []
        }

        toggle_on = button.find('toggle_on')
        if toggle_on is not None:
            button_config['toggle_on'] = [msg.strip() for msg in toggle_on.text.strip().split(';')]

        toggle_off = button.find('toggle_off')
        if toggle_off is not None:
            button_config['toggle_off'] = [msg.strip() for msg in toggle_off.text.strip().split(';')]

        config['fader_buttons'][button_id] = button_config

    return config


def build_mappings(device1_config, device2_config):
    cc_to_nrpn_map = {}
    nrpn_to_cc_map = {}

    for fader_id, fader in device1_config['faders'].items():
        if fader['type'] == 'NRPN':
            if fader_id in device2_config['faders'] and device2_config['faders'][fader_id]['type'] == 'control_change':
                nrpn_to_cc_map[fader['value']] = (device2_config['faders'][fader_id]['value'], device2_config['channel'])

    for fader_id, fader in device2_config['faders'].items():
        if fader['type'] == 'control_change':
            if fader_id in device1_config['faders'] and device1_config['faders'][fader_id]['type'] == 'NRPN':
                cc_to_nrpn_map[fader['value']] = (device1_config['faders'][fader_id]['value'], device1_config['channel'])

    return nrpn_to_cc_map, cc_to_nrpn_map


def build_toggle_mappings(device1_config, device2_config):
    fader_button_map = {}
    steps_button_map = {}

    for button_id, button in device1_config['fader_buttons'].items():
        if button_id in device2_config['fader_buttons']:
            button2 = device2_config['fader_buttons'][button_id]
            fader_button_map[(button_id, button['value'])] = (button_id, button2['value'])

            steps_button_map[button_id] = {
                'toggle_on': [],
                'toggle_off': []
            }

            for i, step in enumerate(button['toggle_on']):
                if i < len(button2['toggle_on']):
                    steps_button_map[button_id]['toggle_on'].append({
                        'device1': step,
                        'device2': button2['toggle_on'][i]
                    })

            for i, step in enumerate(button['toggle_off']):
                if i < len(button2['toggle_off']):
                    steps_button_map[button_id]['toggle_off'].append({
                        'device1': step,
                        'device2': button2['toggle_off'][i]
                    })

    return fader_button_map, steps_button_map



def get_conversion_function(config1, config2):
    if all(fader['type'] == 'NRPN' for fader in config1['faders'].values()) and \
       all(fader['type'] == 'NRPN' for fader in config2['faders'].values()):
        return nrpn_to_cc, nrpn_to_cc
    elif all(fader['type'] == 'control_change' for fader in config1['faders'].values()) and \
         all(fader['type'] == 'control_change' for fader in config2['faders'].values()):
        return cc_to_nrpn, cc_to_nrpn
    else:
        return cc_to_nrpn, nrpn_to_cc


def listen_to_stdin():
    print("Ready to receive data from C#...")
    sys.stdout.flush()

    try:
        sys.stdout.flush()
        for line in sys.stdin:
            if line.strip():
                print(f"Received from C#: {line.strip()}")
                sys.stdout.flush()
            else:
                print("Received an empty line")
                sys.stdout.flush()
    except Exception as e:
        print(f"Exception: {e}")
        sys.stdout.flush()


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
    button_map, step_map = build_toggle_mappings(device1_config, device2_config)

    convert_func1, convert_func2 = get_conversion_function(device1_config, device2_config)

    if dhd_enabled:       
        stdin_thread = threading.Thread(target=listen_to_stdin)
        stdin_thread.start()

        print("DHD is enabled. Listening for updates...")        
        
    else:        
        print("DHD is not enabled. Proceeding without listening for updates.")

    threading.Thread(target=mirror_midi, args=(
        device1_config['midi_in_name'], device2_config['midi_out_name'], 
        {device1_config['channel']: device2_config['channel']}, nrpn_to_cc_map, cc_to_nrpn_map, button_map, step_map,dhd_enabled)).start()
    
    threading.Thread(target=mirror_midi, args=(
        device2_config['midi_in_name'], device1_config['midi_out_name'], 
        {device2_config['channel']: device1_config['channel']}, nrpn_to_cc_map, cc_to_nrpn_map, button_map, step_map, dhd_enabled)).start()
        
if __name__ == "__main__":
    main()
