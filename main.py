import tkinter as tk
from gui.app import AutoRodGUI

if __name__ == "__main__":
    # Punto de entrada de AutoRod Pro
    root = tk.Tk()
    app = AutoRodGUI(root)
    root.mainloop()