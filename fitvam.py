from math import exp, cos, sin, radians, atan


class FitVam(object):
    """
    Referances:
    https://www.researchgate.net/publication/23986705_New_Method_to_Estimate_the_Cycling_Frontal_Area
    https://link.springer.com/content/pdf/10.1007/s12283-017-0234-1.pdf?pdf=button%20sticky
    https://core.ac.uk/download/pdf/29823669.pdf
    https://www.sciencedirect.com/science/article/pii/S0165232X2100063X
    User set parameters for the fit:
    - dataframe: with start and end time
    The following as a dictionary:
    - bike_weight in kg
    - wind speed in m/s: Default 0
    - wind direction in degrees: Default 0
    - temperature in degrees celcius: Default 20

    Calculated parameters from data points:
    - AirDensity
    - effective_wind_speed

    Estimate the following parameters:
    - rider_weight in kg
    - frontal_area in m^2
    - drag_coefficient"""

    def __int__(self, df, start_time, end_time, end, bike_weight=10, altitude=0, wind_speed=0, wind_direction=0,
                temperature=20,
                drag_coefficient=0.8, frontal_area=0.565, rolling_resistance=.005):
        self.df = df
        self.bike_weight = bike_weight
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.temperature = temperature
        self.drag_coefficient = drag_coefficient
        self.frontal_area = frontal_area
        self.rolling_resistance = rolling_resistance
        self.CdA = self.drag_coefficient * self.frontal_area
        self.air_density = self.air_density()
        self.altitude = (self.df.altitude.max - self.df.altitude.min()) / 2
        self.effective_wind_speed = self.effective_wind_speed()
        self.rider_weight = None
        if 'enhanced_alititude' in df.columns:
            df['slope'] = df.enhanced_alititude.diff()/df.enhanced_alititude.diff()
        else:
            df['slope'] = df.alititude.diff() / df.alititude.diff()
        if "enhanced_speed" in df.columns:
            df['speed'] = df.enhanced_speed
        elif "speed" in df.columns:
            pass
        else:
            df['speed'] = df.distance / df.time

    def air_density(self):
        return ((101325 / (287.05 * 273.15)) * (273.15 / (self.temperature + 273.15)) *
                exp(-101325 / (287.05 * 273.15) * 9.8067 * (self.altitude / 1013.25)))

    def effective_wind_speed(self):
        """ wind_direction 180 tail, 0 = head """
        return cos(radians(self.wind_direction)) * self.wind_speed

    def air_drag(self, speed):
        return 0.5 * self.CdA * self.air_density * (speed / (3.6 + self.effective_wind_speed)) ^ 2

    def climbing_force(self, slope, totalmass):
        return totalmass * 9.0867 * sin(atan(slope))

    def func(self, df):
        self.climbing_force(df.slope, self.rider_weight + self.bike_weight)
        totalmass = self.bike_weight + self.kg
        CDA = frontal * Cd
        speed = distance / time
        # forces
        climbing =
        rolling = cos(atan(slope)) * 9.8067 * totalmass
        airdrag = 0.5 * CDA * ad * (speed / (3.6 + effective_wind)) ^ 2

        return frontal * Cd
