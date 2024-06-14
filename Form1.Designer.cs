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
            Device1 = new ListBox();
            label1 = new Label();
            Device2 = new ListBox();
            Start = new Button();
            Stop = new Button();
            label2 = new Label();
            textBox1 = new TextBox();
            SuspendLayout();
            // 
            // Device1
            // 
            Device1.AllowDrop = true;
            Device1.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            Device1.FormattingEnabled = true;
            Device1.ItemHeight = 31;
            Device1.Location = new Point(12, 12);
            Device1.Name = "Device1";
            Device1.Size = new Size(172, 35);
            Device1.TabIndex = 0;
            Device1.SelectedIndexChanged += Device1_SelectedIndexChanged;
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
            // Device2
            // 
            Device2.AllowDrop = true;
            Device2.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            Device2.FormattingEnabled = true;
            Device2.ItemHeight = 31;
            Device2.Location = new Point(274, 12);
            Device2.Name = "Device2";
            Device2.Size = new Size(172, 35);
            Device2.TabIndex = 2;
            // 
            // Start
            // 
            Start.Location = new Point(576, 12);
            Start.Name = "Start";
            Start.Size = new Size(94, 35);
            Start.TabIndex = 3;
            Start.Text = "Start";
            Start.UseVisualStyleBackColor = true;
            // 
            // Stop
            // 
            Stop.Location = new Point(576, 53);
            Stop.Name = "Stop";
            Stop.Size = new Size(94, 35);
            Stop.TabIndex = 4;
            Stop.Text = "Stop";
            Stop.UseVisualStyleBackColor = true;
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
            // textBox1
            // 
            textBox1.Font = new Font("Segoe UI", 13.8F, FontStyle.Regular, GraphicsUnit.Point, 0);
            textBox1.Location = new Point(80, 53);
            textBox1.Name = "textBox1";
            textBox1.ReadOnly = true;
            textBox1.Size = new Size(172, 38);
            textBox1.TabIndex = 6;
            // 
            // Form1
            // 
            AutoScaleDimensions = new SizeF(8F, 20F);
            AutoScaleMode = AutoScaleMode.Font;
            BackColor = SystemColors.AppWorkspace;
            ClientSize = new Size(682, 127);
            Controls.Add(textBox1);
            Controls.Add(label2);
            Controls.Add(Stop);
            Controls.Add(Start);
            Controls.Add(Device2);
            Controls.Add(label1);
            Controls.Add(Device1);
            Name = "Form1";
            Text = "Form1";
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private ListBox Device1;
        private Label label1;
        private ListBox Device2;
        private Button Start;
        private Button Stop;
        private Label label2;
        private TextBox textBox1;
    }
}
