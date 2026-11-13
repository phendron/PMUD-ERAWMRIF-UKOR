#!/bin/python3

import os

def scan_models():
    folder = "extracted_models"
    if not os.path.exists(folder):
        print("[-] 'extracted_models' directory not found.")
        return

    print(f"{'Filename':<30} | {'Model':<10} | {'Display Name':<25} | {'Size':<6} | | {'Resolution':<6} {'Panel':<10} | {'PID'}-")
    print("-" * 105)

    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".json"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r", encoding="latin1") as f:
                content = f.read()
                
            model = "N/A"
            display_name = "N/A"
            pid = "N/A"
            size = "N/A"
            panel = "N/A"
            
            if '"model":' in content:
                try:
                    model = content.split('"model":')[1].split(',')[0].strip().strip('"')
                except:
                    pass
                    
            if '"display_name":' in content:
                try:
                    display_name = content.split('"display_name":')[1].split(',')[0].strip().strip('"')
                except:
                    pass
                    
            if '"PID":' in content:
                try:
                    pid = content.split('"PID":')[1].split(',')[0].strip().strip('"')
                except:
                    pass

            if '"size":' in content:
                try:
                    size = content.split('"size":')[1].split(',')[0].strip() + '"'
                except:
                    pass
                    
            if '"resolution":' in content:
                try:
                    size = content.split('"resolution":')[1].split(',')[0].strip() + '"'
                except:
                    pass

            if 'panel_' in content:
                try:
                    idx = content.find('"default": "panel/panel_')
                    if idx != -1:
                        sub = content[idx + len('"default": "panel/panel_'):]
                        panel = "panel_" + sub.split('"')[0].strip()
                except:
                    pass

            print(f"{filename:<30} | {model:<10} | {display_name:<25} | {size:<6} | {panel:<10} | {pid}")

if __name__ == "__main__":
    scan_models()
