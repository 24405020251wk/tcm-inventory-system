Option Explicit
' Double-click this file to start the TCM Inventory server in the background.
' No console window will stay open, and closing it does not stop the server.
Dim fso, shell, baseDir, target
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
target = baseDir & "\serve.bat"

If Not fso.FileExists(target) Then
    MsgBox "serve.bat was not found in:" & vbCrLf & baseDir, 16, "TCM Inventory"
    WScript.Quit 1
End If

If Not fso.FileExists(baseDir & "\.venv\Scripts\python.exe") Then
    MsgBox "Python virtual environment not found:" & vbCrLf & baseDir & "\.venv", 16, "TCM Inventory"
    WScript.Quit 1
End If

shell.CurrentDirectory = baseDir
' 0 = hidden window, False = do not wait
shell.Run """" & target & """", 0, False
