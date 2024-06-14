import sys
import threading
import queue

print("test")
# Function to run in a separate thread for listening to stdin
def listen_to_stdin(input_queue):
    for line in sys.stdin:
        input_queue.put(line.strip())

# Check if DHD is enabled and set up a thread to listen to stdin if it is
def main():
    if len(sys.argv) != 5:
        print("Usage: MIDI_mirror.py <device1> <device2> <dhd_enabled> <dhd_device>")
        sys.exit(1)

    device1 = sys.argv[1]
    device2 = sys.argv[2]
    dhd_enabled = sys.argv[3] == 'True'
    dhd_device = sys.argv[4]
    print(device1,device2,dhd_enabled, dhd_device)
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