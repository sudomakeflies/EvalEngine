import os
from dotenv import load_dotenv

load_dotenv()

def create_task(description, due_date=None):
    """
    Agrega una tarea al archivo de To Do (tareas.txt).

    Args:
        description: La descripción de la tarea.
        due_date: La fecha límite (opcional) en formato YYYY-MM-DD.
    """
    try:
        folder_path = os.getenv('DOCUMENTS_FOLDER')
        filepath = os.path.join(folder_path, "resultados", "tareas.txt")
        with open(filepath, "a", encoding="utf-8") as f:
            line = ""
            if due_date:
                line += f"{due_date};"
            line += f"{description};Pendiente\n"
            f.write(line)

    except Exception as e:
        print(f"Error al crear la tarea: {e}")

def mark_task_as_complete(task_index):
    """
    Marca una tarea como completa en el archivo de To Do.

    Args:
        task_index: El índice de la tarea a completar (comenzando desde 0).
    """
    try:
        folder_path = os.getenv('DOCUMENTS_FOLDER')
        filepath = os.path.join(folder_path, "resultados", "tareas.txt")
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if 0 <= task_index < len(lines):
            parts = lines[task_index].strip().split(";")
            if len(parts) == 3:
                parts[2] = "Completado"
                lines[task_index] = ";".join(parts) + "\n"

                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            else:
                print("Formato de línea de tarea incorrecto.")
        else:
            print("Índice de tarea fuera de rango.")

    except Exception as e:
        print(f"Error al marcar la tarea como completa: {e}")