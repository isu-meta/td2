from bisect import bisect_left

from fuzzywuzzy import fuzz


def basic_search_tds_metadata(md: dict, tds_md: list) -> dict:
    for m in tds_md:
        if fuzz.ratio(m["title"], md["title"]) >= 90:
            return m

    print(f"Could not find a MARC record for {md['title']}")
    md.update({k: "" for k in ["local_id", "oclc", "abstract", "keywords"]})

    return md


def search_tds_metadata(md: dict, tds_md: list, tds_titles: list) -> dict:
    index = bisect_left(tds_titles, md["title"])

    try:
        if (
            fuzz.ratio(md["title"], tds_md[index]["title"]) < 90
            and fuzz.ratio(md["lname"], tds_md[index]["lname"]) < 90
        ):
            new_index = index - 50 if index - 50 > 0 else 0
            return basic_search_tds_metadata(md, tds_md[new_index:])
        else:
            return tds_md[index]
    except IndexError:
        return basic_search_tds_metadata(md, tds_md)
