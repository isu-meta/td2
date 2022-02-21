from pathlib import Path
import re

from nameparser import HumanName
from pymarc import MARCReader

import td2.config as config
from td2.regex import (
    degree_abbr_to_full,
    RegExReplacer,
)


def get_title(m245):
    """Extract and clean title text from MARC 245 field.

    Parameters
    ----------
        m245 : pymarc.field.Field

    Returns
    -------
        str
    """
    try:
        a = m245["a"].rstrip("/. ").replace(" :", ": ")
        b = m245["b"].rstrip(" /.") if m245["b"] is not None else ""
        return f"{a}{b}"
    except AttributeError:
        return ""


def format_local_id(l_id):
    return (
        l_id.replace(" ", "-")
        .replace(" ", "-")
        .replace(".", "-")
        .replace("$b", "-")
        .replace("$a", "-")
        .replace("--", "-")
    )


def get_local_id(m090, m099):

    local_id = ""
    # Identifier is inconsistent across records, we need to check in two locations
    # split record and reconcile with PDF filename convention
    try:
        local_id = str(m090).split("$a", 1)[1]
        local_id = format_local_id(local_id)
    except IndexError:
        try:
            local_id = str(m099).split("$a", 1)[1]
            local_id = format_local_id(local_id)
        except IndexError:
            local_id = ""

    return local_id


def get_oclc_number(m035s):
    """Returns the OCLC number for a record from a list
    of 035 fields. If no OCLC number is found, returns
    None.

    Parameters
    ----------
        m035s : list of pymarc.field.Field

    Returns
    -------
        str or None
    """
    no_p = re.compile(r"\d+")
    for no in m035s:
        if "OCoLC" in no["a"]:
            return no_p.search(no["a"]).group()

    return ""


def get_name(m100):
    try:
        name = HumanName(m100["a"].strip(".,"))

        return (name.last, name.first.strip("."), name.middle, name.suffix)
    except TypeError:
        return ("", "", "", "")


def get_degree(m502):
    abbr_to_degree = RegExReplacer(degree_abbr_to_full)
    try:
        # Ideally, we'll have something like
        # 'Thesis (M.S.)--Iowa State College, 1952' so we can get
        # 'M.S.' and convert it to the proper dgree'
        degree_name = abbr_to_degree.replace(m502["a"].split("(")[1].split(")")[0])
    except IndexError:
        # Sometimes, we'll have something like this, though,
        # 'Thesis---Iowa State College, 1952' and must abandon all
        # hope.
        degree_name = ""

    return degree_name


def get_description(m5XXs):
    description = " ".join([m["a"] for m in m5XXs])
    return description


def get_institution(m502):
    # split_p = re.compile(r"-+|:|\)|,")
    strip_str = "0123456789 .,"
    institution = ""
    try:
        # institution = split_p.split(m502["a"])[1].strip(r" \d.,")
        institution = m502["a"].split("--")[1]
    except IndexError:
        try:
            institution = m502["a"].split("-", 1)[1]
        except IndexError:
            try:
                institution = m502["a"].split(") ")[1]
            except IndexError:
                try:
                    institution = m502["a"].split(":")[1]
                except IndexError:
                    try:
                        institution = m502["a"].split(",")[1]
                    except IndexError as e:
                        print(
                            f"Institution. Encountered {e} when processing {m502['a']}."
                        )

    institution = institution.strip(strip_str)
    return institution


def get_keywords(subjects):
    keywords = [
        "--".join([sf.rstrip(".") for sf in sub.subfields if len(sf) > 1])
        for sub in subjects
    ]

    return keywords


def get_md_from_record(record):
    md = {}

    md["title"] = get_title(record["245"])
    try:
        md["publication_date"] = (
            record["260"]["c"].strip(".") if record["260"]["c"] is not None else ""
        )
    except TypeError:
        md["publication_date"] = ""

    md["institution"] = get_institution(record["502"])
    md["lname"], md["fname"], md["mname"], md["suffix"] = get_name(record["100"])
    md["degree"] = get_degree(record["502"])
    md["oclc"] = get_oclc_number(record.get_fields("035"))
    md["keywords"] = get_keywords(record.subjects())
    md["abstract"] = get_description(
        record.get_fields("520")
        if record.get_fields("520") != []
        else record.get_fields("500", "502", "504")
    )

    return md


def load_marc_record_metadata(md_file, filter_list=None):
    if md_file.suffix == "mrc":
        md_list = load_metadata_from_marc_file(md_file, filter_list)
    else:
        md_list = load_metadata_from_quick_ref_file(md_file, filter_list)

    return sorted(md_list, key=lambda m: m["title"])


def load_metadata_from_marc_file(marc_file, filter_list=None):
    with open(marc_file, "rb") as fh:
        reader = MARCReader(fh, to_unicode=True, force_utf8=True)
        md_list = []
        for record in reader:
            md = {}

            local_id = get_local_id(record["090"], record["099"])
            if filter_list is not None:
                if local_id is not None:
                    if local_id in filter_list:
                        md = get_md_from_record(record)
                        md["url"] = f"{config.UPLOAD_URL}"  # not fully implemented
            else:
                md = get_md_from_record(record)

            md["local_id"] = local_id

            md_list.append(md)

        return md_list


def build_quick_ref_file(marc_file, out_file):
    """Take a .mrc file and return a TSV with only the fields we need for
    BePress already formatted. This should be faster than working through
    full MARC records."""
    md = load_metadata_from_marc_file(marc_file)
    with open(out_file, "w", encoding="utf-8") as fh:
        for m in md:
            fh.write(
                f"{m['local_id']}\t{m['oclc']}\t{m['title']}\t{m['publication_date']}\t{m['institution']}\t{m['lname']}\t{m['fname']}\t{m['mname']}\t{m['suffix']}\t{m['degree']}\t{'; '.join(m['keywords'])}\t{m['abstract']}\n"
            )


def parse_quick_ref_row(row):
    keys = (
        "local_id",
        "oclc",
        "title",
        "publication_date",
        "institution",
        "lname",
        "fname",
        "mname",
        "suffix",
        "degree",
        "keywords",
        "abstract",
    )
    md = dict(zip(keys, row))
    md["keywords"] = md["keywords"].split("; ")

    return md


def load_metadata_from_quick_ref_file(quick_ref_file, filter_list=None):
    md = []
    with open(quick_ref_file, "r", encoding="utf-8") as fh:
        if filter_list is not None:
            for line in fh:
                row = line.split("\t")
                if row[0] in filter_list:
                    md.append(parse_quick_ref_row(row))
        else:
            for line in fh:
                row = line.split("\t")
                md.append(parse_quick_ref_row(row))

    return md


def make_titles_list(marc_md):
    return [m["title"] for m in marc_md]
