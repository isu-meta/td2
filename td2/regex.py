import re

major_to_department = {
    re.compile(
        r"(Agricultural and Biological|Agricultur(e|al)) Engineering|Water Resources"
    ): "Agricultural and Biosystems Engineering",
    re.compile(r"Agricultural Education"): "Agricultural Education and Studies",
    re.compile(r"Soil Science|Crop Production|Plant Breeding"): "Agronomy",
    re.compile(
        r"Animal (Breeding|Nutrition|Physiology)|Meat Science"
    ): "Animal Science",
    re.compile(r"Intermedia"): "Art and Design",
    re.compile(r"Biochem.*"): "Biochemistry, Biophysics and Molecular Biology",
    re.compile(r"Biomedical"): "Biomedical Sciences",
    re.compile(r"Chemical Engineering"): "Chemical and Biological Engineering",
    re.compile(
        r"Civil.*Engineering|Transportation"
    ): "Civil, Construction, and Environmental Engineering",
    re.compile(r"Curriculum"): "Curriculum and Instruction",
    re.compile(
        r"Ecology and Evolutionary Biology"
    ): "Ecology, Evolution, and Organismal Biology",
    re.compile(r"(Analytical|Physical|Organic) Chemistry"): "Chemistry",
    re.compile(r"(Elementary|Higher) Education|Education, School of"): "Education",
    re.compile(
        r"Education(al)? Leadership"
    ): "Educational Leadership and Policy Studies",
    re.compile(
        r"((Electrical|Computer) Engineering)"
    ): "Electrical and Computer Engineering",
    re.compile(r"Engineering.*Mechanics"): "Engineering Science and Mechanics",
    re.compile(r"English"): "English",
    re.compile(
        r"Family and Consumer Sciences Education"
    ): "Family and Consumer Sciences Education and Studies",
    re.compile(r"Food.*Technology"): "Food Technology",
    re.compile(r"^Nutrition$"): "Food Science and Human Nutrition",
    re.compile(r"Geology|Meteorology"): "Geological and Atmospheric Sciences",
    re.compile(
        r"Journalism|Mass Communication"
    ): "Greenlee School of Journalism and Communication",
    re.compile(r"(Flori|Pomi)culture"): "Horitculture",
    re.compile(r"Human Development"): "Human Development and Family Studies",
    re.compile(
        r"Industrial Engineering"
    ): "Industrial and Manufacturing Systems Engineering",
    re.compile(r"Exercise and Sports? Science"): "Kinesiology",
    re.compile(r"Materials Science & Engineering"): "Materials Science and Engineering",
    re.compile(r"Mathe?matics"): "Mathematics",
    re.compile(
        r"^Genetics|Molecular, Cellular, and Developmental Biology"
    ): "Molecular, Cellular and Developmental Biology",
    re.compile(r"Materials Science"): "Materials Science and Engineering",
    re.compile(r"Plant Pathology"): "Plant Pathology and Microbiology",
    re.compile(r"Physics"): "Physics and Astronomy",
    re.compile(r"Sociology"): "Sociology",
    re.compile(
        r"(;|Interdisciplinary|Arts and Humanities|Biological and Physical Sciences|Community Development|Industrial Relations|International Development Studies|Social Sciences|Neuroscience|Information Assurance|Human-Computer Interaction|Bioinformatics|Sustainable Agriculture|Toxicology|Environmental Science|Plant Physiology)"
    ): "Theses &amp; dissertations (Interdisciplinary)",
    re.compile(
        r"Hotel, Restaurant, and Institution Management"
    ): "Hotel, Restaurant and Institutional Management",
    re.compile(r"Interior Design"): "Interior Design",
    re.compile(r"Business|^Management$|Supply Chain and Informaton Systems|^Marketing$"): "Theses &amp; dissertations (College of Business)",
    re.compile(r"Veterinary Microbiology"): "Veterinary Microbiology and Preventive Medicine",
}


degree_abbr_to_full = {
    re.compile(
        r"(M\.? ?(Arch|ARCH)\.?|Master of Archtecture)"
    ): "Master of Architecture",
    re.compile(r"M\.? ?Acc\.?"): "Master of Accounting",
    re.compile(r"M\.? ?Agr?\.?"): "Master of Agriculture",
    re.compile(r"M\.? ?A\.? ?T\.?"): "Master of Arts in Teaching",
    re.compile(r"M\.? ?B\.? ?A\.?"): "Master of Business Administration",
    re.compile(
        r"(M\.? ?C\.? ?R\.? ?P\.?|Master of Regional Planning)"
    ): "Master of Community and Regional Planning",
    re.compile(r"M\.? ?Ed(uc)?\.?"): "Master of Education",
    re.compile(r"M\.? ?E(ng)?r?\.?"): "Master of Engineering",
    re.compile(r"M\.? ?F\.? ?C\.? ?S\.?"): "Master of Family and Consumer Sciences",
    re.compile(r"M\.? ?F\.? ?A\.?"): "Master of Fine Arts",
    re.compile(r"M\.? ?L(and)?\.? ?A(rch)?\.?"): "Master of Landscape Architecture",
    re.compile(r"M\.? ?P\.? ?A\.?"): "Master of Public Administration",
    re.compile(r"M\.? ?S\.? ?M\.?"): "Master of School Mathematics",
    re.compile(r"M(\.|,)? ?S(\.|,)?.*"): "Master of Science",
    re.compile(r"D\.? ?Arch\.?"): "Doctor of Architecture",
    re.compile(r"M\.? ?A\.?"): "Master of Arts",
    re.compile(r"D\.? ?B\.? ?A\.?"): "Doctor of Business Administration",
    re.compile(r"E[Dd]\.? ?D\.?"): "Doctor of Education",
    re.compile(
        r"(P\.? ?[Hh]\.? ?D?\.?|[Dd]octori?al|Doctorate)"
    ): "Doctor of Philosophy",
    re.compile(r"[Dd]r?\.? ?[Mm]ed\.? ?[Vv]et\.?"): "Doctor of Veterinary Medicine",
    re.compile(r"B\.? ?A\.?"): "Bachelor of Arts",
    re.compile(r"B\.? ?S\.?"): "Bachelor of Science",
    re.compile(r"Spec\.? School Psych\.?"): "Specialist, School Psychology",
    re.compile(r"Sp\.?"): "Specialist",
}


class RegExReplacer:
    def __init__(self, pattern_dict):
        self.patterns = pattern_dict

    def replace(self, text):
        for pattern in self.patterns:
            if pattern.search(text):
                return self.patterns[pattern]

        return text
