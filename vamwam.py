import pandas as pd
import plotly.express as px


def dataprep(df):
    df['vam'] = df['altitude'].diff() / df['timestamp'].diff().dt.total_seconds() * 60 * 60
    df['vamh'] = df['vam'] / df['heart_rate']
    df['interval_time'] = df['timestamp'].diff().dt.total_seconds()
    df['total_time'] = df['timestamp'].diff().dt.total_seconds().cumsum()
    df['speed'] = df['distance'].diff() / df['timestamp'].diff().dt.total_seconds()
    df['speedsqrd'] = df['speed'] ** 2
    df['acceleration'] = df['speed'].diff() / df['timestamp'].diff().dt.total_seconds()
    df['delta_altitude'] = 9.8 * df['altitude'].diff() / df['timestamp'].diff().dt.total_seconds()
    # df['interval_distance'] = df['speed'] * df['interval_time']
    df['interval_distance'] = df['distance'].diff()
    df['slope'] = df['altitude'].diff() / df['interval_distance']
    df['accpower'] = df['acceleration'] * df['speed']
    df['avgpower'] = df['power'].rolling(1).mean()

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


def vam_curves(df):
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
    return vam_curve, vamh_curve


def plot_vam(df, show=True, color=px.colors.sequential.Blues):
    vam_curve, vamh_curve = vam_curves(df)
    slopes = [f"slope_{s}-{s + 1}" for s in range(3, 10)]
    vp = px.line(vam_curve, x="interval", y=slopes, title='Seconds VS VAM',
                 color_discrete_sequence=color)
    vp.update_xaxes(title_text='Seconds')
    vp.update_yaxes(title_text='VAM/hr')
    vp.update_layout(
        width=1000,
        height=800)
    if show:
        vp.show()

    vhp = px.line(vamh_curve, x="interval", y=slopes, title='Seconds VS VAM/hr',
                  color_discrete_sequence=color)
    vhp.update_xaxes(title_text='Seconds')
    vhp.update_yaxes(title_text='VAM/hr')
    vhp.update_layout(
        width=1000,
        height=800)
    if show:
        vhp.show()
    if not show:
        return vp, vhp


def vam_compare(df1, df2):
    vam_curve1, vamh_curve1 = vam_curves(df1)
    vam_curve2, vamh_curve2 = vam_curves(df2)
    slopes = [f"slope_{s}-{s + 1}" for s in range(3, 10)]
    fig = px.line(vam_curve1, x="interval", y=slopes, title='Seconds VS VAM',
                  color_discrete_sequence=px.colors.sequential.Blues)
    fig.add_scatter(x=vam_curve2['interval'], y=vam_curve2[slopes[0]], name=slopes[0])
    fig.add_scatter(x=vam_curve2['interval'], y=vam_curve2[slopes[1]], name=slopes[1])
    fig.add_scatter(x=vam_curve2['interval'], y=vam_curve2[slopes[2]], name=slopes[2])
    fig.add_scatter(x=vam_curve2['interval'], y=vam_curve2[slopes[3]], name=slopes[3])
    fig.add_scatter(x=vam_curve2['interval'], y=vam_curve2[slopes[4]], name=slopes[4])
    fig.add_scatter(x=vam_curve2['interval'], y=vam_curve2[slopes[5]], name=slopes[5])
    fig.add_scatter(x=vam_curve2['interval'], y=vam_curve2[slopes[6]], name=slopes[6])
    fig.update_xaxes(title_text='Seconds')
    fig.update_yaxes(title_text='VAM/hr')
    fig.update_layout(
        width=1000,
        height=800)
    fig.show()

    fig = px.line(vamh_curve1, x="interval", y=slopes, title='Seconds VS VAM/hr',
                  color_discrete_sequence=px.colors.sequential.Blues)
    fig.add_scatter(x=vamh_curve2['interval'], y=vamh_curve2[slopes[0]], name=slopes[0])
    fig.add_scatter(x=vamh_curve2['interval'], y=vamh_curve2[slopes[1]], name=slopes[1])
