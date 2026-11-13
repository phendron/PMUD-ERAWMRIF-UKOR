#!/bin/python3

import os
import re

def extract_model_blocks(filename):
    with open(filename, "rb") as f:
        data = f.read()

    pos = 0
    blocks_found = 0
    os.makedirs("extracted_models", exist_ok=True)

    print("=== Scanning binary for model configuration blocks ===")
    
    while True:
        idx = data.find(b"model/", pos)
        if idx == -1:
            break

        # Safely extract a short model identifier right after 'model/'
        name_slice = data[idx+6 : idx+40]
        m = re.match(rb"([a-zA-Z0-9_\-]+)", name_slice)
        if m:
            clean_name = m.group(1).decode("latin1")
        else:
            clean_name = f"unknown_{blocks_found}"

        brace_count = 0
        start_idx = -1
        end_idx = -1

        for i in range(idx, min(idx + 15000, len(data))):
            char = data[i:i+1]
            if char == b"{":
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == b"}":
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    end_idx = i + 1
                    break

        if start_idx != -1 and end_idx != -1:
            block_data = data[idx:end_idx]
            blocks_found += 1
            
            filename_out = os.path.join("extracted_models", f"{blocks_found:02d}_{clean_name}.json")
            
            # Safeguard against any unexpected path length issues
            if len(filename_out) > 240:
                filename_out = os.path.join("extracted_models", f"{blocks_found:02d}_model_block.json")

            with open(filename_out, "wb") as out_f:
                out_f.write(block_data)
                
            print(f"[+] Extracted: {filename_out} (Model: {clean_name}, Offset: {hex(idx)})")
            pos = end_idx
        else:
            pos = idx + 6

    print(f"\n[+] Extraction complete. Saved {blocks_found} blocks to 'extracted_models/' directory.")

if __name__ == "__main__":
    extract_model_blocks("S34ML04G300Bxx00@BGA63.BIN")
