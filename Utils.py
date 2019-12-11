import xlsxwriter
import os
import pandas as pd

def createCSVFile(positions, selections):
        columnsNames = []
        for i in range(len(selections)):
            columnsNames.append(f'x{i}')
            columnsNames.append(f'y{i}')
            columnsNames.append(f'size : {i}')
        df = pd.DataFrame(columns=columnsNames)
        for i in range(len(selections)):
            df[f'x{i}'] = [positions[i][j][0] for j in range(len(positions[i]))]
            df[f'y{i}'] = [positions[i][j][1] for j in range(len(positions[i]))]
            df[f'size : {i}'] = [selections[i]["size"] if j == 0 else "" for j in range(len(positions[i]))]

        print(df)
        df.to_csv('CSVfile.csv')

def createExcelFile(positions, selections):
    workbook = xlsxwriter.Workbook('BookTracking.xlsx')
    worksheet = workbook.add_worksheet()

    row = 5
    col = 0

    greyHeader = workbook.add_format()
    greyHeader.set_pattern(1)
    greyHeader.set_bg_color('#C0C0C0')

    noSize = workbook.add_format()
    noSize.set_pattern(1)
    noSize.set_bg_color('red')

    worksheet.write(row, col, 'Particles', greyHeader)
    worksheet.write(row, col + 1, 'Size (m)', greyHeader)
    row += 1
    firtSizeRow = row
    firstSizeCol = col
    for i in range(len(selections)):
        worksheet.write(row, col, i)
        worksheet.write(row, col + 1, selections[i]['size'])
        row += 1

    worksheet.conditional_format(f'B{firtSizeRow}:B{row}', {'type':     'cell',
                                            'criteria': '==',
                                            'value':    '"None"',
                                            'format':   noSize})

    if row < 22:
        row = 22                           


    worksheet.write(row, col, 'Frame', greyHeader)
    col = 1
    for i in range(len(positions)):
        worksheet.write(row, col, f"x{i + 1}", greyHeader)
        worksheet.write(row, col + 1, f"y{i + 1}", greyHeader)
        col += 2
    row += 1
    col = 0
    firstTrackingRow = row

    for i in range(len(positions[0])):
        worksheet.write(row, col, i + 1)
        row += 1
    col = 1
    row = firstTrackingRow
    chart = workbook.add_chart({'type': 'scatter'})
    for i in range(len(positions)):
        for x, y in positions[i]:
            worksheet.write(row, col,     x)
            worksheet.write(row, col + 1, y)
            row += 1
        chart.add_series({'name': f'Particle{i + 1}',
                            'categories': ['Sheet1', firstTrackingRow, col, row, col],
                            'values':     ['Sheet1', firstTrackingRow, col + 1, row, col + 1],
                        })
        row = firstTrackingRow
        col += 2

    chart.set_title ({'name': 'Trajectories'})
    chart.set_x_axis({'name': 'X'})
    chart.set_y_axis({'name': 'Y'})
    chart.set_x_axis({
        'major_gridlines': {'visible': False},
        'minor_gridlines': {'visible': False},
        'visible': False
    })
    chart.set_y_axis({
        'major_gridlines': {'visible': False},
        'minor_gridlines': {'visible': False},
        'visible': False
    })
    chart.set_plotarea({
        'fill':   {'color': '#ededed'}
    })
    worksheet.insert_chart('D6', chart)

    worksheet.write(0, 0, "Credits " + u"\u00A9")
    worksheet.write(0, 1, "Séverin FERARD")

    merge_format = workbook.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'red',
        'text_wrap': True})
    worksheet.merge_range('E1:G3', "Don't forget to Save !\nFile > Save As", merge_format)

    workbook.close()
    os.system("open -a 'Microsoft Excel' 'BookTracking.xlsx'")