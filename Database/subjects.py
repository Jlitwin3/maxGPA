"""
This file contains the exact list of required subject/course pairs necessary to complete
each major listed, taken directly from UO catalogue, as well as a NAME key/val pair for 
organizational purposes seen in db.py. Used as a header for the db.py file. It does not contain electives 
nor does it organize whether a class is a possible substitute for another class.

UO catalogue sources:
https://catalog.uoregon.edu/arts-sciences/school-computer-data-sciences/computer-science/ug-computer-science/#requirementstext
https://catalog.uoregon.edu/coll-business/ug-business-admin/#requirementstextcontainer
https://catalog.uoregon.edu/arts-sciences/natural-sciences/mathematics/ug-mathematics/#requirementstext (standard track)
"""

CS = {
    "NAME" : "CS_major",
    "CS"   : ["210", "211", "212", "313", "314", "315", "330", "415", "422", "425"],
    "MATH" : ["231", "232", "251", "252", "341", "343"],
    "PHIL" : ["223"],
}

BA = {
    "NAME" : "BA_major",
    "BA"   : ["101", "169", "211", "213", "308", "322", "325", "453"],
    "EC"   : ["201", "202"],
    "FIN"  : ["311", "316"],
    "MATH" : ["241"],
    "MGMT" : ["311"],
    "MKTG" : ["311"],
    "OBA"  : ["311", "312", "335"],
    "STAT" : ["243"],
}

MATH = {
    "NAME" : "MATH_major",
    "MATH" : ["253", "281", "282", "341", "342", "231", "232", "316", "317"],
    "CS"   : ["122"],
}