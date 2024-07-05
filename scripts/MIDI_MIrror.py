import sys
import threading
import xml.etree.ElementTree as ET
import os
import mido
import time
from collections import deque
from queue import Queue
from pynput.keyboard import Key, Controller

# Define the mapping of GPIO hex values to fader button IDs and actions
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

keyboard = Controller()

def trigger_key_press_id(id):
    Toggle_Key_presses = [
        [Key.ctrl, Key.alt, Key.f1],
        [Key.ctrl, Key.alt, Key.f2],
        [Key.ctrl, Key.alt, Key.f3],
        [Key.ctrl, Key.alt, Key.f4]
    ]
    keyboard = Controller()
    if 0 <= id < len(Toggle_Key_presses):
        key_combination = Toggle_Key_presses[id-1]
        
        print(f"Triggering key press combination for ID {id}: {key_combination}")

        for key in key_combination:
            print(f"Pressing {key}")
            keyboard.press(key)
        
        for key in key_combination:            
            keyboard.release(key)
    else:
        print("Invalid ID. Please provide a valid ID between 0 and", len(Toggle_Key_presses) - 1)

def nrpn_to_nrpn(nrpn_number, data_value, input_channel, channel_map, nrpn_to_nrpn_map, threshold=20, min_interval=0.5, max_interval=0.7):
    if nrpn_number in nrpn_to_nrpn_map:
        target_nrpn_number, default_output_channel = nrpn_to_nrpn_map[nrpn_number]
        output_channel = channel_map.get(input_channel, default_output_channel)

        if not hasattr(nrpn_to_nrpn, 'last_values'):
            nrpn_to_nrpn.last_values = {}
        if not hasattr(nrpn_to_nrpn, 'last_times'):
            nrpn_to_nrpn.last_times = {}

        key = (output_channel, target_nrpn_number)
        current_time = time.time()

        if key not in nrpn_to_nrpn.last_values:
            nrpn_to_nrpn.last_values[key] = data_value
            nrpn_to_nrpn.last_times[key] = current_time
            return None

        last_value = nrpn_to_nrpn.last_values[key]
        last_time = nrpn_to_nrpn.last_times[key]

        value_change = abs(data_value - last_value)
        time_elapsed = current_time - last_time

        if (value_change >= threshold or time_elapsed >= max_interval):
            nrpn_to_nrpn.last_values[key] = data_value
            nrpn_to_nrpn.last_times[key] = current_time

            msb = (data_value >> 7) & 0x7F
            lsb = data_value & 0x7F

            return [
                mido.Message('control_change', control=99, value=(target_nrpn_number >> 7) & 0x7F, channel=output_channel),
                mido.Message('control_change', control=98, value=target_nrpn_number & 0x7F, channel=output_channel),
                mido.Message('control_change', control=6, value=msb, channel=output_channel),
                mido.Message('control_change', control=38, value=lsb, channel=output_channel)
            ]
        elif time_elapsed < min_interval:
            return None
    return None

def cc_to_cc(cc_number, data_value, input_channel, channel_map, cc_to_cc_map, threshold=20, min_interval=0.5, max_interval=0.7):
    if cc_number in cc_to_cc_map:
        target_cc_number, default_output_channel = cc_to_cc_map[cc_number]
        output_channel = channel_map.get(input_channel, default_output_channel)

        if not hasattr(cc_to_cc, 'last_values'):
            cc_to_cc.last_values = {}
        if not hasattr(cc_to_cc, 'last_times'):
            cc_to_cc.last_times = {}

        key = (output_channel, target_cc_number)
        current_time = time.time()

        if key not in cc_to_cc.last_values:
            cc_to_cc.last_values[key] = data_value
            cc_to_cc.last_times[key] = current_time
            return None

        last_value = cc_to_cc.last_values[key]
        last_time = cc_to_cc.last_times[key]

        value_change = abs(data_value - last_value)
        time_elapsed = current_time - last_time

        if (value_change >= threshold or time_elapsed >= max_interval):
            cc_to_cc.last_values[key] = data_value
            cc_to_cc.last_times[key] = current_time

            scaled_data_value = data_value & 0x7F
            return mido.Message('control_change', control=target_cc_number, value=scaled_data_value, channel=output_channel)
        elif time_elapsed < min_interval:
            return None
    return None

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
        pass
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

