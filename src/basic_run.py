from datetime import datetime
import numpy as np
from besos import eppy_funcs as ef
from eppy.modeleditor import IDF
import pandas as pd
pd.set_option('display.max_columns', None)
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

    clerk = DataClerk(outpath=os.path.join(os.path.join(os.getcwd(), 'saves')))

    clerk.gather_and_store_weather(epw_path=weather_file)

    for building in buildings:

        # with clerk:
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

        print(f'\n Done with {building}\n')
        
        clerk.gather_and_store_output(path=building)

    print('final report')
    clerk.report()

    print('with plots')
    clerk.plot_results()


if __name__ == '__main__':

    if not os.getcwd().endswith('src'):
        os.chdir(os.path.join(os.getcwd(), 'src'))

    buildings = ['office', 'school', 'apartment', 'hotel', 'hospital']
    run_buildings(buildings=buildings)
    
