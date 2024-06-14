using System;
using System.IO;
using System.Threading;
using System.Windows.Forms;
using System.Drawing;
using System.Diagnostics; // Added for setting BackColor

namespace Mirror_MIDI
{
    public partial class Form1 : Form
    {
        private DHDServer dhdServer;

        public Form1()
        {
            InitializeComponent();
            PopulateDeviceLists();
        }

        private void PopulateDeviceLists()
        {
            // Assuming the "configs" folder is at the base directory of the project
            string baseDirectory = AppDomain.CurrentDomain.BaseDirectory;
            string configPath = Path.Combine(baseDirectory, "..", "..", "..", "configs");

            if (Directory.Exists(configPath))
            {
                string[] configFiles = Directory.GetFiles(configPath);

                foreach (string configFile in configFiles)
                {
                    string fileNameWithoutExtension = Path.GetFileNameWithoutExtension(configFile);
                    Device1.Items.Add(fileNameWithoutExtension);
                    Device2.Items.Add(fileNameWithoutExtension);
                    DHD_Device.Items.Add(fileNameWithoutExtension);
                }
            }
            else
            {
                MessageBox.Show("Config folder not found!", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void Device1_SelectedIndexChanged(object sender, EventArgs e)
        {
            // Handle selection change for Device1 if needed
        }

        private void Start_Click(object sender, EventArgs e)
        {
            if (Device1.SelectedItem == null || Device2.SelectedItem == null)
            {
                MessageBox.Show("Both devices must be selected.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            if (Device1.SelectedItem.ToString() == Device2.SelectedItem.ToString())
            {
                MessageBox.Show("Both devices cannot be the same.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            if (DHD_Enabled.Checked)
            {
                if (DHD_Device.SelectedItem == null)
                {
                    MessageBox.Show("DHD device must be selected when DHD is enabled.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                if (DHD_Status.Text != " Connected")
                {
                    MessageBox.Show("Please wait for DHD connection to be established.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }
            }

            string dhdEnabled = DHD_Enabled.Checked ? "True" : "False";
            string dhdDeviceSelection = DHD_Device.SelectedItem?.ToString() ?? "None";

            // Assuming the Python script is located in a "scripts" folder at the base directory of the project
            string baseDirectory = AppDomain.CurrentDomain.BaseDirectory;
            string scriptPath = Path.Combine(baseDirectory, "..", "..", "..", "scripts", "MIDI_mirror.py");

            // Start the Python script with the selected parameters
            StartPythonScript(scriptPath, Device1.SelectedItem.ToString(), Device2.SelectedItem.ToString(), dhdEnabled, dhdDeviceSelection);

            MessageBox.Show("Python script started.", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void OnClientConnected()
        {
            this.Invoke(new Action(() =>
            {
                DHD_Status.Text = " Connected";
                DHD_Status.BackColor = Color.LimeGreen;
            }));
        }

        private void OnClientDisconnected()
        {
            this.Invoke(new Action(() =>
            {
                DHD_Status.Text = " Disconnected";
                DHD_Status.BackColor = Color.Red;
            }));
        }

        private void DHD_Status_TextChanged(object sender, EventArgs e)
        {
            // Handle text change for DHD_Status if needed
        }

        private void Stop_Click(object sender, EventArgs e)
        {
            if (dhdServer != null)
            {
                dhdServer.Stop();
                dhdServer = null;
            }

            // Handle logic to stop the process if needed
        }

        private void DHD_Enabled_CheckedChanged(object sender, EventArgs e)
        {
            bool isChecked = DHD_Enabled.Checked;
            DHD_Status.Visible = isChecked;
            DHD_Device.Visible = isChecked;

            if (isChecked)
            {
                if (dhdServer == null)
                {
                    dhdServer = new DHDServer(OnClientConnected, OnClientDisconnected);
                    dhdServer.Start();
                }
            }
            else
            {
                if (dhdServer != null)
                {
                    dhdServer.Stop();
                    dhdServer = null;
                }
                DHD_Status.Text = "";
                DHD_Status.BackColor = SystemColors.Window;
            }
        }
        private Process pythonProcess;

        private void StartPythonScript(string scriptPath, string arg1, string arg2, string arg3, string arg4)
        {
            string pythonExePath = "python";

            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = pythonExePath,
                Arguments = $"\"{scriptPath}\" \"{arg1}\" \"{arg2}\"\"{arg3}\"", // Include initial arguments
                UseShellExecute = false,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            pythonProcess = new Process { StartInfo = startInfo };
            pythonProcess.OutputDataReceived += (sender, args) => Console.WriteLine(args.Data);
            pythonProcess.ErrorDataReceived += (sender, args) => Console.WriteLine(args.Data);

            pythonProcess.Start();
            pythonProcess.BeginOutputReadLine();
            pythonProcess.BeginErrorReadLine();
        }

        private void SendDataToPythonScript(string data)
        {
            if (pythonProcess != null && !pythonProcess.HasExited)
            {
                pythonProcess.StandardInput.WriteLine(data);
            }
        }
    }
}
