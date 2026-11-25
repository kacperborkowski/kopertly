from io import BytesIO

from openpyxl import Workbook

MONTHS = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec",
          "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]


def make_xlsx(sheets: dict[str, list[list]]) -> BytesIO:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for title, rows in sheets.items():
        sheet = workbook.create_sheet(title)
        for row in rows:
            sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer
