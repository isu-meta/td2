from argparse import ArgumentParser
from pathlib import Path

parser = ArgumentParser()
parser.add_argument("xml_file")
parser.add_argument("first_id")
args = parser.parse_args()

id_num = int(args.first_id)
xml_file = Path(args.xml_file)
base_url = "https://lib.dr.iastate.edu/"
etd_url = f"{base_url}etd/"
rtd_url = f"{base_url}rtd/"

with open(xml_file, "r", encoding="utf-8") as fh:
    lines = list(fh)

for i, l in enumerate(lines):
    print(id_num)
    if etd_url in l:
        lines[i] = l.replace(etd_url, etd_url + str(id_num))
        print(lines[i])
        id_num += 1
    elif rtd_url in l:
        lines[i] = l.replace(rtd_url, rtd_url + str(id_num))
        id_num += 1

with open(f"updated-{xml_file.name}", "w", encoding="utf-8") as fh:
    for l in lines:
        fh.write(l)