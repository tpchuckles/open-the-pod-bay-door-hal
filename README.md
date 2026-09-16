# Open the pod-bay door, Hal
This is just a quick python script for retrieving pdfs off sci-hub en masse. Claude/Codex/OpenResearch are happy to run lit review for you, or parse out references from PDFs (and even follow the reference tree back a ways), but may be limited in their "ability" to actually retrieve all PDFs. Instead, ask for a list of DOIs. This script (written by Codex) then reads that list, and uses pyautogui to retrieve pdfs from sci-hub via the browser. 

```
python3 open_pod_bay.py path/to/doi/list.txt
```
