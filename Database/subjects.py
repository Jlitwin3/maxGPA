"""
Author: Dennis Hulett, last updated may 4 2026
This file contains the exact list of required subject/course pairs necessary to complete
each major listed, taken directly from UO catalogue, as well as a NAME key/val pair for 
organizational purposes seen in db.py. Used as a header for the db.py file. It does not contain un-listed electives 
nor does it organize whether a class is a possible substitute for another class.

UO catalogue sources:
https://catalog.uoregon.edu/arts-sciences/school-computer-data-sciences/computer-science/ug-computer-science/#requirementstext
https://catalog.uoregon.edu/coll-business/ug-business-admin/#requirementstextcontainer
https://catalog.uoregon.edu/arts-sciences/natural-sciences/mathematics/ug-mathematics/#requirementstext (standard track)

This is, in essence, the exact same data provided by the csv read-in files, but I had been following the requirements given
by the paper handout provided in class, and did not realize how extensively the requirements had been changed in the online
copy until the Sunday before the deadline. The requirements did not say that reading in the degree plan csv's also had to correspond
to how we formatted our databases, so I elected to not change my code as it would take far too long to do so.
"""

CS = {
    "NAME" : "CS_major",
    "CS"   : ["210", "211", "212", "313", "314", "315", "330", "415", "422", "425"],
    "MATH" : ["231", "232", "251", "251Z", "252", "252Z", "261", "246", "341", "343", "345M", "345"],
    "PHIL" : ["223", "123"],
    "WR"   : ["320", "321"],
    "HC"   : ["301", "301H"],
    "CH"   : ["111", "113", "221Z", "221", "224H", "224", "222", "223", "222Z", "223Z"],
    "BI"   : ["221", "222", "223", "221Z", "222Z", "223Z"],
    "ERTH" : ["201", "202", "203"],
    "GEOG" : ["141", "321", "322", "323"],
    "PHYS" : ["201", "202", "203", "251", "252", "253"],
    "PSY"  : ["201", "301", "304", "305", "348"]
}

BA = {
    "NAME" : "BA_major",
    "BA"   : ["101", "101Z", "169", "169Z", "211", "211Z", "213", "213Z", "308", "322", "325", "453", "361", "365", "252"],
    "EC"   : ["201", "202", "201Z", "202Z", "311"],
    "FIN"  : ["311", "316", "380", "410", "462", "463", "464", "473"],
    "MATH" : ["241", "251Z", "251"],
    "MGMT" : ["311", "335", "410", "415", "416", "417", "420", "422", "443", 
              "455", "460", "461"],
    "MKTG" : ["311", "390", "410", "415", "420", "435", "445", "465", "468", "470", "490"],
    "OBA"  : ["311", "312", "335", "410", "444", "455", "465", "466", "477"],
    "STAT" : ["243", "243Z"],
    "WR"   : ["121Z", "121", "122Z", "122", "123"],
    "HC"   : ["101H", "101", "221H", "221"],
    "ACTG" : ["340", "350", "351", "352", "360", "410", "440", 
              "450", "460", "470", "480"],
    "SBUS" : ["410", "450", "452", "453", "455", "456"],
    "ANTH" : ["209"],
    "GLBL" : ["102"]
}

MATH = {
    "NAME" : "MATH_major",
    "MATH" : ["253", "253Z", "281", "282", "307", "201", "202", "203", "204", "205", "206", 
              "341", "342", "231", "232", "316", "317", "347", "348", "391", "392", "343", "345M", "345", 
              "351", "352", "391", "392", "394", "395", "397", "411", "413", "414", "415", "421", 
              "421M", "422", "431", "432", "433", "441", "444", "445", "446", "458", "461", "462", 
              "463", "467"],
    "CS"   : ["122", "210"],
    "DSCI" : ["345M", "345"]
}