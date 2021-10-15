import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    current_date = dt.date.today()
    current_year = int(current_date.strftime("%Y"))
    return {
        'year': current_year,
    }
