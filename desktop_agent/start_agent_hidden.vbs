Set WshShell = CreateObject("WScript.Shell") 
WshShell.Run "cmd /c cd /d ""D:\AI_Model_Renata\Document-management\Group\V2\DocuVault\desktop_agent\"" && python agent.py", 0, False 
