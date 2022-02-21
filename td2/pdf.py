from os.path import basename
import re

from fuzzywuzzy import fuzz
from nameparser import HumanName
from PyPDF2 import PdfFileReader


def get_author_name(name_str):
    name = HumanName(name_str)
    return (name.last, name.first, name.middle, name.suffix)


def parse_keywords(keywords):
    """Civil Engineering (Civil Engineering Materials), Iowa State University Theses and Dissertations, 2002, Master of Science
    or
    Community and Regional Planning; Public Administration, Iowa State University Theses and Dissertations, 2005, Master Community and Regional Planning, Master of Public Administration
    """
    try:
        kws = [k.strip() for k in keywords.split(",")]
    except TypeError:
        kws = [k.strip() for k in keywords.decode("utf-8").split(",")]

    how_many_keywords = len(kws)

    # Every once in a while, keywords will be separated by semicolons rather than commas.
    if how_many_keywords == 1:
        if kws[0] != "":
            kws = kws[0].split(";")
            how_many_keywords = len(kws)
        # Every once in a while, nothing will be entered
        else:
            return ("", "", "")

    collection_name = "Iowa State University Theses and Dissertations"

    # Sometimes something might be misspelled in the collection name
    # ('Stata' instead of 'State', for example), which breaks kws.index().
    # In such cases we'll have to look for the string that most closely
    # resembles collection_name.
    try:
        collection_name_index = kws.index(collection_name)
    except ValueError:
        collection_name_index = [
            i for i, k in enumerate(kws) if fuzz.ratio(collection_name, k) > 50
        ][0]

    # We need to handle majors with commas in their name, since values
    # in the PDF keyword field are comma seperated., For example:
    # Molecular, Cellular, and Developmental Biology, Iowa State University Theses and Dissertations, 2006, Master of Science.
    # "Iowa State University Theses and Dissertations" should always be the
    # second item in the list unless the major's been ommitted. If it
    # comes later in the list, most likely we've encountered a major
    # that shouldn't have been split. Piece the major back
    # together and move along.
    if collection_name_index > 1:
        kws = [", ".join(kws[:collection_name_index]), *kws[collection_name_index:]]

    how_many_keywords = len(kws)
    if how_many_keywords == 4:
        major, _, year, degree = kws
    elif how_many_keywords == 5:
        major, _, year, degree1, degree2 = kws
        degree = "; ".join([degree1, degree2])
    elif how_many_keywords == 3:
        _, year, degree = kws
        major = ""
    elif how_many_keywords == 2:
        major, _ = kws
        year, degree = ("", "")

    return (major, year, degree)


def get_md_from_pdf(pdf_path):
    print(pdf_path)
    pdf = PdfFileReader(open(pdf_path, "rb"))
    pdf_md = pdf.getDocumentInfo()
    md = {}

    md["title"] = pdf_md.get("/Title", "")
    md["major"], md["publication_date"], md["degree"] = parse_keywords(
        pdf_md.get("/Keywords", "")
    )
    md["institution"] = "Iowa State University"
    md["lname"], md["fname"], md["mname"], md["suffix"] = get_author_name(
        pdf_md.get("/Author", "")
    )
    md["file_size"] = f"{pdf.getNumPages()} pages"
    md["file_name"] = basename(pdf_path)

    return md


def get_major_from_pdf(pdf_path):
    pdf = PdfFileReader(open(pdf_path, "rb"))
    cover_page = pdf.getPage(0).extractText().replace("\n", " ")
    major_p = re.compile(
        r"(Co-)?[Mm]?ajors? *: *(.*)? *[Pp]rogram *of *[Ss]tudy *[Cc]ommittee:"
    )

    try:
        matches = major_p.search(cover_page).groups()
    except AttributeError:
        return enter_major_manually(pdf_path)

    try:
        major = matches[-1].strip()
        # Remove extra spaces
        major = " ".join(major.split())
        # Add spaces for muck like ElectricalEngineering
        major = " ".join(re.findall(r"[A-Z][^A-Z]*", major))

        return major

    except IndexError:
        return enter_major_manually(pdf_path)


def enter_major_manually(pdf_path):
    print(f"Unable to find major for {pdf_path}.")
    major = input("Please enter the major or hit return to skip: ")

    return major
