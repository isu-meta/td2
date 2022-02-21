from argparse import ArgumentParser
from pathlib import Path

from td2.data.departments import DEPARTMENTS
from td2.data.tds import TDS
from td2 import pdf
from td2 import xml
from td2 import proquest
from td2.search import search_tds_metadata


def main():
    parser = ArgumentParser()
    parser.add_argument("in_dir")
    parser.add_argument("outfile")
    parser.add_argument("collection")
    parser.add_argument("doi_number", nargs="?", default=0, type=int)
    parser.add_argument("--unzip-to", nargs="?")
    parser.add_argument("--skip-unzip", action="store_true")
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    outfile = Path(args.outfile)
    collection = args.collection
    doi_number = args.doi_number

    if collection == "etd":
        if args.unzip_to:
            out_dir = Path(args.unzip_to)
        else:
            out_dir = in_dir

        if not args.skip_unzip:
            print("Unzipping ProQuest files.")
            proquest.unzip_files(in_dir, out_dir)

        print("Gathering metadata from ProQuest XML.")
        xml_md = [proquest.get_metadata(x) for x in out_dir.glob("*.xml")]
        for i, p in enumerate(out_dir.glob("*.pdf")):
            xml_md[i]["file_name"] = p.name
            xml_md[i]["major"] = pdf.get_major_from_pdf(p)
        out_xml, doi_xml = xml.build_etd_xml(xml_md, doi_number)
    elif collection == "rtd":
        tds_titles = [t["title"] for t in TDS]

        print("Gathering PDF metadata.")
        pdf_md = [pdf.get_md_from_pdf(p) for p in in_dir.glob("*.pdf")]

        print("Matching PDF metadata with MARC metadata.")
        marc_md = [search_tds_metadata(p, TDS, tds_titles) for p in pdf_md]

        xml_md = xml.get_xml_md(pdf_md, marc_md, DEPARTMENTS, [])
        out_xml, doi_xml = xml.build_rtd_xml(xml_md, doi_number)

    print("Saving XML files.")
    with open(outfile, "w", encoding="utf-8") as fh:
        fh.write(out_xml)

    with open(f"doi-{outfile}", "w", encoding="utf-8") as fh:
        fh.write(doi_xml)

    print("All done! Thanks!")


if __name__ == "__main__":
    main()
