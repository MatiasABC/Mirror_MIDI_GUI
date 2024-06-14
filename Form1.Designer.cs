namespace Mirror_MIDI
{
    partial class Form1
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            label1 = new Label();
            Start = new Button();
            Stop = new Button();
            label2 = new Label();
            DHD_Status = new TextBox();
            Device1 = new ComboBox();
            Device2 = new ComboBox();
            DHD_Enabled = new CheckBox();
            DHD_Device = new ComboBox();
            SuspendLayout();
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            label1.Location = new Point(238, 12);
            label1.Name = "label1";
            label1.Size = new Size(78, 31);
            label1.TabIndex = 1;
            label1.Text = "Mirror";
            // 
            // Start
            // 
            Start.Location = new Point(576, 12);
            Start.Name = "Start";
            Start.Size = new Size(94, 35);
            Start.TabIndex = 3;
            Start.Text = "Start";
            Start.UseVisualStyleBackColor = true;
            Start.Click += Start_Click;
            // 
            // Stop
            // 
            Stop.Location = new Point(576, 53);
            Stop.Name = "Stop";
            Stop.Size = new Size(94, 35);
            Stop.TabIndex = 4;
            Stop.Text = "Stop";
            Stop.UseVisualStyleBackColor = true;
            Stop.Click += Stop_Click;
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            label2.Location = new Point(12, 57);
            label2.Name = "label2";
            label2.Size = new Size(62, 31);
            label2.TabIndex = 5;
            label2.Text = "DHD";
            // 
            // DHD_Status
            // 
            DHD_Status.BackColor = Color.Firebrick;
            DHD_Status.BorderStyle = BorderStyle.FixedSingle;
            DHD_Status.Enabled = false;
            DHD_Status.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            DHD_Status.Location = new Point(274, 55);
            DHD_Status.Name = "DHD_Status";
            DHD_Status.ReadOnly = true;
            DHD_Status.Size = new Size(172, 38);
            DHD_Status.TabIndex = 6;
            DHD_Status.Text = " Not Connected";
            DHD_Status.Visible = false;
            DHD_Status.TextChanged += DHD_Status_TextChanged;
            // 
            // Device1
            // 
            Device1.AllowDrop = true;
            Device1.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            Device1.FormattingEnabled = true;
            Device1.Location = new Point(60, 10);
            Device1.Name = "Device1";
            Device1.Size = new Size(172, 39);
            Device1.TabIndex = 7;
            // 
            // Device2
            // 
            Device2.AllowDrop = true;
            Device2.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            Device2.FormattingEnabled = true;
            Device2.Location = new Point(322, 9);
            Device2.Name = "Device2";
            Device2.Size = new Size(172, 39);
            Device2.TabIndex = 8;
            // 
            // DHD_Enabled
            // 
            DHD_Enabled.AutoSize = true;
            DHD_Enabled.Location = new Point(76, 67);
            DHD_Enabled.Name = "DHD_Enabled";
            DHD_Enabled.Size = new Size(18, 17);
            DHD_Enabled.TabIndex = 9;
            DHD_Enabled.UseVisualStyleBackColor = true;
            DHD_Enabled.CheckedChanged += DHD_Enabled_CheckedChanged;
            // 
            // DHD_Device
            // 
            DHD_Device.AllowDrop = true;
            DHD_Device.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            DHD_Device.FormattingEnabled = true;
            DHD_Device.Location = new Point(100, 55);
            DHD_Device.Name = "DHD_Device";
            DHD_Device.Size = new Size(172, 39);
            DHD_Device.TabIndex = 10;
            DHD_Device.Visible = false;
            // 
            // Form1
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            BackColor = SystemColors.AppWorkspace;
            ClientSize = new Size(682, 127);
            Controls.Add(DHD_Device);
            Controls.Add(DHD_Enabled);
            Controls.Add(Device2);
            Controls.Add(Device1);
            Controls.Add(DHD_Status);
            Controls.Add(label2);
            Controls.Add(Stop);
            Controls.Add(Start);
            Controls.Add(label1);
            Name = "Form1";
            Text = "Mirror MIDI";
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion
        private Label label1;
        private Button Start;
        private Button Stop;
        private Label label2;
        private TextBox DHD_Status;
        private ComboBox Device1;
        private ComboBox Device2;
        private CheckBox DHD_Enabled;
        private ComboBox DHD_Device;
    }
}
