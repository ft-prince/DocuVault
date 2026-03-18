' DocuVault Desktop Agent Launcher
' Double-click this file to start the agent.
' Works on any PC — no hardcoded paths.

Dim objFSO, strDir, WshShell, strCmd

Set objFSO  = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Try pythonw first (no console window), fall back to python
On Error Resume Next
strCmd = "pythonw """ & strDir & "\agent.py"""
WshShell.Run strCmd, 0, False
If Err.Number <> 0 Then
    Err.Clear
    strCmd = "python """ & strDir & "\agent.py"""
    WshShell.Run strCmd, 0, False
End If
On Error GoTo 0
