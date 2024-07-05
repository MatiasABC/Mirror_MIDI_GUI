using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using System.Drawing;
using System.Collections.Generic;

namespace Mirror_MIDI
{
    public partial class Form1 : Form
    {
        private Process pythonProcess;
        private DHDServer dhdServer;
        private List<CheckBox> selectedCheckBoxes = new List<CheckBox>();
        private CheckBox[] checkBoxes;

        public Form1()
        {
            InitializeComponent();
            PopulateDeviceLists();

            // Add the FormClosing event handler
            this.FormClosing += new FormClosingEventHandler(Form1_FormClosing);

            // Initialize checkBoxes array
            checkBoxes = new CheckBox[] { Cart1, Cart2, Cart3, Cart4, Cart5, Cart6, Cart7, Cart8 };

            // Add CheckedChanged event handlers for checkboxes
            AddCheckBoxEventHandlers();
        }

        private void AddCheckBoxEventHandlers()
        {
            foreach (var checkBox in checkBoxes)
            {
                checkBox.CheckedChanged += CheckBox_CheckedChanged;
            }
        }

        private void CheckBox_CheckedChanged(object sender, EventArgs e)
        {
            CheckBox checkBox = sender as CheckBox;

            if (checkBox.Checked)
            {
                if (selectedCheckBoxes.Count < 4)
                {
                    selectedCheckBoxes.Add(checkBox);
                }
                else
                {
                    checkBox.Checked = false;
                }
            }
            else
            {
                selectedCheckBoxes.Remove(checkBox);
            }

            UpdateCheckBoxStates();
        }

        private void UpdateCheckBoxStates()
        {
            bool canCheckMore = selectedCheckBoxes.Count < 4;

            foreach (var checkBox in checkBoxes)
            {
                if (!selectedCheckBoxes.Contains(checkBox))
                {
                    checkBox.Enabled = canCheckMore;
                }
            }
        }

        private Dictionary<int, int> GetSelectedCheckBoxesDictionary()
        {
            Dictionary<int, int> selectedDict = new Dictionary<int, int>();

            for (int i = 0; i < selectedCheckBoxes.Count; i++)
            {
                CheckBox checkBox = selectedCheckBoxes[i];
                int position = int.Parse(checkBox.Name.Replace("Cart", ""));
                selectedDict[i + 1] = position;
            }

            // Print the dictionary to the console for debugging
            foreach (var kvp in selectedDict)
            {
                Debug.WriteLine($"Fader {kvp.Key}: Cart {kvp.Value}");
            }

            return selectedDict;
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
                
                if (selectedCheckBoxes.Count == 0)
                {
                    MessageBox.Show("At least one checkbox must be selected when DHD is enabled.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
            Dictionary<int, int> selectedButtonsDict = GetSelectedCheckBoxesDictionary();
            StartPythonScript(Device1.SelectedItem.ToString(), Device2.SelectedItem.ToString(), dhdEnabled, dhdDeviceSelection, selectedButtonsDict);
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

        private void StartPythonScript(string device1, string device2, string dhdEnabled, string dhdDevice, Dictionary<int, int> selectedButtonsDict)
        {
            string scriptName = "MIDI_mirror.py";
            string scriptPath = GetPythonScriptPath(scriptName);

            if (pythonProcess != null)
            {
                StopPythonScript();
            }

            string selectedButtonsArg = string.Join(";", selectedButtonsDict.Select(kvp => $"{kvp.Key}:{kvp.Value}"));

            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"\"{scriptPath}\" \"{device1}\" \"{device2}\" \"{dhdEnabled}\" \"{dhdDevice}\" \"{selectedButtonsArg}\"",                
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                RedirectStandardInput = true,
                CreateNoWindow = true
            };

            Debug.WriteLine($"\"{scriptPath}\" \"{device1}\" \"{device2}\" \"{dhdEnabled}\" \"{dhdDevice}\" \"{selectedButtonsArg}\"");
            pythonProcess = new Process { StartInfo = startInfo };
            pythonProcess.OutputDataReceived += PythonProcess_OutputDataReceived;
            pythonProcess.ErrorDataReceived += PythonProcess_ErrorDataReceived;
            pythonProcess.Start();
            pythonProcess.BeginOutputReadLine();
            pythonProcess.BeginErrorReadLine();
        }

        private void StopPythonScript()
        {
            if (pythonProcess != null)
            {
                try
                {
                    ProcessStartInfo killStartInfo = new ProcessStartInfo
                    {
                        FileName = "cmd.exe",
                        Arguments = $"/c taskkill /F /T /PID {pythonProcess.Id}",
                        UseShellExecute = true,
                        RedirectStandardOutput = false,
                        RedirectStandardError = false,
                        CreateNoWindow = true
                    };

                    using (var killProcess = new Process { StartInfo = killStartInfo })
                    {
                        killProcess.Start();
                        killProcess.WaitForExit();
                    }
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
            Fader_Label.Visible = isChecked;
            Cart1_Label.Visible = isChecked;
            Cart2_Label.Visible = isChecked;
            Cart3_Label.Visible = isChecked;
            Cart4_Label.Visible = isChecked;
            Cart5_Label.Visible = isChecked;
            Cart6_Label.Visible = isChecked;
            Cart7_Label.Visible = isChecked;
            Cart8_Label.Visible = isChecked;
            Cart_Stack_Label.Visible = isChecked;
            Cart1.Visible = isChecked;
            Cart2.Visible = isChecked;
            Cart3.Visible = isChecked;
            Cart4.Visible = isChecked;
            Cart5.Visible = isChecked;
            Cart6.Visible = isChecked;
            Cart7.Visible = isChecked;
            Cart8.Visible = isChecked;

            // Ensure the server is only created once and controlled based on checkbox state
            if (dhdServer == null)
            {
                // Initialize the server with event handlers that can send messages to the Python script
                dhdServer = new DHDServer(OnClientConnected, OnClientDisconnected, SendMessageToPythonScript);

            }

            if (isChecked)
            {
                dhdServer.Start();
            }
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            StopPythonScript();
        }

        private void SendMessageToPythonScript(string message)
        {
            if (pythonProcess != null && !pythonProcess.HasExited)
            {
                pythonProcess.StandardInput.WriteLine(message);
                pythonProcess.StandardInput.Flush();
            }
        }

        private void PythonProcess_OutputDataReceived(object sender, DataReceivedEventArgs e)
        {
            if (!string.IsNullOrEmpty(e.Data))
            {
                this.Invoke(new Action(() =>
                {
                    Debug.WriteLine(e.Data, "Python Output");
                }));
            }
        }

        private void PythonProcess_ErrorDataReceived(object sender, DataReceivedEventArgs e)
        {
            if (!string.IsNullOrEmpty(e.Data))
            {
                this.Invoke(new Action(() =>
                {
                    Debug.WriteLine(e.Data, "Python Error");
                }));
            }
        }
    }
}
