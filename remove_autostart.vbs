Option Explicit
' Double-click to cancel the automatic startup.
Dim fso, shell, startupDir, lnkPath
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

startupDir = shell.SpecialFolders("Startup")
lnkPath = startupDir & "\TCMInventoryServer.lnk"

If fso.FileExists(lnkPath) Then
    fso.DeleteFile lnkPath, True
    MsgBox "Autostart removed.", 64, "TCM Inventory"
Else
    MsgBox "Autostart is not installed.", 48, "TCM Inventory"
End If
