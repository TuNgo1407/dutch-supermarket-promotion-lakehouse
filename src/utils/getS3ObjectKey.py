from typing import NamedTuple

class DateTuple(NamedTuple):
    year:str
    month:str
    week:str    


def get_s3_object_key(DateTuple:DateTuple,cat:str):

    return f"supermarkets/year={DateTuple.year}/month={DateTuple.month}/week={DateTuple.week}/cat={cat}.json"