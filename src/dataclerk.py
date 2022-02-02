import os
import yaml
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from attrdict import AttrDict
from itertools import product
from datetime import datetime
from pvlib.iotools import read_epw
plt.style.use('bmh')

from utils.data_utils import mtr2df
from config import weather_dict
from config import idf_dict


class DataClerk:
    '''
    Prepares energyplus runs from yaml file
    Collects and stores data during and after a series of EnergyPlus simulations
    
    The central idea is to use DataClerk using a with statement. During this,
    DataClerk automatically stores all time based information

    All relevant variables for an experiments are stored in a directory of directory
    Each item represents one experiment. Each such item is a dict with keys:
        - config_file (str)
        - cfg (dict)
        - data (pandas.DataFrame)

    Also stores paths to relevant directories

    Attributes:
        experiments(dict): 
        df(pd.DataFrame): Stores all time-based data
        data_dict(dict): Stores all data that were created during the simulation and are not cleary time dependent 
        year(int): All data will be unified in its year
        weather_file(str): path to weather file used in the simulation
        outpath(str): path where run outputs are stored
        _vars(List[str]): list of global variables
        _dirs(List[str]): list of current directories in the output directory
    '''

    def __init__(self, out_path=None, year=2020,
                       idf_path=None, weather_path=None):


        self.experiments = {}

        self.data_dict = {'simulations': [], 'quantities': set()}
        self.year = year

        self.out_path = out_path or os.path.join(os.getcwd(), 'data')
        assert os.path.isdir(self.out_path), f'{self.out_path} does not exist'
        
        self._vars = dir()
        self._dirs = os.listdir(self.out_path)

        self.weather_path = weather_path
        self.idf_path = idf_path
        if self.weather_path is None:
            Warning('No weather path provided!')
        if self.idf_path is None:
            Warning('No ep model path provided!')



    def setup_cfg(self, cfg_file : str) -> AttrDict:
        '''
        Returns cfg AttrDict from yaml file. Also sets up the facilities to store results
        in self.experiments
        '''
        if cfg_file.endswith('.yml') or cfg_file.endswith('.yaml'):
            cfg = yaml.safe_load(Path(cfg_file).read_text())
            cfg = AttrDict(cfg)
        else:
            raise NotImplementedError('Currently only yaml config files are supported')

        if '/' in cfg_file: 
            name = cfg_file.split('/')[-1]
        elif '\\' in cfg_file:
            name = cfg_file.split('\\')[-1]
        name = name.split('.')[0]
        cfg['name'] = name
        cfg['out_dir'] = os.path.join(self.out_path, name)
        cfg['idf_path'] = self.idf_path
        cfg['weather_path'] = self.weather_path

        self.experiments[name] = AttrDict({})
        self.experiments[name]['cfg_file'] = name + '.yml'
        self.experiments[name]['cfg'] = cfg

        self.curr_experiment = name 

        return cfg



    def __enter__(self):
        pass


    def __exit__(self, exc_type, exc_value, tb):
        # if exc_type is not None:
        #     tb.format_tb().print_exception(exc_type, exc_value, tb)            
        #    # tb.print_exception(exc_type, exc_value, tb)
        
        new_vars = dir()
        new_vars = [entry for entry in new_vars if not entry in self._vars]

        new_dirs = os.listdir(self.out_path)
        new_dirs = [entry for entry in new_dirs if not entry in self._dirs]

        print('these are the new dirs:')
        print(new_dirs)

        for path in new_dirs:
            df = self.gather_output(path=path)
            
            print(f'for {path} obtained data:')
            print(df.head())


    def report(self, all=False, with_head=False):
        '''
        prints current self.df
        '''
        print('Current data:')

        print('Spanning an index range:')

        if all:
            keys = list(self.experiments)
        else: 
            keys = [self.curr_experiment]

        for key in keys:
            df = self.experiments[key]['data']
            print(f'obtained data for experiment {key}')
            print(df.info())
            print(f'gathered in timeframe: {df.index[0]} to {df.index[-1]}')

            if with_head:
                print(df.head())



    def gather_and_store_output(self, cfg) -> None:
        '''
        Obtains data using self.gather_output and appends the
        data to self.df

        Args:
            cfg(AttrDict): current experiment config
        '''

        try:
            exp_df = self.experiments[cfg.name]['data']
        except KeyError:
            exp_df = None

        name = self.curr_experiment
        path = os.path.join(self.out_path, name)

        files = os.listdir(path)
        files = [os.path.join(path, file) for file in files]
        file = [file for file in files if file.endswith('.mtr')][0]

        df = self.gather_output(os.path.join(path, file))

        df['time_tuple'] = df.apply(lambda row: (row.name.month, 
                                    row.name.day, row.name.hour), axis=1)            

        if exp_df is None:
            exp_df = df
        else:
            exp_df = df.merge(exp_df, on='time_tuple', how='inner')

        if not isinstance(exp_df.index[0], pd.Timestamp):
            exp_df = self.index_as_timestamp(exp_df)

        self.experiments[cfg.name]['data'] = exp_df


    def gather_output(self, path: str = None) -> pd.DataFrame:
        '''
        obtains data from all .mtr files in path and returns them as a pd.DataFrame
        '''
        return  mtr2df(path or self.outpath)


    def gather_and_store_weather(self, cfg, drops=['data_source_unct']):
        '''
        Obtains weather data using self.gather_weather and stores it in self.df

        Args:
            cfg(AttrDict): config file of current experiment
            drops(List[str]): name of columns that are dropped
        '''
        
        try:
            df = self.experiments[self.curr_experiment]['data']
        except KeyError:
            df = None

        # used to match weather data to simulation output data
        epw_path = os.path.join(self.weather_path, weather_dict[cfg.location])
        epw_df = self.gather_weather(epw_path)
        epw_df['time_tuple'] = epw_df.apply(lambda row: (row.month, row.day, row.hour), axis=1)
        epw_df = epw_df.drop(drops, axis=1)

        if df is None:
            df = epw_df
        else:
            df = df.merge(epw_df, on='time_tuple', how='inner')

        if not isinstance(df.index[0], pd.Timestamp):
            df = self.index_as_timestamp(df)
        
        # add weekday if necessary
        if not 'weekday' in df.columns:
            df['weekday'] = df.index.map(lambda x: x.weekday())

        self.experiments[self.curr_experiment]['data'] = df



    def gather_weather(self, epw_path : str, data=[]) -> pd.DataFrame:
        '''
        adds weather data to self.df
        '''

        return read_epw(epw_path)[0]


    def index_as_timestamp(self, df):
        '''
        sets index to datetime type
        '''
        df['timestamp'] = df.apply(lambda row: 
                pd.Timestamp(datetime(self.year, row.month, row.day, row.hour)), axis=1)
        df.set_index('timestamp', inplace=True)

        return df


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

        num_cols = len(columns)

        x = self.df.index
        vals = np.zeros((num_cols, len(x)))

        _, ax = plt.subplots(num_cols, 1, figsize=(16, num_cols*4))
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
