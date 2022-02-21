from argparse import ArgumentParser
import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from doiowa.md import CrossrefXML, Depositor, ItemMetadata
from fuzzywuzzy import fuzz
from lxml import etree

from td2.regex import major_to_department, RegExReplacer

major_to_dept = RegExReplacer(major_to_department)


def add_id_number_to_doi_xml():
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
        if etd_url in l:
            lines[i] = l.replace(etd_url, etd_url + str(id_num))
            id_num += 1
        elif rtd_url in l:
            lines[i] = l.replace(rtd_url, rtd_url + str(id_num))
            id_num += 1

    with open(f"updated-{xml_file.name}", "w", encoding="utf-8") as fh:
        for l in lines:
            fh.write(l)


def build_full_name(name_parts):
    return f"{name_parts[0]} {name_parts[1] + ' ' if name_parts[1] != '' else ''}{name_parts[2]}{', ' + name_parts[3] if name_parts[3] != '' else ''}"


def get_department(major: str, department_list: list) -> str or list:
    # If the major matches the name of the department, everything's done and
    # we return the department name.
    if major not in department_list:
        # If the major doesn't match the department, we check if its in the list
        # of majors that have been matched to their department.
        department = major_to_dept.replace(major)
        if department == major:
            # If the major is not yet mapped to a department, we provide a list
            # of the top five closest matches, allowing the user to select the
            # appropriate match or enter the full or partial department name
            # themself. If no match is found, we keep calling this function
            # until one is.
            top_five = [
                (i, o[1])
                for i, o in enumerate(
                    reversed(
                        sorted([(fuzz.ratio(major, d), d) for d in department_list])
                    )
                )
            ][:5]
            print("\n-------------------------\n")
            print(f"{major} does not match any department names in Digital Commons.")
            print("\n-------------------------\n")
            for o in top_five:
                print(f"{o[0] + 1}. {o[1]}\n")
            response = input(
                "Please select an option from the list above by number or enter a department name: "
            )

            try:
                choice = int(response)
                if 0 < choice < 6:
                    department = top_five[choice - 1][1]
                else:
                    print(
                        "Please select one of the options provided or type department name.\n"
                    )
                    department = get_department(major, department_list)
            except ValueError:
                if response in department_list:
                    department = response
                else:
                    department = get_department(response, department_list)
    else:
        department = major

    return department


def get_xml_md(
    pdf_md: dict, marc_md: list, department_list: list, discipline_list: list
) -> list:
    xml_md = []
    for p, m in zip(pdf_md, marc_md):
        print(f"Setting up XML metadata for {p['title']}")
        md = {**p, **m}
        md["department"] = get_department(md["major"], department_list)
        # md["discipline"] = get_discipline(md["major"], discipline_list)
        xml_md.append(md)

    return xml_md


def get_discipline(
    major: str or list, discipline_list: list, return_all: bool = False
) -> str or list:
    print(f"Get Discipline: {major}")
    # Get rid of emphasis or specialization, so we're just matching the base
    # major.
    major = major.split("(")[0].strip()
    ratios = sorted([(fuzz.ratio(major, d), d) for d in discipline_list])

    if return_all:
        return ratios
    
    return ratios[-1][1]


def get_kind(degree: str) -> str:
    return "dissertation" if degree == "Doctor of Philosophy" else "thesis"


def build_etd_xml(etds: list, doi_counter: int) -> tuple:
    head = """<?xml version='1.0' encoding='UTF-8'?>
<documents xmlns:str="http://www.metaphoricalweb.org/xmlns/string-utilities" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
    tail = """</documents>"""
    docs = []
    doi_md = []

    doi_base = f"https://doi.org/10.31274/etd-{datetime.date.today().strftime('%Y%m%d')}-"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    crossref_md = CrossrefXML()
    depositor = Depositor(
        doi_batch_id=timestamp,
        timestamp=timestamp
    )
    crossref_md.insert_depositor(depositor.to_xml())

    for e in etds:
        doi = f"{doi_base}{doi_counter}"
        e["kind"] = get_kind(e["degree"])
        #print(e)
        rights_holder = build_full_name((e["fname"], e["mname"], e["lname"], e["suffix"]))
        advisor1 = build_full_name((e["advisor1"]["fname"], e["advisor1"]["mname"], e["advisor1"]["lname"], e["advisor1"]["suffix"]))
        doc = f"""    <document>
        <title>{escape(e["title"])}</title>
        <publication-date>{e["publication_date"]}</publication-date>
        <publication_date_date_format>YYYY-MM-DD</publication_date_date_format>
        <authors>
            <author xsi:type="individual">
                <email/>
                <institution>Iowa State University</institution>
                <lname>{e["lname"]}</lname>
                <fname>{e["fname"]}</fname>
                <mname>{e["mname"]}</mname>
                <suffix>{e["suffix"]}</suffix>
            </author>
        </authors>
        <disciplines></disciplines>
        <keywords>
            {"".join([f"<keyword>{escape(k.strip())}</keyword>" for k in e["keywords"]])}
        </keywords>
        <abstract>{"".join([f"<p>{escape(a.strip())}</p>" for a in e["abstract"]])}</abstract>
        <fulltext-url>https://behost.lib.iastate.edu/DR/{e["file_name"]}</fulltext-url>
        <document-type>{e["kind"]}</document-type>
        <degree_name>{e["degree"]}</degree_name>
        <department>{e["department"]}</department>
        <abstract_format>html</abstract_format>
        <fields>
            <field name="language" type="string">
                <value>en</value>
            </field>
            <field name="provenance" type="string">
                <value>Received from ProQuest</value>
            </field>
            <field name="copyright_date" type="string">
                <value>{e["copyright_date"]}</value>
            </field>
            <field name="embargo_date" type="date">
                <value>{e["embargo_date"]}</value>
            </field>
            <field name="doi" type="string">
                <value>{doi}</value>
            </field>
            <field name="file_size" type="string">
                <value>{e["file_size"]} pages</value>
            </field>
            <field name="fileformat" type="string">
                <value>application/pdf</value>
            </field>
            <field name="rights_holder" type="string">
                <value>{rights_holder}</value>
            </field>
            <field name="advisor1" type="string">
                <value>{advisor1}</value>
            </field>
            <field name="major" type="string">
                <value>{escape(e["major"])}</value>
            </field>
        </fields>
    </document>"""


        crossref_item_md = ItemMetadata(
            abstract=e["abstract"],
            date={"year": e["publication_date"], "month": "01", "day": "01"},
            degree=e["degree"],
            doi=doi[16:],
            institution_name="Iowa State University",
            kind="dissertation",
            media_type="print",
            person_name={"given_name": " ".join([e["fname"], e["mname"]]).strip(), "surname": e["lname"], "suffix": e["suffix"]},
            resource="https://lib.dr.iastate.edu/rtd/",
            title=e["title"],
        )

        doi_counter += 1
        docs.append(doc)
        doi_md.append(crossref_item_md)
    
    bepress_xml = "\n".join([head] + docs + [tail])
    for d in doi_md:
        crossref_md.insert_item_metadata(d.to_xml())

    crossref_xml = etree.tostring(
        crossref_md.to_xml(), xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode("utf-8")

    return (bepress_xml, crossref_xml)


def build_rtd_xml(rtds: list, doi_counter: int) -> tuple:
    head = """<?xml version='1.0' encoding='UTF-8'?>
