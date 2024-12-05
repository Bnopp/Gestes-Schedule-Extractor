import re
import json

data = """
[
    { id: 'C_15412_66_3_0', start: '2024-08-19T08: 00: 00',end :'2024-08-19T09: 35: 00', title:'ACCUEIL (Le Franc)',className:'title_centre', backgroundColor:'rgb(112,
        117,
        143)', extendedProps: {commentaire:'Groupe : SIG1, Module : SI130 - BRIT1 - Branches instrumentales 1'
        }
    },
    { id: 'C_10057_43_2_1', start: '2024-08-19T09: 50: 00',end :'2024-08-19T11: 25: 00', title:'MARK (Bruyndonckx)',className:'title_centre', backgroundColor:'rgb(112,
        117,
        143)', extendedProps: {commentaire:'Groupe : SIG1-inf, Module : SI110 - CGES - Compléments de gestion <br/><u>Commentaires :</u><br/>Importation horaires du 19-06-2024'
        }
    },
    { id: 'C_10063_3_7_2', start: '2024-08-20T08: 00: 00',end :'2024-08-20T09: 35: 00', title:'TSYS (Bron)',className:'title_centre', backgroundColor:'rgb(112,
        117,
        143)', extendedProps: {commentaire:'Groupe : SIG1, Module : SI120 - INGP - Ingénierie Plateformes<br/><u>Commentaires :</u><br/>Importation horaires du 19-06-2024'
        }
    },
    { id: 'C_10064_66_3_3', start: '2024-08-20T09: 50: 00',end :'2024-08-20T11: 25: 00', title:'MATH (Le Franc)',className:'title_centre', backgroundColor:'rgb(112,
        117,
        143)', extendedProps: {commentaire:'Groupe : SIG1, Module : SI130 - BRIT1 - Branches instrumentales 1<br/><u>Commentaires :</u><br/>Importation horaires du 19-06-2024'
        }
    },
    { id: 'C_10050_158_2_4', start: '2024-08-20T13: 10: 00',end :'2024-08-20T16: 35: 00', title:'BECO (Barbafieri)',className:'title_centre', backgroundColor:'rgb(112,
        117,
        143)', extendedProps: {commentaire:'Groupe : SIG1-inf, Module : SI110 - CGES - Compléments de gestion <br/><u>Commentaires :</u><br/>Importation horaires du 19-06-2024'
        }
    }
]
"""

# Step 1: Fix 'end :' to 'end:'
data = data.replace("end :", "end:")

# Step 2: Remove spaces after colons in time strings
data = re.sub(r"T(\d+):\s*(\d+):\s*(\d+)", r"T\1:\2:\3", data)

# Step 3: Quote property names
property_names = [
    "id",
    "start",
    "end",
    "title",
    "className",
    "backgroundColor",
    "extendedProps",
    "commentaire",
]
pattern = r"(\b(?:" + "|".join(property_names) + r")\b)\s*:"
data = re.sub(pattern, r'"\1":', data)

# Step 4: Replace single quotes with double quotes
data = data.replace("'", '"')


# Step 5: Escape line breaks inside strings
def escape_line_breaks(match):
    return match.group(0).replace("\n", "\\n")


data = re.sub(r"\"(.*?)\"", escape_line_breaks, data, flags=re.DOTALL)

# Step 6: Parse the JSON data
try:
    data_json = json.loads(data)
    # Step 7: Pretty-print the JSON data with proper encoding
    print(json.dumps(data_json, indent=4, ensure_ascii=False))
except json.JSONDecodeError as e:
    print("JSON decode error:", e)
