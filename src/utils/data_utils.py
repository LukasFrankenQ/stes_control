import matplotlib.pyplot as plt
plt.style.use('bmh')
import pandas as pd
from datetime import datetime
import os

def mtr2df(filename, stop_after_week=False):
    '''
    Reads the .mtr output file (usually 'eplusout.mtr')
    of a besos simulation

    Parameters
    ----------
    filename : str
        mtr file to be read
    stop_after_week : bool
        if tru only reads the data for a single week

    
    Returns
    ----------
    data : pd.DataFrame
        dataframe of time series stored in file

    '''

    file = open(filename, 'r')
    lines = file.readlines()

    df = pd.DataFrame()

    date_indicator = '2.'
    indicators = {}
    columns = []

    # determine end of preamble
    for i, line in enumerate(lines):
        
        if line.startswith('End of Data'):
            separation = i+1
            print(f'Separation found: {separation}')
            break

    preamble = lines[:separation]
    for line in preamble[::-1]:
        line = line.partition(',')
        print(line)
        indicator = line[0]
        try:
            indicator = int(indicator)
            if indicator == 6:
                break

            col = line[-1]
            if ',' in col:
                col = col.partition(',')[-1]

            if col.endswith('\n'):
                col = col[:-1]
            columns.append(col)

        except ValueError:
            continue

    
    lines = lines[separation+1:]
    print('first remaining line')
    print(lines[0])
    columns = columns[::-1]
    len_data = len(lines) // (len(columns) + 1)
    num_cols = len(columns) + 1

    print('cols: ', columns)
    df = pd.DataFrame(columns=['timestamp']+columns)

    for i in range(len_data):
        date = lines[i * num_cols].split(',')
        month = int(date[2])
        day = int(date[3])
        hour = int(date[5]) - 1
        date = pd.Timestamp(datetime(2020, month, day, hour, 0, 0))

        row = {'timestamp': date} 
        for j, col in enumerate(columns):
            line = lines[i * num_cols + j + 1].split(',')[-1]
            row[col] = float(line)

        df = df.append(row, ignore_index=True)

        if i == 24 * 7 and stop_after_week:
            break

    df = df.set_index('timestamp')
    
    print('Obtained data:')
    _, ax = plt.subplots(1, 1, figsize=(16, 4))
    df.plot(ax=ax)
    plt.show()







if __name__ == '__main__':
    filename = os.path.join(os.getcwd(), 'dump', 'eplusout.mtr')
    mtr2df(filename)