<documents xmlns:str="http://www.metaphoricalweb.org/xmlns/string-utilities" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
    tail = """</documents>"""
    docs = []
    doi_md = []

    doi_base = f"https://doi.org/10.31274/rtd-{datetime.date.today().strftime('%Y%m%d')}-"
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    crossref_md = CrossrefXML()
    depositor = Depositor(
        doi_batch_id=timestamp,
        timestamp=timestamp
    )
    crossref_md.insert_depositor(depositor.to_xml())

    for r in rtds:
        doi = f"{doi_base}{doi_counter}"
        r["kind"] = get_kind(r["degree"])
        #print(r)
        rights_holder = f"{r['fname']} {r['mname'] + ' ' if r['mname'] != '' else ''}{r['lname']}{', ' + r['suffix'] if r['suffix'] != '' else ''}"
        doc = f"""    <document>
        <title>{escape(r["title"])}</title>
        <publication-date>{r["publication_date"]}-01-01</publication-date>
        <publication_date_date_format>YYYY-MM-DD</publication_date_date_format>
        <authors>
            <author xsi:type="individual">
                <email/>
                <institution>Iowa State University</institution>
                <lname>{r["lname"]}</lname>
                <fname>{r["fname"]}</fname>
                <mname>{r["mname"]}</mname>
                <suffix>{r["suffix"]}</suffix>
            </author>
        </authors>
        <disciplines></disciplines>
        <keywords>
            {"".join([f"<keyword>{escape(k)}</keyword>" for k in r["keywords"]])}
        </keywords>
        <abstract>{escape(r["abstract"].strip())}</abstract>
        <fulltext-url>https://behost.lib.iastate.edu/DR/{r["file_name"]}</fulltext-url>
        <document-type>{r["kind"]}</document-type>
        <degree_name>{r["degree"]}</degree_name>
        <department>{r["department"]}</department>
        <abstract_format>html</abstract_format>
        <fields>
            <field name="language" type="string">
                <value>en</value>
            </field>
            <field name="provenance" type="string">
                <value>Iowa State University</value>
            </field>
            <field name="copyright_date" type="string">
                <value>{r["publication_date"]}</value>
            </field>
            <field name="doi" type="string">
                <value>{doi}</value>
            </field>
            <field name="file_size" type="string">
                <value>{r["file_size"]}</value>
            </field>
            <field name="fileformat" type="string">
                <value>application/pdf</value>
            </field>
            <field name="rights_holder" type="string">
                <value>{rights_holder}</value>
            </field>
            <field name="major" type="string">
                <value>{r["major"]}</value>
            </field>
            <field name="oclc_number"> type="string">
                <value>{r["oclc"]}</value>
            </field>
        </fields>
    </document>"""

        crossref_item_md = ItemMetadata(
            abstract=r["abstract"],
            date={"year": r["publication_date"], "month": "01", "day": "01"},
            degree=r["degree"],
            doi=doi[16:],
            institution_name=r["institution"],
            kind="dissertation",
            media_type="print",
            person_name={"given_name": " ".join([r["fname"], r["mname"]]).strip(), "surname": r["lname"], "suffix": r["suffix"]},
            resource="https://lib.dr.iastate.edu/rtd/",
            title=r["title"],
        )

        doi_counter += 1
        docs.append(doc)
        doi_md.append(crossref_item_md)
    
    bepress_xml = "\n".join([head] + docs + [tail])
    for d in doi_md:
        crossref_md.insert_item_metadata(d.to_xml())

    
    crossref_xml = etree.tostring(
        crossref_md.to_xml(), xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode("utf-8")

    return (bepress_xml, crossref_xml)