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
    dataclerk = DataClerk(out_path=os.path.join(os.getcwd(), 'saves'),
                    idf_path=os.path.join(os.getcwd(), '..', 'data', 'epm'),
                    weather_path=os.path.join(os.getcwd(), '..', 'data', 'weather'),
                    year=2020
                    )


    for cfg_file in cfg_files:

        print(f'Starting run {cfg_file}.')

        cfg = dataclerk.setup_cfg(cfg_file)
        print('working with cfg')
        dataclerk.gather_and_store_weather(cfg)

        print('before run')
        dataclerk.report(with_head=True)

        model = build_model(cfg, view=False)
        model.run(output_directory=cfg.out_dir)
        print(f'\n Done with run {cfg_file}\n')

        dataclerk.gather_and_store_output(cfg)
        # dataclerk.to_file()

    print('final report')
    dataclerk.report(with_head=True)

    print('with plots')
    # dataclerk.plot_results()


if __name__ == '__main__':

    # Iterate over yml files in runs/ that define the runs
    if not os.getcwd().endswith('src'):
        os.chdir(os.path.join(os.getcwd(), 'src'))

    buildings = ['office', 'school', 'apartment', 'hotel', 'hospital']
    run_cfgs = os.listdir(os.path.join(os.getcwd(), 'runs'))
    run_cfgs = [os.path.join(os.getcwd(), 'runs', run) for run in run_cfgs]
    execute_runs(cfg_files=run_cfgs[:1])
    
