from datetime import datetime


def time_format_iso8601(time_str: str) -> datetime:
    """
    Only support "2020-09-23T16:00:00Z" this type time data,
    and support all time zome like Z H ...

    Args:
        time_str ([str]): '2019-08-31T06:33:29Z'
                          '2019-08-31T06:33:29H'
                          or more ...
        https://en.wikipedia.org/wiki/List_of_military_time_zones
    Returns:
        [datetime.datetime]: utc datetime 
        [bool]: False error format.
    """
    try:
        time_zone = {
            "A": 1,
            "B": 2,
            "C": 3,
            "D": 4,
            'E': 5,
            'F': 6,
            'G': 7,
            'H': 8,
            'I': 9,
            'K': 10,
            'L': 11,
            'M': 12,
            'N': -1,
            'O': -2,
            'P': -3,
            'Q': -4,
            'R': -5,
            'S': -6,
            'T': -7,
            'U': -8,
            'V': -9,
            'W': -10,
            'X': -11,
            'Y': -12,
            'Z': 0
        }[time_str[-1]]
    except:
        return False
    raw_time = datetime.strptime(time_str[:-1], "%Y-%m-%dT%H:%M:%S")
    utc_time = raw_time + datetime.timedelta(hours=-time_zone)
    return utc_time
