using System;
using System.IO;
using System.Threading;
using System.Windows.Forms;

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
                    MessageBox.Show("Please wait for DHD connection to be stablished.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

            }

            // Proceed with further logic if validation is successful
            MessageBox.Show("Logic to start the process can be implemented here.", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void OnClientConnected()
        {
            this.Invoke(new Action(() =>
            {
                DHD_Status.Text = " Connected";
                DHD_Status.BackColor = Color.LimeGreen;
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
            if (dhdServer == null)
            {
                dhdServer = new DHDServer(OnClientConnected);
                dhdServer.Start();
            }
            bool isChecked = DHD_Enabled.Checked;
            DHD_Status.Visible = isChecked;
            DHD_Device.Visible = isChecked;
        }
    }
}