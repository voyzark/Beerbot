from datetime import datetime, timedelta

def next_monday(dt: datetime = None) -> datetime:
    dt = dt or datetime.now()
    dt = round_down_day(dt)
    return dt + timedelta(days=7-dt.weekday())


def round_down_day(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day, 0, 0, 0, 0)


def format_german(dt: datetime) -> str:
    weekday_abbreviation = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    
    weekday = weekday_abbreviation[dt.weekday()]
    return f'{weekday}, {dt.strftime("%d.%m. %H:%M Uhr")}'

if __name__ == '__main__':
    dt = next_monday() + timedelta(hours=20)
    print( format_german(dt) )