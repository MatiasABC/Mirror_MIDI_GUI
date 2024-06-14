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

            Device1.Enabled = false;
            Device2.Enabled = false;
            DHD_Enabled.Enabled = false;
            DHD_Device.Enabled = false;
            Start.Enabled = false;  
            string dhdEnabled = DHD_Enabled.Checked ? "True" : "False";
            string dhdDeviceSelection = DHD_Device.SelectedItem?.ToString() ?? "None";

            // Assuming the Python script is located in a "scripts" folder at the base directory of the project
            string baseDirectory = AppDomain.CurrentDomain.BaseDirectory;


            // Start the Python script with the selected parameters
            StartPythonScriptAsync(Device1.SelectedItem.ToString(), Device2.SelectedItem.ToString(), dhdEnabled, dhdDeviceSelection);

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

            // Terminate the Python process if it's running
            if (pythonProcess != null && !pythonProcess.HasExited)
            {
                pythonProcess.Kill();
                pythonProcess.WaitForExit(); // Optional: Wait for the process to exit
                pythonProcess.Dispose();
                pythonProcess = null;
            }

            Device1.Enabled = true;
            Device2.Enabled = true;
            DHD_Enabled.Enabled = true; 
            DHD_Device.Enabled = true;
            Start.Enabled = true;
            
        }

        private async void DHD_Enabled_CheckedChanged(object sender, EventArgs e)
        {
            bool isChecked = DHD_Enabled.Checked;
            DHD_Status.Visible = isChecked;
            DHD_Device.Visible = isChecked;

            if (isChecked)
            {
                if (dhdServer == null)
                {
                    dhdServer = new DHDServer(OnClientConnected, OnClientDisconnected);
                    await Task.Run(() => dhdServer.Start());
                }
            }

        }
        private Process pythonProcess;
        private string GetPythonScriptPath(string scriptName)
        {
            // Get the full path to the directory where the executable is running
            string exeDirectory = AppDomain.CurrentDomain.BaseDirectory;

            // Construct the path to the "scripts" folder by navigating up two levels from the exe directory
            // and then into the "scripts" folder
            string scriptPath = Path.Combine(exeDirectory, "..", "..", "..", "scripts", scriptName);

            // Get the absolute path (resolving any "..")
            scriptPath = Path.GetFullPath(scriptPath);

            return scriptPath;
        }
        private Process StartPythonScriptAsync(string arg1, string arg2, string arg3, string arg4)
        {
            string scriptName = "MIDI_mirror.py";
            string scriptPath = GetPythonScriptPath(scriptName);

            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"\"{scriptPath}\" \"{arg1}\" \"{arg2}\" \"{arg3}\" \"{arg4}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            Process pythonProcess = new Process { StartInfo = startInfo };
            pythonProcess.OutputDataReceived += (sender, args) => Debug.WriteLine(args.Data);
            pythonProcess.ErrorDataReceived += (sender, args) => Debug.WriteLine(args.Data);

            pythonProcess.Start();
            pythonProcess.BeginOutputReadLine();
            pythonProcess.BeginErrorReadLine();

            return pythonProcess; // Return the process in case you need to interact with it later
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
