#!/usr/bin/env python3
import sys
import zipfile
import xml.etree.ElementTree as ET
import argparse

def extract_paragraphs(docx_path):
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    }
    paragraphs = []
    try:
        with zipfile.ZipFile(docx_path) as z:
            xml_content = z.read('word/document.xml')
        root = ET.fromstring(xml_content)
        
        for p in root.findall('.//w:p', namespaces):
            p_text = []
            for t in p.findall('.//w:t', namespaces):
                if t.text:
                    p_text.append(t.text)
            text_str = "".join(p_text).strip()
            if text_str:
                paragraphs.append(text_str)
    except Exception as e:
        sys.stderr.write(f"Error reading docx: {e}\n")
        sys.exit(1)
    return paragraphs

def main():
    parser = argparse.ArgumentParser(description="Search text within a .docx file.")
    parser.add_argument("--file", "-f", required=True, help="Path to the .docx file")
    parser.add_argument("--query", "-q", required=True, help="Search term/query")
    parser.add_argument("--context", "-c", type=int, default=1, help="Number of surrounding paragraphs to show")
    args = parser.parse_args()

    paragraphs = extract_paragraphs(args.file)
    query_lower = args.query.lower()
    
    matches_found = 0
    results = []
    
    for idx, p in enumerate(paragraphs):
        if query_lower in p.lower():
            matches_found += 1
            start = max(0, idx - args.context)
            end = min(len(paragraphs), idx + args.context + 1)
            
            match_block = []
            for c_idx in range(start, end):
                prefix = ">>> " if c_idx == idx else "    "
                match_block.append(f"[{c_idx}] {prefix}{paragraphs[c_idx]}")
            
            results.append("\n".join(match_block))
            if matches_found >= 15:
                results.append("\n... (showing first 15 matches, more exist) ...")
                break
                
    if not results:
        print(f"No matches found for query: '{args.query}'")
    else:
        print(f"Found {matches_found} matches in '{args.file}':\n")
        print("\n" + "="*80 + "\n\n".join(results) + "\n" + "="*80)

if __name__ == "__main__":
    main()
