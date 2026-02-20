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


def round_down_hour(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0, 0)


def round_up_hour(dt: datetime) -> datetime:
    new_dt = datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0, 0)
    new_dt += timedelta(hours=1)
    return new_dt


def round_down_half_hour(dt: datetime) -> datetime:
    if dt.minute < 30:
        return datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0, 0)
    else:
        return datetime(dt.year, dt.month, dt.day, dt.hour, 30, 0, 0)