def mirror_midi(device, input_device_name, output_device_name, channel_map, cc_to_cc_map_device1, nrpn_to_nrpn_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map, step_map, DHD_enabled, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location, convert_func, dhd_device, delay=0.0001):
    message_queue = deque()
    last_send_time = time.time()
    nrpn_cache = {}
    message_buffer = deque(maxlen=10)

    def handle_special_message(button_id):
        for Cart_Stack_number, allocated_button in Radio_Assist_Faders_Location.items():
            if allocated_button == button_id:
                print(f"Special message detected for button {button_id}")
                return Cart_Stack_number
        return None

    def send_messages():
        nonlocal last_send_time
        while message_queue:
            msg = message_queue.popleft()
            outport.send(msg)
        last_send_time = time.time()

    def process_stdin_messages_device1():
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

    with mido.open_input(input_device_name) as inport, mido.open_output(output_device_name) as outport:
        print(f"Mirroring MIDI from {input_device_name} to {output_device_name}...")
        opposite_device = "device1" if device == "device2" else "device2"
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

            messages = list(inport.iter_pending())
            if messages:
                for message in messages:
                    #print(f"Received MIDI message: {message}")
                    message_buffer.append(message)

                    converted_message = None
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
                    if converted_message:
                        if isinstance(converted_message, list):
                            message_queue.extend(converted_message)
                        else:
                            message_queue.append(converted_message)
                        continue

                    if converted_message is None and not nrpn_cache:
                        for button_id, actions in step_map.items():
                            for action, steps in actions.items():
                                for step in steps:
                                    if " AND " in step[device]:
                                        steps_list = step[device].split(" AND ")
                                        if all(any(str(msg) == s for msg in message_buffer) for s in steps_list):
                                            print(f"Complete sequence matches for button {button_id}, action {action}")
                                            special_message_result = handle_special_message(button_id)
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

                send_messages()

            time.sleep(0.001)

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

def build_fader_mappings(device1_config, device2_config):
    cc_to_cc_map_device1 = {}
    nrpn_to_nrpn_map_device1 = {}
    cc_to_cc_map_device2 = {}
    nrpn_to_nrpn_map_device2 = {}
    cc_to_nrpn_map = {}
    nrpn_to_cc_map = {}

    for fader_id, fader in device1_config['faders'].items():
        target_fader = device2_config['faders'][fader_id]

        if fader['type'] == 'NRPN' and target_fader['type'] == 'NRPN':
            nrpn_to_nrpn_map_device1[fader['value']] = (target_fader['value'], device2_config['channel'])
        elif fader['type'] == 'control_change' and target_fader['type'] == 'control_change':
            cc_to_cc_map_device1[fader['value']] = (target_fader['value'], device2_config['channel'])
        elif fader['type'] == 'NRPN' and target_fader['type'] == 'control_change':
            nrpn_to_cc_map[fader['value']] = (target_fader['value'], device2_config['channel'])
        elif fader['type'] == 'control_change' and target_fader['type'] == 'NRPN':
            cc_to_nrpn_map[fader['value']] = (target_fader['value'], device1_config['channel'])

    for fader_id, fader in device2_config['faders'].items():
        target_fader = device1_config['faders'][fader_id]

        if fader['type'] == 'NRPN' and target_fader['type'] == 'NRPN':
            nrpn_to_nrpn_map_device2[fader['value']] = (target_fader['value'], device1_config['channel'])
        elif fader['type'] == 'control_change' and target_fader['type'] == 'control_change':
            cc_to_cc_map_device2[fader['value']] = (target_fader['value'], device1_config['channel'])
        elif fader['type'] == 'NRPN' and target_fader['type'] == 'control_change':
            nrpn_to_cc_map[fader['value']] = (target_fader['value'], device1_config['channel'])
        elif fader['type'] == 'control_change' and target_fader['type'] == 'NRPN':
            cc_to_nrpn_map[fader['value']] = (target_fader['value'], device2_config['channel'])

    return cc_to_cc_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device1, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map

def build_toggle_mappings(device1_config, device2_config):
    steps_button_map = {}

    for button_id, button in device1_config['fader_buttons'].items():
        if button_id in device2_config['fader_buttons']:
            button2 = device2_config['fader_buttons'][button_id]

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

    return steps_button_map

def get_conversion_function(config1, config2):
    config1_types = set(fader['type'] for fader in config1['faders'].values())
    config2_types = set(fader['type'] for fader in config2['faders'].values())

    if config1_types == {'NRPN'} and config2_types == {'NRPN'}:
        return nrpn_to_nrpn, nrpn_to_nrpn
    elif config1_types == {'control_change'} and config2_types == {'control_change'}:
        return cc_to_cc, cc_to_cc
    elif config1_types == {'NRPN'} and config2_types == {'control_change'}:
        return nrpn_to_cc, cc_to_nrpn
    elif config1_types == {'control_change'} and config2_types == {'NRPN'}:
        return cc_to_nrpn, nrpn_to_cc
    else:
        return None, None

