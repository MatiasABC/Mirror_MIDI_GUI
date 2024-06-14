import sys
import threading
import queue
import xml.etree.ElementTree as ET
import os
import mido

def cc_to_nrpn(cc_number, data_value, input_channel, channel_map):
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
            mido.Message('control_change', control=38, value=0, channel=output_channel)  # Assuming LSB of data value is 0
        ]
    return None

def nrpn_to_cc(nrpn_number, data_value, input_channel, channel_map, threshold=20, min_interval=0.5, max_interval=0.7):
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

# Function to run in a separate thread for listening to stdin
def listen_to_stdin(input_queue):
    for line in sys.stdin:
        input_queue.put(line.strip())

# Function to read and parse an XML configuration file
def read_xml_config(file_name):
    # Construct the path to the configs folder, which is one level higher
    configs_path = os.path.join(os.path.dirname(__file__), '..', 'configs', file_name)
    # Normalize the path to resolve any '..'
    full_path = os.path.normpath(configs_path)
    
    try:
        tree = ET.parse(full_path)
        root = tree.getroot()
        # Assuming you want to store the entire XML structure for later use
        return root
    except ET.ParseError as e:
        print(f"Error parsing XML file {full_path}: {e}")
    except FileNotFoundError:
        print(f"XML file not found: {full_path}")
    return None

# Check if DHD is enabled and set up a thread to listen to stdin if it is
def main():
    if len(sys.argv) != 5:
        print("Usage: MIDI_mirror.py <device1> <device2> <dhd_enabled> <dhd_device>")
        sys.exit(1)

    device1 = sys.argv[1]
    device2 = sys.argv[2]
    dhd_enabled = sys.argv[3] == 'True'
    dhd_device = sys.argv[4]
    print(device1, device2, dhd_enabled, dhd_device)

    # Read and store XML configurations for device1 and device2
    # Assuming the XML files are named as '<device_id>.xml'
    device1_config = read_xml_config(f"{device1}.xml")
    device2_config = read_xml_config(f"{device2}.xml")

    if dhd_enabled:
        input_queue = queue.Queue()
        stdin_listener_thread = threading.Thread(target=listen_to_stdin, args=(input_queue,))
        stdin_listener_thread.daemon = True  # Daemonize thread
        stdin_listener_thread.start()

        print("DHD is enabled. Listening for updates...")

        # Example main loop
        try:
            while True:
                # Check if there's new data from stdin
                if not input_queue.empty():
                    data = input_queue.get()
                    print(f"Received update: {data}")
                # Your main script logic here
                # For demonstration, we'll just pass to simulate doing work
                pass
        except KeyboardInterrupt:
            print("Exiting...")

    else:
        print("DHD is not enabled. Proceeding without listening for updates.")
        # Your main script logic here without DHD updates

if __name__ == "__main__":
    main()