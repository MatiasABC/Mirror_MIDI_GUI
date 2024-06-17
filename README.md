# Mirror_MIDI
# MIDI Mirror Application

The MIDI Mirror Application is designed to facilitate real-time mirroring of MIDI messages between two devices, with the added capability to convert between Control Change (CC) and Non-Registered Parameter Number (NRPN) messages based on configurable mappings. It also supports integration with a DHD server for enhanced functionality.

## Features

- **MIDI Mirroring**: Bidirectional mirroring of MIDI messages between two configured devices.
- **CC to NRPN Conversion**: Dynamically converts CC messages to NRPN messages based on predefined mappings.
- **NRPN to CC Conversion**: Converts NRPN messages back to CC messages, allowing for flexible device compatibility.
- **DHD Server Integration**: Optional integration with a DHD server for additional control and functionality.
- **Configurable Mappings**: Easily configure device mappings and message conversions through XML configuration files.
- **Real-time Updates**: Supports real-time updates without the need to restart the application for configuration changes.

## Requirements

- Windows 10 or later / macOS / Linux
- .NET Framework 4.7.2 or later / .NET Core 3.1 or later (for cross-platform compatibility)
- MIDI-compatible devices
- Optional: DHD server for enhanced features

## Installation

1. Clone the repository or download the source code.
2. Open the solution in Visual Studio.
3. Restore NuGet packages.
4. Build the solution.
5. Run the application from Visual Studio or navigate to the `bin` directory to run the executable directly.

## Configuration

1. Edit the XML configuration files located in the `configs` directory to set up your MIDI devices and mappings.
2. If using DHD server integration, ensure the server is running and accessible.
3. Adjust the application settings as necessary to connect to the DHD server and configure device mappings.

## Usage

1. Launch the MIDI Mirror Application.
2. Use the GUI to select your MIDI input and output devices.
3. Check the "Enable DHD" checkbox if you wish to use DHD server functionality.
4. Press the "Start" button to begin mirroring MIDI messages.
5. To stop the application, press the "Stop" button.

## Troubleshooting

- Ensure that your MIDI devices are correctly connected and recognized by your operating system.
- Verify that the XML configuration files are correctly formatted and located in the expected directory.
- If using DHD server integration, ensure the server is running and correctly configured to accept connections from the application.


## License

This project is licensed under the MIT License - see the LICENSE file for details.
