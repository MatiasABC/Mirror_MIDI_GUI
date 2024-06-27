using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Diagnostics;

namespace Mirror_MIDI
{
    public class DHDServer
    {
        private const string HOST = "0.0.0.0";
        private const int PORT = 4646;
        private Thread serverThread;
        private bool isRunning;
        private Action onClientConnected;
        private Action onClientDisconnected;
        private Action<string> onDataReceived;
        public DHDServer(Action onClientConnected, Action onClientDisconnected, Action<string> onDataReceived)
        {
            this.onClientConnected = onClientConnected;
            this.onClientDisconnected = onClientDisconnected;
            this.onDataReceived = onDataReceived;
        }

        public void Start()
        {
            serverThread = new Thread(new ThreadStart(RunServer));
            serverThread.IsBackground = true;
            serverThread.Start();
        }

        private void RunServer()
        {
            isRunning = true;

            try
            {
                using (Socket serverSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp))
                {
                    serverSocket.Bind(new IPEndPoint(IPAddress.Parse(HOST), PORT));
                    serverSocket.Listen(10);

                    while (isRunning)
                    {
                        Socket clientSocket = serverSocket.Accept();
                        onClientConnected?.Invoke();

                        Thread clientThread = new Thread(() => HandleClient(clientSocket));
                        clientThread.IsBackground = true;
                        clientThread.Start();
                    }
                }
            } 
            catch (Exception ex)
            {
                Console.WriteLine($"Server error: {ex.Message}");
            }
        }

        private void HandleClient(Socket clientSocket)
        {
            try
            {
                using (clientSocket)
                {
                    byte[] buffer = new byte[1024];
                    int received;
                    List<string> receivedMessages = new List<string>();
                    DateTime lastMessageTime = DateTime.Now;

                    while (true)
                    {
                        received = clientSocket.Receive(buffer);
                        if (received == 0)
                            break;  // Client has disconnected

                        string formattedData = BitConverter.ToString(buffer, 0, received).Replace("-", ",");
                        Debug.WriteLine($"Received from client: {formattedData}");

                        // Filter out startup messages
                        if (formattedData.StartsWith("02,00"))
                            continue;

                        receivedMessages.Add(formattedData);
                        lastMessageTime = DateTime.Now;

                        // Process messages if no new messages are received within 0.2 seconds
                        while ((DateTime.Now - lastMessageTime).TotalSeconds < 0.2)
                        {
                            if (clientSocket.Available > 0)
                            {
                                received = clientSocket.Receive(buffer);
                                formattedData = BitConverter.ToString(buffer, 0, received).Replace("-", ",");
                                Debug.WriteLine($"Received from client: {formattedData}");
                                receivedMessages.Add(formattedData);
                                lastMessageTime = DateTime.Now;
                            }
                        }

                        // Process collected messages
                        ProcessMessages(receivedMessages);
                        receivedMessages.Clear();
                    }

                    onClientDisconnected?.Invoke();
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Client error: {ex.Message}");
                onClientDisconnected?.Invoke();
            }
        }
        private void ProcessMessages(List<string> messages)
        {
            // Process each GPIO accordingly
            ProcessGPIO(messages, "2A", "GPIO 0");
            ProcessGPIO(messages, "2B", "GPIO 1");
            ProcessGPIO(messages, "2D", "GPIO 2");
            ProcessGPIO(messages, "2E", "GPIO 3");
        }
        private void ProcessGPIO(List<string> messages, string gpioCode, string gpioName)
        {
            var gpioMessages = messages.Where(m => m.Contains($"03,00,11,0E,00,00,00,{gpioCode}")).ToList();

            // Define the mapping for the GPIO to hex codes directly
            var gpio_to_hex_map = new Dictionary<string, string>
    {
        {"2A00", "2A00"},
        {"2A01", "2A01"},
        {"2B00", "2B00"},
        {"2B01", "2B01"},
        {"2C00", "2C00"},
        {"2C01", "2C01"},
        {"2D00", "2D00"},
        {"2D01", "2D01"},
        {"2E00", "2E00"},
        {"2E01", "2E01"}
    };

            // Check for GPIO ON
            if (gpioMessages.Count == 1 && gpioMessages[0].EndsWith("00,00,00,00,00,00,00,00"))
            {
                Debug.WriteLine($"{gpioName} ON");
                onDataReceived?.Invoke(gpio_to_hex_map[gpioCode + "00"]);
            }
            // Check for GPIO OFF
            else if (gpioMessages.Count == 3 &&
                     gpioMessages[0].EndsWith("00,00,00,00,00,00,00,00") &&
                     gpioMessages[1].EndsWith("01,00,00,00,00,00,00,00") &&
                     gpioMessages[2].EndsWith("00,00,00,00,00,00,00,00"))
            {
                Debug.WriteLine($"{gpioName} OFF");
                onDataReceived?.Invoke(gpio_to_hex_map[gpioCode + "01"]);
            }
        }


        public void Stop()
        {
            isRunning = false;
            serverThread.Join();
        }
    }
}
