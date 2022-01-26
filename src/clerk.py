import os
import pandas as pd
import matplotlib.pyplot as plt
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
        weather_file(str): path to weather file used in the simulation
        outpath(str): path where run outputs are stored
        _vars(List[str]): list of global variables
        _dirs(List[str]): list of current directories in the output directory
    '''

    def __init__(self, outpath=None, weather_file=None):

        self.df = None
        self.data_dict = None

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
        pass


    def gather_and_store(self, path: str=None):
        '''
        Obtains data using self.gather_output and appends the
        data to self.df
        '''
        files = os.listdir(os.path.join(self.outpath, path))
        files = [os.path.join(self.outpath, path, file) for file in files]
        file = [file for file in files if file.endswith('.mtr')][0]

        df = self.gather_output(os.path.join(path, file))
        df.columns = [path + '_' + col for col in df.columns]

        if self.df is None:
            self.df = df
        else:
            self.df = pd.concat([self.df, df], axis=1)


    def gather_output(self, path: str=None) -> pd.DataFrame:
        '''
        obtains data from all .mtr files in path and returns them as a pd.DataFrame
        '''

        return mtr2df(path or self.outpath)


    def gather_weather(self, epw_path : str, data=[
                            'dry_bulb_temperature',
                            'direct_normal_radiation',
                            'direct_normal_illuminance',
                            'diffuse_horizontal_radiation',
                            'diffuse_horizontal_illuminance'
                            ]
    ):
        '''
        adds weather data to self.df
        '''

        epw, _ = read_epw(epw_path)
        print(epw.head())
        print(epw.tail())

        df = pd.DataFrame({d.getattr(epw, d).values for d in data})

        print(df.head())
        print(df.tail())