def convert_to_dict(s):
    pairs = s.split(';')
    result = {}
    for pair in pairs:
        key, value = pair.split(':')
        result[int(key)] = int(value)
    return result

def listen_to_stdin(dhd_device_config, step_map, stdin_queue_device1, stdin_queue_device2, dhd_device, Radio_Assist_Faders_Location):
    try:
        for line in sys.stdin:
            if line.strip():
                print(f"Received from C#: {line.strip()}")
                sys.stdout.flush()

                hex_action = line.strip()
                if hex_action in gpio_to_fader_button_map:
                    Cart_stack_triggered, action = gpio_to_fader_button_map[hex_action]
                    steps = step_map[Radio_Assist_Faders_Location[Cart_stack_triggered]]
                    for step in steps[action]:
                        stdin_queue_device1.put((step["device1"], "device1"))
                        print("put in queue", step["device1"])

                    for step in steps[action]:
                        stdin_queue_device2.put((step["device2"], "device2"))
                        print("put in queue", step["device2"])
                else:
                    print(f"Unknown or malformed action received: {line.strip()}")
            else:
                print("Received an empty line")
                sys.stdout.flush()
    except Exception as e:
        print(f"Exception: {e}")
        sys.stdout.flush()

def main():
    if len(sys.argv) != 6:
        print(len(sys.argv))
        print("Usage: MIDI_mirror.py <device1> <device2> <dhd_enabled> <dhd_device>")
        sys.exit(1)

    device1 = sys.argv[1]
    device2 = sys.argv[2]
    dhd_enabled = sys.argv[3] == 'True'
    dhd_device = sys.argv[4]
    GPIO_fader_position = sys.argv[5]

    Radio_Assist_Faders_Location = {}
    
    device1_config = read_xml_config(f"{device1}.xml")
    device2_config = read_xml_config(f"{device2}.xml")

    if device1_config is None or device2_config is None:
        print("Error: Unable to read configuration files.")
        sys.exit(1)

    device1_config = parse_config(device1_config)
    device2_config = parse_config(device2_config)

    if dhd_device != "None":
        Radio_Assist_Faders_Location = convert_to_dict(GPIO_fader_position)
        if dhd_device == device1:
            dhd_config = device1_config
        elif dhd_device == device2:
            dhd_config = device2_config
        else:
            dhd_config = read_xml_config(f"{dhd_device}.xml")
            if dhd_config is None:
                print(f"Error: Unable to read DHD device configuration file '{dhd_device}.xml'.")
                sys.exit(1)
            dhd_config = parse_config(dhd_config)

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

    cc_to_cc_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device1, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map = build_fader_mappings(device1_config, device2_config)
    step_map = build_toggle_mappings(device1_config, device2_config)
    convert_func1, convert_func2 = get_conversion_function(device1_config, device2_config)

    stdin_queue_device1 = Queue()
    stdin_queue_device2 = Queue()

    if dhd_enabled:
        stdin_thread = threading.Thread(target=listen_to_stdin, args=(dhd_config, step_map, stdin_queue_device1, stdin_queue_device2, dhd_device, Radio_Assist_Faders_Location))
        stdin_thread.start()

        print("DHD is enabled. Listening for updates...")

    threading.Thread(target=mirror_midi, args=(
        "device1", device1_config['midi_in_name'], device2_config['midi_out_name'], 
        {device1_config['channel']: device2_config['channel']}, cc_to_cc_map_device1, nrpn_to_nrpn_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map, step_map, dhd_enabled, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location, convert_func1, dhd_device)).start()

    threading.Thread(target=mirror_midi, args=(
        "device2", device2_config['midi_in_name'], device1_config['midi_out_name'], 
        {device2_config['channel']: device1_config['channel']}, cc_to_cc_map_device1, nrpn_to_nrpn_map_device1, cc_to_cc_map_device2, nrpn_to_nrpn_map_device2, nrpn_to_cc_map, cc_to_nrpn_map, step_map, dhd_enabled, stdin_queue_device1, stdin_queue_device2, Radio_Assist_Faders_Location, convert_func2, dhd_device)).start()

if __name__ == "__main__":
    main()
