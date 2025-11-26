import pandas as pd
import numpy as np
import math

# Importing data (manually inputed to avoid importing a csv file)

data_water = {
    "ID": ["w1", "w2", "w3", "w4", "w5", "w6", "w7"],
    "Name": [
        "underground water with disinfection",
        "underground water with chemical treatment",
        "underground water without treatment",
        "conventional treatment",
        "microstrainer treatment",
        "conventional with biological treatment",
        "seawater reverse osmosis"
    ],
    "ecoinvent-v3.5 Dataset": [
        "tap water production, underground water with disinfection",
        "tap water production, underground water with chemical treatment",
        "tap water production, underground water without treatment",
        "tap water production, conventional treatment",
        "tap water production, microstrainer treatment",
        "tap water production, conventional with biological treatment",
        "tap water production, seawater reverse osmosis, conventional pretreatment, baseline module, single stage"
    ],
    "Amount (MJ)": [""]*7,
    "Unit": ["kg"]*7,
    "Comment": [""]*7,
    "Proportion": [0.142857143]*7,
    "CO2": [
        0.000136391,
        0.000297429,
        0.0000141293,
        0.000218099,
        0.000376121,
        0.000287996,
        0.005769645
    ],
    "GEO": [
        "Europe without Switzerland (Europe without Switzerland)",
        "Europe without Switzerland (Europe without Switzerland)",
        "Switzerland (CH)",
        "Europe without Switzerland (Europe without Switzerland)",
        "Rest-of-World (RoW)",
        "Europe without Switzerland (Europe without Switzerland)",
        "Global (GLO)"
    ]
}

df_water = pd.DataFrame(data_water)

data_heat = {
    "ID": ["h1","h2","h3","h4","h5","h6","h7"],
    "Name": [
        "Heat, central or small-scale, share of gas heating",
        "Heat, central or small-scale, share of oil heating",
        "Heat, district or industrial, share of district heating",
        "Heat, borehole heat pump {CH}",
        "Heat, central or small-scale, share from wood heating",
        "Heat, central or small-scale, share from solar thermal",
        "Electricity, low voltage, Zurich, Switzerland"
    ],
    "ecoinvent-v3.5 Dataset": [
        "Heat production, natural gas, at boiler condensing modulating <100kW",
        "Heat production, light fuel oil, at boiler 10kW, non-modulating",
        "Heat from municipal waste incineration to generic market for heat district or industrial, other than natural gas",
        "Heat production, borehole heat exchanger, brine-water heat pump 10kW",
        "Heat production, softwood chips from forest, at furnace 50kW",
        "Operation, solar collector system, Cu flat plate collector, multiple dwelling, for hot water",
        ""
    ],
    "Amount (MJ)": [0.499, 0.272, 0.158, 0.0598, 0.0095, 0.048, 0.248],
    "Unit": ["MJ"]*7,
    "Comment": [
        "Share of gas heating",
        "Share of oil heating",
        "Share of district heating",
        "Share from heat pumps",
        "Share from wood heating",
        "Share from solar thermal",
        "Share from electricity"
    ],
    "Proportion": [0.385536583, 0.210152206, 0.122073708, 0.046202581, 0.007339875, 0.037085683, 0.191609364],
    "CO2": [0.074034296, 0.104351333, 0.000259857, 0.029316816, 0.006017536, 0.002793585, 0.033284045],
    "GEO": [
        "Europe without Switzerland (Europe without Switzerland)",
        "Europe without Switzerland (Europe without Switzerland)",
        "Switzerland (CH)",
        "Europe without Switzerland (Europe without Switzerland)",
        "Switzerland (CH)",
        "Switzerland (CH)",
        "Switzerland (CH)"
    ]
}

df_heat = pd.DataFrame(data_heat)

# Defining functions for distribution and calculation

def water_source_random():
    water_names = df_water['Name'].values
    random_water = np.random.choice(water_names) # Equivalent probability for each value
    co2_factor = df_water.loc[df_water['Name'] == random_water, 'CO2'].values[0]
    return random_water, co2_factor

def heat_source_random():
    heat_names = df_heat['Name'].values
    heat_probs = df_heat['Proportion'].values
    random_heat = np.random.choice(heat_names, p=heat_probs)
    co2_factor = df_heat.loc[df_heat['Name'] == random_heat, 'CO2'].values[0]
    return random_heat, co2_factor

def shower_time_random(mean_log,sig_log):
    shower_time = np.random.lognormal(mean=mean_log, sigma=sig_log, size=1)[0]
    round_time = round(shower_time, 2)
    return round_time

def CO2_cal(shower_duration, water_flow_rate, cte_heat_energy_water, cte_heat_source, cte_heat_energy):
    total_water = shower_duration * water_flow_rate
    total_heat_energy = total_water * cte_heat_energy
    total_CO2eq_heat = total_heat_energy * cte_heat_source
    total_CO2eq_water = total_water * cte_heat_energy_water
    total_CO2eq = total_CO2eq_heat + total_CO2eq_water
    return total_water,total_heat_energy,total_CO2eq_heat,total_CO2eq_water,total_CO2eq

# Constant for water and energy
Flow_rate = 2.5 * 4.546 # Conversion in liter, final unit in liter of water per minute
Heat_Energy = 0.144 # In MJ per liter of water

# Constant for shower distribution
mean = 10 # Mean of shower in minutes
standard_deviation = 3 # std of shower in minutes
variance = standard_deviation**2
mu =  math.log((mean**2)/math.sqrt(variance + (mean**2)))
sigma = math.sqrt(math.log(1 + (variance / (mean**2))))

# Function for Monte Carlo
def run_monte_carlo(N, mu, sigma, Flow_rate, Heat_Energy, seed=None, progress_callback=None):
    if seed is not None:
        np.random.seed(seed)

    results = []

    for i in range(1, N+1):
        shower_time = shower_time_random(mu, sigma)
        heat_name, heat_factor = heat_source_random()
        water_name, water_factor = water_source_random()

        total_water, total_heat_energy, total_CO2_heat, total_CO2_water, total_CO2 = CO2_cal(
            shower_time,
            Flow_rate,
            water_factor,
            heat_factor,
            Heat_Energy
        )

        results.append({
            "Simulation": i,
            "Shower_time_min": shower_time,
            "Heat_Source": heat_name,
            "Heat_CO2_factor": heat_factor,
            "Water_Source": water_name,
            "Water_CO2_factor": water_factor,
            "Total_Water_L": total_water,
            "Total_Heat_Energy_kWh": total_heat_energy,
            "CO2_Heat": total_CO2_heat,
            "CO2_Water": total_CO2_water,
            "CO2_Total": total_CO2
        })

        if progress_callback is not None:
            progress_callback(i / N)

    df_results = pd.DataFrame(results)
    return df_results