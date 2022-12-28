import os

from loadfiles import fit2dict, fit2df, fit2csv, fit2excel


def test_fit2dict():
    fitfile = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    fit_dict = fit2dict(fitfile)
    assert fit_dict['header']['version'] == 21.0
    assert len(fit_dict['records']) == 3303
    assert len(fit_dict['events']) == 1
    assert len(fit_dict['sessions']) == 1
    assert len(fit_dict['other_records']) == 0


def test_fit2df():
    fitfile = "testdata/tempfiles/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    df = fit2df(fitfile)
    assert df.shape == (3303, 10)
    assert df.index.name == 'timestamp'
    assert df.columns.tolist() == ['cadence', 'distance', 'enhanced_altitude', 'enhanced_speed', 'grade', 'heart_rate',
                                   'position_lat', 'position_long', 'power', 'temperature']


def testfit2csv():
    fitfile = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    outfile = "testdata/tempfiles/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.csv"
    fit2csv(fitfile, outfile)
    assert os.path.exists(outfile)


def testfit2excel():
    fitfile = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    outfile = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.xlsx"
    fit2excel(fitfile, outfile)
    assert os.path.exists(outfile)
