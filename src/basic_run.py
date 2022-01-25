from datetime import datetime
import numpy as np
from besos import eppy_funcs as ef
from eppy.modeleditor import IDF
import pandas as pd
import os
import matplotlib.pyplot as plt
plt.style.use('bmh')

from utils.data_utils import mtr2df
from utils.idf_utils import show_runperiod, set_runperiod
from config import file_dict
from clerk import DataClerk

def run_buildings(buildings=None):

    dummy_file = 'dummy.idf'
    idf_path = os.path.join(os.getcwd(), '..', 'data', 'epm')
    weather_file = os.path.join(os.getcwd(), '..', 'data', 'weather', 'portangeles.epw')
    print(os.getcwd())
    clerk = DataClerk(outpath=os.path.join('src', 'saves'))

    for building in buildings:

        with clerk:

            print(f'Starting analysis of {building}.')

            # Change the model runtime according to need
            model = ef.get_building(os.path.join(idf_path, file_dict[building]))
            model.view_model()

            start = pd.Timestamp(datetime(2020, 2, 1))
            end = pd.Timestamp(datetime(2020, 2, 16))

            set_runperiod(model, start=start, end=end)
            model.saveas(dummy_file)

            IDF.setiddname('C:\\EnergyPlusV9-0-1\\Energy+.idd')

            model = IDF(dummy_file, weather_file)

            elec_out = model.newidfobject('OUTPUT:METER:METERFILEONLY',)
            elec_out.Key_Name = 'Electricity:Facility'
            elec_out.Reporting_Frequency = 'Hourly'

            gas_out = model.newidfobject('OUTPUT:METER:METERFILEONLY',)
            gas_out.Key_Name = 'Gas:Facility'
            gas_out.Reporting_Frequency = 'Hourly'

            model.run(output_directory=os.path.join('saves', building))

            print(f'Done with {building}')


def plot_flows(buildings=None):
    
    data = []

    for building in buildings:

        file = os.path.join('saves', building, 'eplusout.mtr')
        data.append(mtr2df(file))

    num_cols = len(data[0].columns) - 1
    _, ax = plt.subplots(num_cols, 1, figsize=(16, num_cols*4))

    cols = list(data[0].columns)
    cols.remove('weekday')
    for i, col in enumerate(cols):
        
        x = data[0].index
        vals = np.zeros(len(x))
        for df, building in zip(data, buildings):
            y = np.array(df[col])

            ax[i].fill_between(x, vals+y, y2=vals, label=building)
            vals += y

    ax[0].legend()

    for a in ax:
        a.set_axisbelow(True)

    for i, col in enumerate(cols):
        ax[i].set_title(col)


if __name__ == '__main__':
    buildings = ['office', 'school', 'apartment', 'hotel', 'hospital']
    run_buildings(buildings=buildings)
    plot_flows(buildings=buildings)
