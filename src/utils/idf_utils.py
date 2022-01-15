import os
import pandas as pd
from datetime import datetime
from besos import eppy_funcs as ef, sampling

def set_runperiod(building, 
                  start=None, 
                  end=None, 
                  start_year=None,
                  start_month=None,
                  start_day=None,
                  end_year=None,
                  end_month=None,
                  end_day=None,
                  ):
    '''
    Sets the runperiod of a energy plus model.
    Start and end can be passed as timestamp or as str.
    they may also be passed as inidividual integers.

    Parameters
    ----------
    start : pd.Timestamp or str
        beginning time of the run
    end : pd.Timestamp or str
        end time of the run

    Returns
    ----------
    -

    '''

    # Obtain start as pd.Timestamp
    if start is not None:
        if isinstance(start, str) or isinstance(start, datetime):
            start = pd.Timestamp(start)
        assert isinstance(start, pd.Timestamp), f'Please provide start as str or pd.Timestamp, instead of {type(start)}'

    elif start_year is not None and \
         start_month is not None and \
         start_day is not None:
        print(f'start, start_year, start_month and start_day is None; Start date will not be set')

    elif start_year is None or \
         start_month is None or \
         start_day is None:
        raise ValueError(f'Received partial information: \n start_year: {start_year}, \
                                                         \n start_month: {start_month}, \
                                                         \n start_day: {start_day}')

    else:
        start = pd.Timestamp(datetime(start_year, start_month, start_day))

    # Obtain end as pd.Timestamp
    if end is not None:
        if isinstance(end, str) or isinstance(end, datetime):
            end = pd.Timestamp(end)
        assert isinstance(end, pd.Timestamp), f'Please provide end as str or pd.Timestamp, instead of {type(end)}'

    elif end_year is not None and \
         end_month is not None and \
         end_day is not None:
        print(f'end, end_year, end_month and end_day is None; End date will not be set')

    elif end_year is None or \
         end_month is None or \
         end_day is None:
        raise ValueError(f'Received partial information: \n end_year: {end_year}, \
                                                         \n end_month: {end_month}, \
                                                         \n end_day: {end_day}')

    else:
        end = pd.Timestamp(datetime(end_year, end_month, end_day))

    # set the respective quantities in the model
    for date, obj in zip([start, end], ['Begin', 'End']):
        
        building.__dict__['idfobjects']['RUNPERIOD'][0][obj+'_Year'] = date.year
        building.__dict__['idfobjects']['RUNPERIOD'][0][obj+'_Month'] = date.month
        building.__dict__['idfobjects']['RUNPERIOD'][0][obj+'_Day_of_Month'] = date.day


def show_runperiod(building):
    '''
    Shows the runperiod of a energyplus model

    Parameters
    ----------
    building : besos.IDF_class.IDF 
        the energy plus model of interest

    Returns
    ----------
    -

    '''
    print(building.__dict__['idfobjects']['RUNPERIOD'])


if __name__ == '__main__':

    weather_path = os.path.join(os.getcwd(), '..', 'data', 'weather')
    idf_path = os.path.join(os.getcwd(), '..', 'data', 'epm')

    b = ef.get_building(os.path.join(idf_path, 'smalloffice.idf'))
    
    print(type(b))
    start = '2020-01-01'
    end = '2020-01-08'
    print('Before:')
    show_runperiod(b)
    set_runperiod(b, start=start, end=end)
    print('After:')
    show_runperiod(b)
    b.saveas(os.path.join(idf_path, 'changed.idf'))
    print('After getting it back after saving:')
    b = ef.get_building(os.path.join(idf_path, 'changed.idf'))
    show_runperiod(b)
    print('While the old file stil says:')
    b = ef.get_building(os.path.join(idf_path, 'smalloffice.idf'))
    show_runperiod(b)
    
