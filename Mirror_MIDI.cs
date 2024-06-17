using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
using System.Drawing;

namespace Mirror_MIDI
{
    public partial class Form1 : Form
    {
        private Process pythonProcess;

        public Form1()
        {
            InitializeComponent();
            PopulateDeviceLists();
        }

        private void PopulateDeviceLists()
        {
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

            StartPythonScript(Device1.SelectedItem.ToString(), Device2.SelectedItem.ToString(), dhdEnabled, dhdDeviceSelection);
        }

        private void Stop_Click(object sender, EventArgs e)
        {
            StopPythonScript();

            Device1.Enabled = true;
            Device2.Enabled = true;
            DHD_Enabled.Enabled = true;
            DHD_Device.Enabled = true;
            Start.Enabled = true;
        }

        private void StartPythonScript(string device1, string device2, string dhdEnabled, string dhdDevice)
        {
            string scriptName = "MIDI_mirror.py";
            string scriptPath = GetPythonScriptPath(scriptName);

            if (pythonProcess != null)
            {
                StopPythonScript();
            }

            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = $"/C python \"{scriptPath}\" \"{device1}\" \"{device2}\" \"{dhdEnabled}\" \"{dhdDevice}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = false // Change to false to see the terminal window
            };

            pythonProcess = new Process { StartInfo = startInfo };
            pythonProcess.OutputDataReceived += (sender, args) => Debug.WriteLine(args.Data);
            pythonProcess.ErrorDataReceived += (sender, args) => Debug.WriteLine(args.Data);

            pythonProcess.Start();
            pythonProcess.BeginOutputReadLine();
            pythonProcess.BeginErrorReadLine();
        }

        private void StopPythonScript()
        {
            if (pythonProcess != null && !pythonProcess.HasExited)
            {
                try
                {
                    pythonProcess.Kill();
                    pythonProcess.WaitForExit();
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"Error stopping Python script: {ex.Message}");
                }
                finally
                {
                    pythonProcess.Dispose();
                    pythonProcess = null;
                }
            }
        }

        private string GetPythonScriptPath(string scriptName)
        {
            string exeDirectory = AppDomain.CurrentDomain.BaseDirectory;
            string scriptPath = Path.Combine(exeDirectory, "..", "..", "..", "scripts", scriptName);
            scriptPath = Path.GetFullPath(scriptPath);
            return scriptPath;
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

        private void DHD_Enabled_CheckedChanged(object sender, EventArgs e)
        {
            bool isChecked = DHD_Enabled.Checked;
            DHD_Status.Visible = isChecked;
            DHD_Device.Visible = isChecked;
        }
    }
}
