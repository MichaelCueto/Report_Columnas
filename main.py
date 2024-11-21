import tkinter as tk
from tkinter import filedialog, messagebox

def start_dash(folder_path):
    # Importa y ejecuta el módulo Dash aquí
    import app
    app.run_app(folder_path)

def select_folder_and_start():
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal de Tkinter
    folder_path = filedialog.askdirectory(title="Seleccione la carpeta 'columnas_actualizado'")
    
    if folder_path:
        root.destroy()  # Cierra la ventana de Tkinter
        start_dash(folder_path)  # Inicia la aplicación Dash
    else:
        messagebox.showerror("Error", "Debe seleccionar una carpeta para continuar")
        root.destroy()  # Asegúrate de que la ventana de Tkinter se cierre correctamente

if __name__ == '__main__':
    select_folder_and_start()



