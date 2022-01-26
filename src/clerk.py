import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from itertools import product
from datetime import datetime
from pvlib.iotools import read_epw
plt.style.use('bmh')

from utils.data_utils import mtr2df


class DataClerk:
    '''
    Collects and stores data during and after a series of EnergyPlus simulations
    
    The central idea is to use DataClerk using a with statement. During this,
    DataClerk automatically stores all time based information

    Attributes:
        df(pd.DataFrame): Stores all time-based data
        data_dict(dict): Stores all data that were created during the simulation and are not cleary time dependent 
        year(int): All data will be unified in its year
        weather_file(str): path to weather file used in the simulation
        outpath(str): path where run outputs are stored
        _vars(List[str]): list of global variables
        _dirs(List[str]): list of current directories in the output directory
    '''

    def __init__(self, outpath=None, weather_file=None, year=2020):

        self.df = None
        self.data_dict = {'simulations': [], 'quantities': set()}
        self.year = year

        self.outpath = outpath or os.path.join(os.getcwd(), 'data')
        assert os.path.isdir(self.outpath), f'{self.outpath} does not exist'
        
        self._vars = dir()
        self._dirs = os.listdir(self.outpath)

        self.weather_file = weather_file
        if self.weather_file is None:
            Warning('No weather file provided!')


    def __enter__(self):
        pass


    def __exit__(self, exc_type, exc_value, tb):
        # if exc_type is not None:
        #     tb.format_tb().print_exception(exc_type, exc_value, tb)            
        #    # tb.print_exception(exc_type, exc_value, tb)
        
        new_vars = dir()
        new_vars = [entry for entry in new_vars if not entry in self._vars]

        new_dirs = os.listdir(self.outpath)
        new_dirs = [entry for entry in new_dirs if not entry in self._dirs]

        print('these are the new dirs:')
        print(new_dirs)

        for path in new_dirs:
            df = self.gather_output(path=path)
            
            print(f'for {path} obtained data:')
            print(df.head())


    def report(self):
        '''
        prints current self.df
        '''
        print('Current data:')

        print('Spanning an index range:')
        print(f'from {self.df.index[0]} to {self.df.index[-1]}')

        print(self.df.info())


    def gather_and_store_output(self, path: str=None) -> None:
        '''
        Obtains data using self.gather_output and appends the
        data to self.df
        '''
        self.data_dict['simulations'].append(path)

        files = os.listdir(os.path.join(self.outpath, path))
        files = [os.path.join(self.outpath, path, file) for file in files]
        file = [file for file in files if file.endswith('.mtr')][0]

        df = self.gather_output(os.path.join(path, file))
        self.data_dict['quantities'].update(df.columns)
        df.columns = [path + '_' + col for col in df.columns]

        df['time_tuple'] = df.apply(lambda row: (row.name.month, row.name.day, row.name.hour), axis=1)            

        if self.df is None:
            self.df = df

        else:
            self.df = self.df.merge(df, on='time_tuple', how='inner')

        if not isinstance(self.df.index[0], pd.Timestamp):
            self.set_index_time()


    def gather_output(self, path: str = None) -> pd.DataFrame:
        '''
        obtains data from all .mtr files in path and returns them as a pd.DataFrame
        '''
        return  mtr2df(path or self.outpath)


    def gather_and_store_weather(self, epw_path: str = None, drops=['data_source_unct']) -> None:
        '''
        Obtains weather data using self.gather_weather and stores it in self.df

        epw_path(str): path to weather file
        drops(List[str]): name of columns that are dropped
        '''
        
        # used to match weather data to simulation output data
        epw_df = self.gather_weather(epw_path)
        epw_df['time_tuple'] = epw_df.apply(lambda row: (row.month, row.day, row.hour), axis=1)
        epw_df = epw_df.drop(drops, axis=1)

        if self.df is None:
            self.df = epw_df
        else:
            self.df = self.df.merge(epw_df, on='time_tuple', how='inner')

        if not isinstance(self.df.index[0], pd.Timestamp):
            self.set_index_time()
        
        # add weekday if necessary
        if not 'weekday' in self.df.columns:
            self.df['weekday'] = self.df.index.map(lambda x: x.weekday())


    def gather_weather(self, epw_path : str, data=[]) -> pd.DataFrame:
        '''
        adds weather data to self.df
        '''

        return read_epw(epw_path)[0]


    def set_index_time(self):
        '''
        sets index to datetime type
        '''
        self.df['timestamp'] = self.df.apply(lambda row: 
                pd.Timestamp(datetime(self.year, row.month, row.day, row.hour)), axis=1)
        self.df.set_index('timestamp', inplace=True)


    def plot_results(self, simulations='all', columns='all') -> None:
        '''
        Plots desired columns for chosen simulations using
        a 'fill-between' plot.

        Args:
            simulations ('all' or List[str]): simulation runs that should be plotted
            columns ('all' or List[str]): quantities that should be plotted
        '''
        
        if simulations == 'all':
            simulations = self.data_dict['simulations']
        
        if columns == 'all':
            columns = self.data_dict['quantities']

        num_sims = len(simulations)
        num_cols = len(columns)

        _, ax = plt.subplots(num_cols, 1, figsize=(16, num_cols*4))

        x = self.df.index
        vals = np.zeros((num_cols, len(x)))
        for (i, col), sim in product(enumerate(columns), simulations):

            y = self.df[sim + '_' + col]
            ax[i].fill_between(x, vals[i]+y, y2=vals[i], label=sim)
            vals[i] += y

        ax[0].legend()

        for a in ax:
            a.set_axisbelow(True)

        for i, col in enumerate(columns):
            ax[i].set_title(col)

        plt.tight_layout()
        plt.show()
