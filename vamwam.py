import pandas as pd
import plotly.express as px

from fit2gpx import Converter


def dataprep(afile, source='fit'):
    if source == 'fit':
        conv = Converter()
        df_lap, df = conv.fit_to_dataframes(fname=afile)
    df['vam'] = df['altitude'].diff() / df['timestamp'].diff().dt.total_seconds() * 60 * 60
    df['vamh'] = df['vam'] / df['heart_rate']
    df['interval_time'] = df['timestamp'].diff().dt.total_seconds()
    df['total_time'] = df['timestamp'].diff().dt.total_seconds().cumsum()
    df['interval_distance'] = df['speed'] * df['interval_time']
    df['slope'] = df['altitude'].diff() / df['interval_distance']

    intervals = range(60, 1200, 60)
    for t in intervals:
        df[f'slope_{t}'] = df['slope'].rolling(t).mean() * 100
        df[f'vamh_{t}'] = df['vamh'].rolling(t).mean()
        df[f'vam_{t}'] = df['vam'].rolling(t).mean()
        df[f'hr_{t}'] = df['heart_rate'].rolling(t).mean()
    return df


def vamh_time(df):
    fig = px.scatter(df, x="total_time", y="vamh")
    fig.show()


def vamh_distance(df):
    fig = px.scatter(df, x="interval_distance", y="vamh")
    fig.show()


def plot_vam(df):
    intervals = range(60, 1200, 60)
    slopes = [f"slope_{s}-{s + 1}" for s in range(3, 10)]
    vam_curve = pd.DataFrame(columns=['interval'] + slopes)
    vamh_curve = pd.DataFrame(columns=['interval'] + slopes)
    for t in intervals:
        vam_row = [t]
        vamh_row = [t]
        for s in range(3, 10):
            vam = df[(s < df[f'slope_{t}']) & (df[f'slope_{t}'] < s + 1)][f'vam_{t}'].max()
            vamh = df[(s < df[f'slope_{t}']) & (df[f'slope_{t}'] < s + 1)][f'vamh_{t}'].max()
            if vam:
                vam_row.append(vam)
                vamh_row.append(vamh)
            else:
                vam_row.append(0)
                vamh_row.append(0)
        vam_curve.loc[len(vam_curve.index)] = vam_row
        vamh_curve.loc[len(vamh_curve.index)] = vamh_row

    fig = px.line(vam_curve, x="interval", y=slopes, title='Seconds VS VAM',
                  color_discrete_sequence=px.colors.sequential.Blues)
    fig.update_xaxes(title_text='Seconds')
    fig.update_yaxes(title_text='VAM/hr')
    fig.update_layout(
        width=1000,
        height=800)
    fig.show()

    fig = px.line(vamh_curve, x="interval", y=slopes, title='Seconds VS VAM/hr',
                  color_discrete_sequence=px.colors.sequential.Blues)
    fig.update_xaxes(title_text='Seconds')
    fig.update_yaxes(title_text='VAM/hr')
    fig.update_layout(
        width=1000,
        height=800)
    fig.show()
