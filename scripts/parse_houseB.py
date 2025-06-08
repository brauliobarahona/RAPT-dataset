# %%
import os
import h5py
import numpy as np
import pandas as pd

from matplotlib import rcParams
import matplotlib.pyplot as plt
%matplotlib widget

def clean_boiler_measurements(Pb, Ptot):
    """ Force boiler measurements to zero when larger than total consumption.
    """
    _ix = Pb > Ptot
    if np.any(_ix):
        print("Found {} out of {} ({:.2}%) boiler measurements larger than total consumption.".format(
            _ix.sum(), len(_ix), _ix.sum()/len(_ix)*100))
        Pb[_ix] = 0.0
    return Pb

# %%
#path_to_house = "./datasets/dfB_300s.hdf"
home = os.getcwd() 
ddir = "./data/Data_vs01/data" # 5-min data
fn = os.path.join(ddir, "dfB_300s.hdf")
print(os.path.isfile(fn))

# %% Read data from HDF5 file and parse power data to kW
with pd.HDFStore(fn) as store:
    df = store['data']

df.tail()
df.describe().T

pv_chs = ["B_pv_prod_power", "B_to_batt_power", "B_direct_cons_power", "B_to_net_power"]
load_chs = ["B_total_cons_power", "B_boiler_power"]
batt_chs = ["B_to_batt_power", "B_from_batt_power"]
grid_chs = ["B_from_net_power", "B_to_net_power"]
batt_grid_netting_chs = ["B_from_batt_power", "B_from_net_power"]
pow_chs = pv_chs + load_chs + batt_grid_netting_chs
#pow_chs = ["B_pv_prod_power", "B_to_batt_power", "B_direct_cons_power", "B_to_net_power",
#           "B_total_cons_power", "B_boiler_power", "B_from_batt_power", "B_from_net_power"]

df = df[pow_chs]*1e-3  # convert to kW
df.describe().T

# %% Comparing measured PV power at inverter output to sum of power flows to battery, 
#     to direct consumption by loads, and to grid
P_pv = df["B_pv_prod_power"] # measured
P_pvOUT = df[["B_to_batt_power", "B_direct_cons_power", "B_to_net_power"]].sum(axis=1)
plt.scatter(P_pv, P_pvOUT, s=1, alpha=0.1)
plt.show()

# %% Comparing measured total Load to sum of power flows from PV, battery and grid
L = df["B_total_cons_power"] # measured
L_calc = df[["B_direct_cons_power", "B_from_batt_power", "B_from_net_power"]].sum(axis=1)
plt.scatter(L, L_calc, s=1, alpha=0.1)
plt.xlabel("Total Load (kW)")
plt.ylabel("Calculated Load (kW)")

# %% Create data for heating load disaggregation
L_other = df["B_total_cons_power"] - df["B_boiler_power"]
df_LOAD = pd.DataFrame({
                      "B_other": L_other,
                      "B_boiler": df["B_boiler_power"],
                      "total_consumption": df["B_total_cons_power"]
                    })
print(df_LOAD.describe().T)

Pb = clean_boiler_measurements(df_LOAD["B_boiler"], df_LOAD["total_consumption"])
df_LOAD = pd.DataFrame({
                      "total_consumption": df["B_total_cons_power"],
                      "B_boiler": Pb,
                    })
L_other = df_LOAD["total_consumption"] - df_LOAD["B_boiler"]
df_LOAD["B_other"] = L_other
print(df_LOAD.describe().T)

# %% save preprocessed data to csv file
df_LOAD.to_csv(os.path.join(ddir, "HouseB_consumption.csv"), index=True, index_label="datetime", 
  float_format='%.4f')

# %% plots
df_LOAD.plot(figsize=(5, 4), marker='.', markersize=3, alpha=0.5)
plt.ylabel("Power [kW]")