import datetime
import os
from zipfile import ZipFile

from dateutil import relativedelta
from lxml import etree

from td2.data.departments import DEPARTMENTS
from td2.regex import degree_abbr_to_full, RegExReplacer
from td2.xml import get_department as match_department


def unzip_files(in_path, out_path):
    extracted_files = []
    for f in in_path.glob("*.zip"):
        z = ZipFile(f)
        extracted_files.append(z.namelist())

        z.extractall(out_path)

    return extracted_files


def get_metadata(xml_file):
    md = {}

    tree = etree.parse(os.fspath(xml_file))
    md["title"] = get_title(tree)
    md["publication_date"] = get_publication_date(tree)
    md.update(get_name(tree))
    md["keywords"] = get_keywords(tree)
    md["abstract"] = get_abstract(tree)
    md["degree"] = get_degree_name(tree)
    md["department"] = get_department(tree)
    md["copyright_date"] = get_copyright_date(tree)
    md["embargo_date"] = get_embargo_date(tree)
    md["file_size"] = get_file_size(tree)
    md["advisor1"] = get_name(tree, "advisor")
    md["institution"] = "Iowa State University"

    return md


def get_title(tree):
    xpath = "string(//DISS_description/DISS_title)"
    return tree.xpath(xpath)


def get_publication_date(tree):
    xpath = "string(//DISS_description/DISS_dates/DISS_accept_date)"
    return mdy_to_iso(tree.xpath(xpath))


def get_name(tree, kind="author"):
    if kind == "author":
        surname_xpath = "string(//DISS_authorship/DISS_author/DISS_name/DISS_surname)"
        fname_xpath = "string(//DISS_authorship/DISS_author/DISS_name/DISS_fname)"
        middle_xpath = "string(//DISS_authorship/DISS_author/DISS_name/DISS_middle)"
        suffix_xpath = "string(//DISS_authorship/DISS_author/DISS_name/DISS_suffix)"
    elif kind == "advisor":
        surname_xpath = "string(//DISS_description/DISS_advisor/DISS_name/DISS_surname)"
        fname_xpath = "string(//DISS_description/DISS_advisor/DISS_name/DISS_fname)"
        middle_xpath = "string(//DISS_description/DISS_advisor/DISS_name/DISS_middle)"
        suffix_xpath = "string(//DISS_description/DISS_advisor/DISS_name/DISS_suffix)"

    name = {
        "lname": tree.xpath(surname_xpath),
        "fname": tree.xpath(fname_xpath),
        "mname": tree.xpath(middle_xpath),
        "suffix": tree.xpath(suffix_xpath),
    }

    return name


def get_keywords(tree):
    xpath = "string(//DISS_keyword)"
    return tree.xpath(xpath).split(", ")


def get_abstract(tree):
    xpath = "//DISS_abstract/DISS_para/text()"
    return tree.xpath(xpath)


def get_degree_name(tree):
    xpath = "string(//DISS_description/DISS_degree)"
    global degree_abbr_to_full
    abbr_to_degree = RegExReplacer(degree_abbr_to_full)
    degree = abbr_to_degree.replace(tree.xpath(xpath))

    return degree


def get_department(tree):
    xpath = "string(//DISS_inst_contact)"
    global DEPARTMENTS
    department = tree.xpath(xpath)

    department = match_department(department, DEPARTMENTS)

    return department


def get_copyright_date(tree):
    xpath = "string(//DISS_description/DISS_dates/DISS_comp_date)"
    return tree.xpath(xpath)


def get_embargo_date(tree):
    embargo_code_xpath = "string(//DISS_submission/@embargo_code)"
    agreement_date_xpath = "string(//DISS_repository/DISS_agreement_decision_date)"
    embargo_code = int(tree.xpath(embargo_code_xpath))
    try:
        agreement_date = datetime.date.fromisoformat(
            tree.xpath(agreement_date_xpath).split(" ")[0]
        )
    except ValueError:
        agreement_date = datetime.date.today()

    if embargo_code == 0:
        return_date = agreement_date
    elif embargo_code == 1:
        return_date = agreement_date + relativedelta(months=6)
    elif embargo_code == 2:
        return_date = agreement_date + relativedelta(years=1)
    elif embargo_code == 3:
        return_date = agreement_date + relativedelta(years=2)
    elif embargo_code == 4:
        end_date_xpath = "string(//DISS_restriction/DISS_sales_restriction/@remove)"
        return_date = datetime.date.fromisoformat(
            mdy_to_iso(tree.xpath(end_date_xpath))
        )

    return return_date.isoformat()


def get_file_size(tree):
    xpath = "string(//DISS_description/@page_count)"
    return tree.xpath(xpath)


def mdy_to_iso(bad_date):
    m, d, y = bad_date.split("/")
    return f"{y}-{m}-{d}"
