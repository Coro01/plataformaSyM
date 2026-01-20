Dim WShell
Set WShell = CreateObject("WScript.Shell")

' ----------------------------------------------------
' CONFIGURACIÓN CRÍTICA
' ----------------------------------------------------
' 🚨 1. RUTA ABSOLUTA AL DIRECTORIO DEL PROYECTO (Donde está manage.py)
projectPath = "C:\Users\LABTECH\Documents\Proyectos"

' 🚨 2. RUTA ABSOLUTA AL EJECUTABLE PYTHON DENTRO DE TU VENV
' Esto garantiza que use el Python correcto y no el del sistema.
pythonExePath = projectPath & "\venv\Scripts\python.exe"

' ----------------------------------------------------
' COMANDO DE EJECUCIÓN
' ----------------------------------------------------
' El comando completo que se ejecutaría en la CMD:
' C:\Users\LABTECH\Documents\Proyectos\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
command = Chr(34) & pythonExePath & Chr(34) & " manage.py runserver 127.0.0.1:8000"

' ----------------------------------------------------
' INICIAR PROCESO EN MODO SILENCIOSO
' ----------------------------------------------------
' WShell.Run (comando, estilo_ventana, esperar_hasta_terminar)
' Estilo_ventana = 0 (vbHide) oculta la ventana
WShell.Run command, 0, False

Set WShell = Nothing
' Mensaje opcional (solo se vería si se ejecuta el VBScript desde el CMD)
WScript.Quit
