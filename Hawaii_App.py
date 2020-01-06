from flask import Flask, jsonify, request, flash, render_template

from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import pandas as pd
import json
import pprint
from sqlalchemy import create_engine, func


dbpath = '/Users/crobinson1205/Downloads/SQL_AlchemyHW/hawaii.sqlite'

engine = create_engine(f"sqlite:///{dbpath}")
conn = engine.connect()

#get latest date in data set
query = """
select
max(date)
from measurement
"""
data_date = pd.read_sql(query,conn)
maxdate = data_date.iloc[0,0]
maxdate = maxdate.replace("-","")

#pull precipitation data for last year
query = f"""
select
date
,ifnull(prcp,0) as precipitation
from measurement
where cast(replace(date,'-','') as int) > ({maxdate} - 10000) 
"""
data_prcp = pd.read_sql(query,conn)
data_prcp.set_index('date', inplace = True)
data_prcp = data_prcp.sort_index(ascending = True)

#plot precipitation data
data_prcp.plot(y = 'precipitation')
plt.xticks([])

#print precipitation data
data_prcp.to_csv('Hawaii Precipitation data.csv',index=True)

#For Flask app
#data_measure dataframe to dict
dict_dm = data_prcp.to_dict()
precipitation_JSON = json.dumps(dict_dm)

#Total Number of stations
query = """
select count(station) as Stations from station
"""
data_obv = pd.read_sql(query,conn)
print("\n")
print(f"There are {data_obv.iloc[0,0]} total stations in the data set")


#stations and observation counts in descending order
query = """
select
station as Station
,count(station) as Observations
,min(tobs) as [Temperature (min)]
,max(tobs) as [Temperature (max)]
,avg(tobs) as [Temperature (avg)]
from measurement 
group by station
order by Observations desc
"""
data_station = pd.read_sql(query,conn)
station_list = data_station['Station'].values.tolist()

#station with highest observations
print("\n")
print(f"Station {data_station.iloc[0,0]} has the most observations with {data_station.iloc[0,1]}")
print("\n")

#find station with highest amount of observations in the last year of data
query = f"""
select
station as Station
,count(tobs) as Observations
from measurement 
where cast(replace(date,'-','') as int) > ({maxdate} - 10000) 
group by station
order by Observations desc
"""
data_obv_total = pd.read_sql(query,conn)
topstation = data_obv_total.iloc[0,0]

#Observations from station with most observations
query = f"""
select
station
,tobs
from measurement
where cast(replace(date,'-','') as int) > ({maxdate} - 10000) 
and station = '{topstation}'
order by date desc
"""
data_obv_highest = pd.read_sql(query,conn)

#plot data from station with most observations
data_obv_highest.plot(kind = 'hist', bins = 12)


#tempature data from past year - Flask
query =f"""
select
date
,min(tobs) as [Temperature (min)]
,max(tobs) as [Temperature (max)]
,avg(tobs) as [Temperature (avg)]
from measurement 
where cast(replace(date,'-','') as int) > ({maxdate} - 10000) 
"""
data_temp = pd.read_sql(query,conn)
data_temp.set_index('date', inplace = True)
data_temp = data_temp.sort_index(ascending = True)

dict_temp = data_temp.to_dict()

temperature_JSON = json.dumps(dict_temp)

#all temperature recordings - Flask
query =f"""
select
cast(replace(date,'-','') as int) as date
,tobs
from measurement 
"""
data_temp_range = pd.read_sql(query,conn)


#APP
print("Temperature App:")

app = Flask(__name__)

@app.route("/")

def HomePage():
    return (
        f"Welcome to the Hawaii Precipitation API!<br/>"
        f"<br/>"
        f"<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>"
        f"Hawaii Temperature Range Routes:<br/>"
        f"/api/v1.0/start_date/'yyyy-mm-dd'<br/>"
        f"/api/v1.0/start_date/'yyyy-mm-dd'/end_date/'yyyy-mm-dd'<br/>"
        f"<br/>"
        f"*Note insert date(s) where 'yyyy-mm-dd' is provided*<br/>"
    )        

@app.route("/api/v1.0/precipitation")

def precipitation():
    return precipitation_JSON

@app.route("/api/v1.0/stations")

def stations():
    return json.dumps(station_list)
    
@app.route("/api/v1.0/tobs")

def tempature():
    return temperature_JSON

@app.route("/api/v1.0/start_date/<start>")

def date_range_start(start):
    start_mod = int(''.join([x for x in start if x.isdigit()]))

    dbpath = '/Users/crobinson1205/Downloads/SQL_AlchemyHW/hawaii.sqlite'

    engine = create_engine(f"sqlite:///{dbpath}")
    conn = engine.connect()

    query =f"""
    select
    cast(replace(date,'-','') as int) as date
    ,tobs
    from measurement 
    """
    data_temp_start = pd.read_sql(query,conn)
    data_temp_start = data_temp_start.dropna()

    data_temp_start = data_temp_start[(data_temp_start['date'] > start_mod)]
    
    start_dict = {}
    start_dict["Temperature(min)"] = int(data_temp_start.min().iloc[1])
    start_dict["Tempature(max)"] = int(data_temp_start.max().iloc[1])
    start_dict["Temperature(average)"] = int(data_temp_start.mean().iloc[1])

    return json.dumps(start_dict)

@app.route("/api/v1.0/start_date/<start>/end_date/<end>")

def date_range_start_end(start,end):
    start_mod = int(''.join([x for x in start if x.isdigit()]))
    end_mod = int(''.join([x for x in end if x.isdigit()]))

    dbpath = '/Users/crobinson1205/Downloads/SQL_AlchemyHW/hawaii.sqlite'

    engine = create_engine(f"sqlite:///{dbpath}")
    conn = engine.connect()

    query =f"""
    select
    cast(replace(date,'-','') as int) as date
    ,tobs
    from measurement 
    """
    data_temp_range = pd.read_sql(query,conn)
    #data_temp_range = data_temp_range.dropna()

    data_temp_range = data_temp_range[(data_temp_range['date'] > start_mod) & (data_temp_range['date'] < end_mod)]

    range_dict = {}
    range_dict["Temperature(min)"] = int(data_temp_range.min().iloc[1])
    range_dict["Tempature(max)"] = int(data_temp_range.max().iloc[1])
    range_dict["Temperature(average)"] = int(data_temp_range.mean().iloc[1])
    
    return json.dumps(range_dict)

if __name__ == "__main__":
    app.run(debug=True)