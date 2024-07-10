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
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(Form1));
            label1 = new Label();
            Start = new Button();
            Stop = new Button();
            label2 = new Label();
            DHD_Status = new TextBox();
            Device1 = new ComboBox();
            Device2 = new ComboBox();
            DHD_Enabled = new CheckBox();
            DHD_Device = new ComboBox();
            Fader_Label = new Label();
            Cart1_Label = new Label();
            Cart2_Label = new Label();
            Cart3_Label = new Label();
            Cart4_Label = new Label();
            Cart5_Label = new Label();
            Cart6_Label = new Label();
            Cart7_Label = new Label();
            Cart8_Label = new Label();
            Cart_Stack_Label = new Label();
            Cart1 = new CheckBox();
            Cart2 = new CheckBox();
            Cart3 = new CheckBox();
            Cart4 = new CheckBox();
            Cart5 = new CheckBox();
            Cart6 = new CheckBox();
            Cart7 = new CheckBox();
            Cart8 = new CheckBox();
            OnAirLights_checkbox = new CheckBox();
            label3 = new Label();
            COM_options = new ComboBox();
            SuspendLayout();
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            label1.Location = new Point(190, 13);
            label1.Name = "label1";
            label1.Size = new Size(78, 31);
            label1.TabIndex = 1;
            label1.Text = "Mirror";
            // 
            // Start
            // 
            Start.Location = new Point(490, 10);
            Start.Name = "Start";
            Start.Size = new Size(94, 35);
            Start.TabIndex = 3;
            Start.Text = "Start";
            Start.UseVisualStyleBackColor = true;
            Start.Click += Start_Click;
            // 
            // Stop
            // 
            Stop.Location = new Point(490, 51);
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
            label2.Location = new Point(12, 55);
            label2.Name = "label2";
            label2.Size = new Size(138, 31);
            label2.TabIndex = 5;
            label2.Text = "Radio Assist";
            // 
            // DHD_Status
            // 
            DHD_Status.BackColor = Color.Firebrick;
            DHD_Status.BorderStyle = BorderStyle.FixedSingle;
            DHD_Status.Enabled = false;
            DHD_Status.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            DHD_Status.Location = new Point(12, 139);
            DHD_Status.Name = "DHD_Status";
            DHD_Status.ReadOnly = true;
            DHD_Status.Size = new Size(172, 38);
            DHD_Status.TabIndex = 6;
            DHD_Status.Text = " Not Connected";
            DHD_Status.Visible = false;
            // 
            // Device1
            // 
            Device1.AllowDrop = true;
            Device1.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            Device1.FormattingEnabled = true;
            Device1.Location = new Point(12, 10);
            Device1.Name = "Device1";
            Device1.Size = new Size(172, 39);
            Device1.TabIndex = 7;
            // 
            // Device2
            // 
            Device2.AllowDrop = true;
            Device2.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            Device2.FormattingEnabled = true;
            Device2.Location = new Point(274, 10);
            Device2.Name = "Device2";
            Device2.Size = new Size(172, 39);
            Device2.TabIndex = 8;
            // 
            // DHD_Enabled
            // 
            DHD_Enabled.AutoSize = true;
            DHD_Enabled.Location = new Point(156, 67);
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
            DHD_Device.Location = new Point(12, 94);
            DHD_Device.Name = "DHD_Device";
            DHD_Device.Size = new Size(172, 39);
            DHD_Device.TabIndex = 10;
            DHD_Device.Visible = false;
            // 
            // Fader_Label
            // 
            Fader_Label.AutoSize = true;
            Fader_Label.Location = new Point(341, 106);
            Fader_Label.Name = "Fader_Label";
            Fader_Label.Size = new Size(51, 20);
            Fader_Label.TabIndex = 11;
            Fader_Label.Text = "Faders";
            Fader_Label.Visible = false;
            // 
            // Cart1_Label
            // 
            Cart1_Label.AutoSize = true;
            Cart1_Label.Location = new Point(285, 126);
            Cart1_Label.Name = "Cart1_Label";
            Cart1_Label.Size = new Size(17, 20);
            Cart1_Label.TabIndex = 12;
            Cart1_Label.Text = "1";
            Cart1_Label.Visible = false;
            // 
            // Cart2_Label
            // 
            Cart2_Label.AutoSize = true;
            Cart2_Label.Location = new Point(308, 126);
            Cart2_Label.Name = "Cart2_Label";
            Cart2_Label.Size = new Size(17, 20);
            Cart2_Label.TabIndex = 13;
            Cart2_Label.Text = "2";
            Cart2_Label.Visible = false;
            // 
            // Cart3_Label
            // 
            Cart3_Label.AutoSize = true;
            Cart3_Label.Location = new Point(331, 126);
            Cart3_Label.Name = "Cart3_Label";
            Cart3_Label.Size = new Size(17, 20);
            Cart3_Label.TabIndex = 14;
            Cart3_Label.Text = "3";
            Cart3_Label.Visible = false;
            // 
            // Cart4_Label
            // 
            Cart4_Label.AutoSize = true;
            Cart4_Label.Location = new Point(354, 126);
            Cart4_Label.Name = "Cart4_Label";
            Cart4_Label.Size = new Size(17, 20);
            Cart4_Label.TabIndex = 15;
            Cart4_Label.Text = "4";
            Cart4_Label.Visible = false;
            // 
            // Cart5_Label
            // 
            Cart5_Label.AutoSize = true;
            Cart5_Label.Location = new Point(377, 126);
            Cart5_Label.Name = "Cart5_Label";
            Cart5_Label.Size = new Size(17, 20);
            Cart5_Label.TabIndex = 16;
            Cart5_Label.Text = "5";
            Cart5_Label.Visible = false;
            // 
            // Cart6_Label
            // 
            Cart6_Label.AutoSize = true;
            Cart6_Label.Location = new Point(400, 126);
            Cart6_Label.Name = "Cart6_Label";
            Cart6_Label.Size = new Size(17, 20);
            Cart6_Label.TabIndex = 17;
            Cart6_Label.Text = "6";
            Cart6_Label.Visible = false;
            // 
            // Cart7_Label
            // 
            Cart7_Label.AutoSize = true;
            Cart7_Label.Location = new Point(423, 126);
            Cart7_Label.Name = "Cart7_Label";
            Cart7_Label.Size = new Size(17, 20);
            Cart7_Label.TabIndex = 18;
            Cart7_Label.Text = "7";
            Cart7_Label.Visible = false;
            // 
            // Cart8_Label
            // 
            Cart8_Label.AutoSize = true;
            Cart8_Label.Location = new Point(446, 126);
            Cart8_Label.Name = "Cart8_Label";
            Cart8_Label.Size = new Size(17, 20);
            Cart8_Label.TabIndex = 19;
            Cart8_Label.Text = "8";
            Cart8_Label.Visible = false;
            // 
            // Cart_Stack_Label
            // 
            Cart_Stack_Label.AutoSize = true;
            Cart_Stack_Label.Location = new Point(205, 147);
            Cart_Stack_Label.Name = "Cart_Stack_Label";
            Cart_Stack_Label.Size = new Size(75, 20);
            Cart_Stack_Label.TabIndex = 20;
            Cart_Stack_Label.Text = "Cart Stack";
            Cart_Stack_Label.Visible = false;
            // 
            // Cart1
            // 
            Cart1.AutoSize = true;
            Cart1.Location = new Point(286, 150);
            Cart1.Name = "Cart1";
            Cart1.Size = new Size(18, 17);
            Cart1.TabIndex = 21;
            Cart1.UseVisualStyleBackColor = true;
            Cart1.Visible = false;
            // 
            // Cart2
            // 
            Cart2.AutoSize = true;
            Cart2.Location = new Point(307, 150);
            Cart2.Name = "Cart2";
            Cart2.Size = new Size(18, 17);
            Cart2.TabIndex = 22;
            Cart2.UseVisualStyleBackColor = true;
            Cart2.Visible = false;
            // 
            // Cart3
            // 
            Cart3.AutoSize = true;
            Cart3.Location = new Point(330, 150);
            Cart3.Name = "Cart3";
            Cart3.Size = new Size(18, 17);
            Cart3.TabIndex = 23;
            Cart3.UseVisualStyleBackColor = true;
            Cart3.Visible = false;
            // 
            // Cart4
            // 
            Cart4.AutoSize = true;
            Cart4.Location = new Point(353, 150);
            Cart4.Name = "Cart4";
            Cart4.Size = new Size(18, 17);
            Cart4.TabIndex = 24;
            Cart4.UseVisualStyleBackColor = true;
            Cart4.Visible = false;
            // 
            // Cart5
            // 
            Cart5.AutoSize = true;
            Cart5.Location = new Point(374, 150);
            Cart5.Name = "Cart5";
            Cart5.Size = new Size(18, 17);
            Cart5.TabIndex = 25;
            Cart5.UseVisualStyleBackColor = true;
            Cart5.Visible = false;
            // 
            // Cart6
            // 
            Cart6.AutoSize = true;
            Cart6.Location = new Point(398, 150);
            Cart6.Name = "Cart6";
            Cart6.Size = new Size(18, 17);
            Cart6.TabIndex = 26;
            Cart6.UseVisualStyleBackColor = true;
            Cart6.Visible = false;
            // 
            // Cart7
            // 
            Cart7.AutoSize = true;
            Cart7.Location = new Point(422, 150);
            Cart7.Name = "Cart7";
            Cart7.Size = new Size(18, 17);
            Cart7.TabIndex = 27;
            Cart7.UseVisualStyleBackColor = true;
            Cart7.Visible = false;
            // 
            // Cart8
            // 
            Cart8.AutoSize = true;
            Cart8.Location = new Point(445, 150);
            Cart8.Name = "Cart8";
            Cart8.Size = new Size(18, 17);
            Cart8.TabIndex = 28;
            Cart8.UseVisualStyleBackColor = true;
            Cart8.Visible = false;
            // 
            // OnAirLights_checkbox
            // 
            OnAirLights_checkbox.AutoSize = true;
            OnAirLights_checkbox.Location = new Point(334, 67);
            OnAirLights_checkbox.Name = "OnAirLights_checkbox";
            OnAirLights_checkbox.Size = new Size(18, 17);
            OnAirLights_checkbox.TabIndex = 30;
            OnAirLights_checkbox.UseVisualStyleBackColor = true;
            OnAirLights_checkbox.CheckedChanged += checkBox1_CheckedChanged;
            // 
            // label3
            // 
            label3.AutoSize = true;
            label3.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            label3.Location = new Point(190, 55);
            label3.Name = "label3";
            label3.Size = new Size(147, 31);
            label3.TabIndex = 29;
            label3.Text = "On Air Lights";
            // 
            // COM_options
            // 
            COM_options.AllowDrop = true;
            COM_options.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            COM_options.FormattingEnabled = true;
            COM_options.Location = new Point(354, 55);
            COM_options.Name = "COM_options";
            COM_options.Size = new Size(92, 39);
            COM_options.TabIndex = 31;
            COM_options.Visible = false;
            // 
            // Form1
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            BackColor = SystemColors.AppWorkspace;
            ClientSize = new Size(596, 194);
            Controls.Add(COM_options);
            Controls.Add(OnAirLights_checkbox);
            Controls.Add(label3);
            Controls.Add(Cart8);
            Controls.Add(Cart7);
            Controls.Add(Cart6);
            Controls.Add(Cart5);
            Controls.Add(Cart4);
            Controls.Add(Cart3);
            Controls.Add(Cart2);
            Controls.Add(Cart1);
            Controls.Add(Cart_Stack_Label);
            Controls.Add(Cart8_Label);
            Controls.Add(Cart7_Label);
            Controls.Add(Cart6_Label);
            Controls.Add(Cart5_Label);
            Controls.Add(Cart4_Label);
            Controls.Add(Cart3_Label);
            Controls.Add(Cart2_Label);
            Controls.Add(Cart1_Label);
            Controls.Add(Fader_Label);
            Controls.Add(DHD_Device);
            Controls.Add(DHD_Enabled);
            Controls.Add(Device2);
            Controls.Add(Device1);
            Controls.Add(DHD_Status);
            Controls.Add(label2);
            Controls.Add(Stop);
            Controls.Add(Start);
            Controls.Add(label1);
            Icon = (Icon)resources.GetObject("$this.Icon");
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
        private Label Fader_Label;
        private Label Cart1_Label;
        private Label Cart2_Label;
        private Label Cart3_Label;
        private Label Cart4_Label;
        private Label Cart5_Label;
        private Label Cart6_Label;
        private Label Cart7_Label;
        private Label Cart8_Label;
        private Label Cart_Stack_Label;
        private CheckBox Cart1;
        private CheckBox Cart2;
        private CheckBox Cart3;
        private CheckBox Cart4;
        private CheckBox Cart5;
        private CheckBox Cart6;
        private CheckBox Cart7;
        private CheckBox Cart8;
        private CheckBox OnAirLights_checkbox;
        private Label label3;
        private ComboBox COM_options;
    }
}
