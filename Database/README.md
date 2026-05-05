AUTHOR: Dennis Hulett
Created adminindex.html, db.py, subjects.py, and docker-compose.yml/Dockerfile/requirements.txt, as well as this README

the docker compose file is what i used to run/test my database setup. running docker compose up in this folder in your terminal should spin up the database in docker, as well as a simple html page that you can open at http://localhost:5000/ (5000 can be replaced by any port of your choosing but that is currently what is specified in the docker compose file) that will prompt the user to submit a csv file, which will then be parsed and sorted into the three collections in the database.

the three collections in the database are categorized by major -- our three selected majors are CS, business admin, and math. for more information regarding what classes are considered to be involved in each major, look at the subjects.py file.

the db.py file, in abstract, takes the csv that was provided and converts each applicable line (as in, matches with the data given in subjects.py) into a document that is inserted into the database. each document looks like this:
document {
        "term": term, 
        "major": subj,
        "class": numb,
        "professors": [instructor_entry]
    }

where each instructor entry looks like this: 
instructor_entry = {"crn": crn, "name": instructor, "grades": grade_dist}

for a practical example: in the pub_rec_master_f2015-u2025.csv file provided by the instructors, a particular series of lines that would be added to both the CS major as well as the MATH major looks as follows:

202203,Spring 2023,MATH,252,33730,"Hu, Yang ",0,4,6,3,3,2,1,0,2,0,0,0,1,0,0,0,3,22
202203,Spring 2023,MATH,252,33731,"Dunn, Francis Charles",0,2,2,1,4,2,0,4,2,0,3,1,2,0,0,0,0,23
202203,Spring 2023,MATH,252,33732,"Brooke, Corey Tucker",1,2,2,1,3,4,2,5,1,1,2,1,4,0,1,0,1,30
202203,Spring 2023,MATH,252,33733,"Fritze, Halley Ann",0,3,0,0,4,3,3,9,3,1,3,0,2,0,4,0,0,35
202203,Spring 2023,MATH,252,33734,"Manco Berrio, Diego Fernando ",3,6,3,1,4,2,2,0,0,0,0,0,1,1,0,0,2,23
202203,Spring 2023,MATH,252,33736,"Haight, Sean Patrick Robert",3,3,1,4,5,1,1,4,3,2,2,1,1,0,2,0,1,33
202203,Spring 2023,MATH,252,33737,"Granath, Elliot M",27,6,0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,34

and the key provided at the top of the csv looks like this:
TERM,TERM_DESC,SUBJ,NUMB,CRN,INSTRUCTOR,AP,A,AM,BP,B,BM,CP,C,CM,DP,D,DM,F,P,N,OTHER,W,TOT_NON_W

in db.py, using a key that matches TERM, SUBJ, and NUMB (in this case, (202203, MATH, 252)), all of the professors for this class will be concatenated into a single document that looks like this*:
    {
        "term": 202203, 
        "major": MATH,
        "class": 252,
        "professors": [
            {"crn": 33730, "name": "Hu, Yang ", "grades": {A:10, B:8, C:3, DNF:1}}
            {"crn": 33731, "name": "Dunn, Francis Charles", "grades": {A:4, B:6, C:6, DNF: 6}}
            {"crn": 33732, "name": "Brooke, Corey Tucker", "grades": {A:3, B:8, C:8, DNF: 9}}
            {"crn": 33733, "name": "Fritze, Halley Ann", "grades": {A:3, B:7, C:15, DNF: 10}}
            {"crn": 33734, "name": "Manco Berrio, Diego Fernando ", "grades": {A:12, B:7, C:2, DNF:1}}
            {"crn": 33736, "name": "Haight, Sean Patrick Robert", "grades": {A:7, B:10, C:8, DNF:8}}
            {"crn": 33737, "name": "Granath, Elliot M", "grades": {A:33, B:1, C:0, DNF:0}}
        ]
    }

*i combined all of the letter grades in my head while writing this so the actual numbers might accidentally be off. either way ideally the structure still gets across.

this is an extreme example that includes a lot of professors to show the most hectic a single document might look; most classes only tend to have one or two professors that teach it in any given term. the functions to parse all of this data are fully written, and parsing the csv file mentioned above only took about a second. i have left a multitude of comments in the db.py file that should hopefully communicate exactly what each function is doing.

