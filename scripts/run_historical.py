from wind_wind.historical import get_generation, get_ARE_capacities
import statistics

cfs = []
for year in range(2015, 2026):
    gen = get_generation(year)
    cap = get_ARE_capacities(year)

    cf = gen/cap
    # print(cf)
    cfs.append(cf.mean())
print(f"{statistics.mean(cfs):.2%}")