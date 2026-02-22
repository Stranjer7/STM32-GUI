"""
Simple LED Blink Control GUI for STM32F105
UART1 on PB6(TX), PB7(RX) - LED on PB2
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime

class LEDControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("STM32 LED Blink Control")
        self.root.geometry("600x400")
        
        # Serial communication
        self.serial_port = None
        self.connected = False
        self.current_blink = 500  # Default 500ms
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(conn_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        
        self.port_combo = ttk.Combobox(conn_frame, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="LED Control", padding="10")
        control_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Blink speed control
        ttk.Label(control_frame, text="Blink Speed (ms):").pack(pady=5)
        
        self.speed_slider = tk.Scale(control_frame, from_=50, to=2000, 
                                      orient=tk.HORIZONTAL, length=400,
                                      resolution=10)
        self.speed_slider.set(500)
        self.speed_slider.pack(pady=5)
        
        # Speed value label
        self.speed_label = ttk.Label(control_frame, text="500 ms")
        self.speed_label.pack()
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Set Speed", 
                  command=self.set_blink_speed).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Get Current Speed", 
                  command=self.get_blink_speed).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test LED ON", 
                  command=lambda: self.send_command("BLINK=50")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test LED OFF", 
                  command=lambda: self.send_command("BLINK=2000")).pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Communication Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8,
                                                  bg='black', fg='lime',
                                                  font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(log_frame, text="Clear Log", 
                  command=self.clear_log).pack(pady=2)
        
        # Disable controls initially
        self.set_controls_enabled(False)
    
    def refresh_ports(self):
        """Refresh available COM ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports and not self.port_combo.get():
            self.port_combo.set(ports[0])
        
        if not self.connected:
            self.root.after(2000, self.refresh_ports)
    
    def toggle_connection(self):
        """Connect or disconnect from STM32"""
        if not self.connected:
            port = self.port_combo.get()
            if port:
                self.log_message(f"Connecting to {port}...")
                try:
                    self.serial_port = serial.Serial(
                        port=port,
                        baudrate=115200,
                        timeout=1
                    )
                    self.connected = True
                    self.connect_btn.config(text="Disconnect")
                    self.status_label.config(text="Connected", foreground="green")
                    self.set_controls_enabled(True)
                    self.log_message("✅ Connected successfully")
                    
                    # Start reading thread
                    self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
                    self.read_thread.start()
                    
                    # Send init command
                    self.send_command("INIT")
                    
                except Exception as e:
                    self.log_message(f"❌ Connection failed: {str(e)}")
        else:
            if self.serial_port:
                self.serial_port.close()
            self.connected = False
            self.connect_btn.config(text="Connect")
            self.status_label.config(text="Disconnected", foreground="red")
            self.set_controls_enabled(False)
            self.log_message("Disconnected")
            self.refresh_ports()
    
    def set_controls_enabled(self, enabled):
        """Enable or disable controls"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.speed_slider.config(state=state)
    
    def set_blink_speed(self):
        """Send blink speed command"""
        speed = int(self.speed_slider.get())
        self.speed_label.config(text=f"{speed} ms")
        self.send_command(f"BLINK={speed}")
    
    def get_blink_speed(self):
        """Request current blink speed"""
        self.send_command("GET")
    
    def send_command(self, command):
        """Send command to STM32"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(f"{command}\n".encode())
                self.log_message(f"📤 TX: {command}")
            except Exception as e:
                self.log_message(f"❌ TX Error: {str(e)}")
    
    def read_serial(self):
        """Read serial data in background"""
        while self.connected and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode().strip()
                    if line:
                        self.root.after(0, self.handle_serial_data, line)
            except Exception as e:
                self.root.after(0, self.log_message, f"❌ RX Error: {str(e)}")
            time.sleep(0.01)
    
    def handle_serial_data(self, data):
        """Handle incoming data"""
        self.log_message(f"📥 RX: {data}")
        
        # Parse blink speed response
        if data.startswith("BLINK:"):
            try:
                speed = int(data.split(":")[1])
                self.current_blink = speed
                self.speed_slider.set(speed)
                self.speed_label.config(text=f"{speed} ms")
            except:
                pass
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear log window"""
        self.log_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = LEDControlGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()