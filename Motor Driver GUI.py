import tkinter as tk
import serial
import sys

# === Config ===
USE_SERIAL = False  # Set to True later
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

ser = None
if USE_SERIAL:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except:
        print("Serial not available")
        USE_SERIAL = False

def send(cmd):
    if USE_SERIAL and ser:
        ser.write(cmd.encode())
    print(f"[Sent] {cmd}")

# Create main window
root = tk.Tk()
root.title("RC-Style Motor Control")
root.geometry("220x220")

# Make buttons respond to press/release
btn_up = tk.Button(root, text="↑ UP", width=10, height=2)
btn_down = tk.Button(root, text="↓ DOWN", width=10, height=2)
btn_left = tk.Button(root, text="← LEFT", width=10, height=2)
btn_right = tk.Button(root, text="→ RIGHT", width=10, height=2)

# Bind events
btn_up.bind("<ButtonPress>", lambda e: send('U'))
btn_up.bind("<ButtonRelease>", lambda e: send('S'))

btn_down.bind("<ButtonPress>", lambda e: send('D'))
btn_down.bind("<ButtonRelease>", lambda e: send('S'))

btn_left.bind("<ButtonPress>", lambda e: send('L'))
btn_left.bind("<ButtonRelease>", lambda e: send('S'))

btn_right.bind("<ButtonRelease>", lambda e: send('S'))

# Layout
btn_up.grid(row=0, column=1, padx=5, pady=5)
btn_left.grid(row=1, column=0, padx=5, pady=5)
btn_right.grid(row=1, column=2, padx=5, pady=5)
btn_down.grid(row=2, column=1, padx=5, pady=5)

# Handle window close
def on_close():
    if ser: ser.close()
    root.destroy()
root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()