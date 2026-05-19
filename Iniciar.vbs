Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strFolder = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Set env variable so installer knows not to launch the app
objShell.Environment("PROCESS")("EXTRACTOR_VBS_LAUNCH") = "1"

' Run installer and wait
objShell.Run "python """ & strFolder & "\installer.py""", 0, True

' Then launch app
objShell.Run "python """ & strFolder & "\extractor_ui.py""", 0, False
