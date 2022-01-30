from datetime import datetime
import numpy as np
from besos import eppy_funcs as ef
from eppy.modeleditor import IDF
from attrdict import AttrDict
from pathlib import Path
import yaml
import pandas as pd
pd.set_option('display.max_columns', None)
import os
import matplotlib.pyplot as plt
plt.style.use('bmh')

from utils.data_utils import mtr2df
from utils.idf_utils import build_model
from config import idf_dict
from config import weather_dict
from dataclerk import DataClerk


def execute_runs(cfg_files=[]):

    IDF.setiddname('C:\\EnergyPlusV9-0-1\\Energy+.idd')

    dummy_file = 'dummy.idf'
    idf_path = os.path.join(os.getcwd(), '..', 'data', 'epm')
    weather_path = os.path.join(os.getcwd(), '..', 'data', 'weather')
    dataclerk = DataClerk(outpath=os.path.join(os.getcwd(), 'saves'))

    for cfg_file in cfg_files:

        print(f'Starting run {cfg_file}.')

        if cfg_file.endswith('.yml') or cfg_file.endswith('.yaml'):
            cfg = yaml.safe_load(Path(cfg_file).read_text())
            cfg = AttrDict(cfg)
        else:
            raise NotImplementedError('Currently only yaml config files are supported')

        dataclerk.gather_and_store_weather(epw_path=os.path.join(
                            weather_path, weather_dict[cfg.waether_path]))

        model = build_model(cfg, idf_path=idf_path, weather_path=weather_path, view=True)
        model.run(output_directory=os.path.join('saves', cfg_file.split('.')[0]))
        print(f'\n Done with run {cfg_file}\n')

        dataclerk.gather_and_store_output(path=cfg_file.split('.')[0])
        dataclerk.to_file()

    print('final report')
    dataclerk.report()

    print('with plots')
    dataclerk.plot_results()


if __name__ == '__main__':

    # Iterate over yml files in runs/ that define the runs
    if not os.getcwd().endswith('src'):
        os.chdir(os.path.join(os.getcwd(), 'src'))

    buildings = ['office', 'school', 'apartment', 'hotel', 'hospital']
    run_cfgs = os.listdir(os.path.join(os.getcwd(), 'runs'))
    run_cfgs = [os.path.join(os.getcwd(), 'runs', run) for run in run_cfgs]
    execute_runs(run_cfgs=run_cfgs)
    
