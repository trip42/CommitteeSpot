import re

def plural_to_singular(noun):
    special_cases = {
        'people':'Person',
    }

    if noun.lower() in special_cases:
        return special_cases[noun.lower()]

    plural_map = (
        ('ches','ch'),
        ('xes','x'),
        ('sex','s'),
        ('s',''),
    )

    for pend, send in plural_map:
        if noun.endswith(pend):
            return noun[:-1*len(pend)] + send

    return noun

def validate_email(email):
    if len(email) > 6:
        if re.match('[\w\.-]+@[\w\.-]+\.\w{2,4}', email) != None:
            return True
    return False
