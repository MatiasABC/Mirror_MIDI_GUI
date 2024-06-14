using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace Mirror_MIDI
{
    public class DHDServer
    {
        private const string HOST = "0.0.0.0";
        private const int PORT = 4646;
        private Thread serverThread;
        private bool isRunning;
        private Action onClientConnected;

        public DHDServer(Action onClientConnected)
        {
            this.onClientConnected = onClientConnected;
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
                // Handle exception (e.g., log it)
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

                    while ((received = clientSocket.Receive(buffer, SocketFlags.None)) > 0)
                    {
                        string formattedData = BitConverter.ToString(buffer, 0, received).Replace("-", ",");
                        Console.WriteLine($"Received from client: {formattedData}");
                    }
                }
            }
            catch (Exception ex)
            {
                // Handle client exception (e.g., log it)
                Console.WriteLine($"Client error: {ex.Message}");
            }
        }

        public void Stop()
        {
            isRunning = false;
            serverThread.Join();
        }
    }
}
