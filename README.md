# Open the pod-bay door, Hal
This is just a quick python script for retrieving pdfs off sci-hub or other journal sites en masse. Claude/Codex/OpenResearch are happy to run lit review for you, or parse out references from PDFs (and even follow the reference tree back a ways), but may be limited in their "ability" to actually retrieve all PDFs. Instead, ask for a list of DOIs. This script (written by Codex) then reads that list, and uses pyautogui to retrieve pdfs via the browser. You'll need to supply your own screenshots of the buttons you want clicked (e.g., the pdf download button). 

```
python3 open_pod_bay.py path/to/doi/list.txt https://doi.org/
```
