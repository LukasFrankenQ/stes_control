import matplotlib.pyplot as plt
plt.style.use('bmh')
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import os

def mtr2df(filename, twoweeks=False, do_plot=False):
    '''
    Reads the .mtr output file (usually 'eplusout.mtr')
    of a besos simulation

    Parameters
    ----------
    filename : str
        mtr file to be read
    twoweeks : bool
        if true only reads the data for the first two weeks
    do_plot : bool
        if true, plots the data obtained from an .mtr file

    
    Returns
    ----------
    data : pd.DataFrame
        dataframe of time series stored in file

    '''

    file = open(filename, 'r')
    lines = file.readlines()

    df = pd.DataFrame()

    columns = []

    # determine end of preamble
    for i, line in enumerate(lines):
        
        if line.startswith('End of Data'):
            separation = i+1
            break

    preamble = lines[:separation]
    for line in preamble[::-1]:
        line = line.partition(',')
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
    columns = columns[::-1]
    len_data = len(lines) // (len(columns) + 1)
    num_cols = len(columns) + 1

    df = pd.DataFrame(columns=['timestamp']+columns)

    if twoweeks: 
        len_data = 24 * 14

    for i in tqdm(range(len_data)):
        date = lines[i * num_cols].split(',')
        month = int(date[2])
        day = int(date[3])
        hour = int(date[5]) - 1
        weekday = date[-1]
        date = pd.Timestamp(datetime(2020, month, day, hour, 0, 0))

        row = {'timestamp': date} 
        for j, col in enumerate(columns):
            line = lines[i * num_cols + j + 1].split(',')[-1]
            row[col] = float(line)

        df = df.append(row, ignore_index=True)

    df = df.set_index('timestamp')


    if do_plot:
        print('Obtained data:')
        _, ax = plt.subplots(1, 1, figsize=(16, 4))
        ax.set_title('Power flow in: ', filename)
        df.plot(ax=ax)
        plt.show()

    print(f'Done with file {filename}!')

    return df



if __name__ == '__main__':
    filename = os.path.join(os.getcwd(), 'src', 'dump', 'eplusout.mtr')
    mtr2df(filename, twoweeks=True, do_plot=True)