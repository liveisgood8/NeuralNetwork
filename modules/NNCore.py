from pandas import DataFrame
from pandas import Series
from pandas import concat
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras import backend as KerasBackend
from math import sqrt
from matplotlib import pyplot
import numpy

from PyQt5 import QtCore

'''
TODO
Сделать потом несколько повторов
Поэксперемнтировать с количеством элементов в пачке (batch size)
Поэксперементировать с количествой нейронов (neurons)
'''


class Predictions:
    values = None
    rmse = 0


class NeuralNetwork:
    def __init__(self, data, repeats, epoch, batch_size, lstm_neurons):
        self.repeats = repeats
        self.epoch = epoch
        self.batch_size = batch_size
        self.lstm_neurons = lstm_neurons
        self.raw_values = data.ix[:, 1]

        # transform data to be stationary
        diff_values = self.difference(self.raw_values, 1)

        # transform data to be supervised learning
        supervised = self.timeseries_to_supervised(diff_values, 1)
        supervised_values = supervised.values

        # split data into train and test-sets on two equal parts
        self.sv_len = (len(supervised_values) - 1) // 2
        self.train, self.test = supervised_values[0:self.sv_len], supervised_values[-self.sv_len:]

        # transform the scale of the data
        self.scaler, self.train_scaled, self.test_scaled = self.scale(self.train, self.test)

        KerasBackend.clear_session()

    # frame a sequence as a supervised learning problem
    @staticmethod
    def timeseries_to_supervised(data, lag=1):
        df = DataFrame(data)
        columns = [df.shift(i) for i in range(1, lag + 1)]
        columns.append(df)
        df = concat(columns, axis=1)
        df.fillna(0, inplace=True)
        return df

    # create a differenced series
    @staticmethod
    def difference(dataset, interval=1):
        diff = list()
        for i in range(interval, len(dataset)):
            value = dataset[i] - dataset[i - interval]
            diff.append(value)
        return Series(diff)

    # invert differenced value
    @staticmethod
    def inverse_difference(history, yhat, interval=1):
        return yhat + history.iloc[-interval]

    # scale train and test data to [-1, 1]
    @staticmethod
    def scale(train, test):
        # fit scaler
        scaler = MinMaxScaler(feature_range=(-1, 1))
        scaler = scaler.fit(train)
        # transform train
        train = train.reshape(train.shape[0], train.shape[1])
        train_scaled = scaler.transform(train)
        # transform test
        test = test.reshape(test.shape[0], test.shape[1])
        test_scaled = scaler.transform(test)
        return scaler, train_scaled, test_scaled

    # inverse scaling for a forecasted value
    @staticmethod
    def invert_scale(scaler, X, value):
        new_row = [x for x in X] + [value]
        array = numpy.array(new_row)
        array = array.reshape(1, len(array))
        inverted = scaler.inverse_transform(array)
        return inverted[0, -1]

    # fit an LSTM network to training data
    def fit_lstm(self, iteration_callback):
        X, y = self.train_scaled[:, 0:-1], self.train_scaled[:, -1]
        X = X.reshape(X.shape[0], 1, X.shape[1])
        model = Sequential()
        model.add(LSTM(self.lstm_neurons, batch_input_shape=(self.batch_size, X.shape[1], X.shape[2]), stateful=True))
        model.add(Dense(1))
        model.compile(loss='mean_squared_error', optimizer='adam')

        for i in range(self.epoch):
            model.fit(X, y, epochs=1, batch_size=self.batch_size, verbose=0, shuffle=False)
            model.reset_states()
            iteration_callback(i)
        return model

    # make a one-step forecast
    def forecast_lstm(self, model, batch_size, X):
        X = X.reshape(1, 1, len(X))
        yhat = model.predict(X, batch_size=batch_size)
        return yhat[0, 0]

    def make_multi_predictions(self, repeat_iterator_callback, epoch_iterator_callback):
        for i in range(self.repeats):
            model = self.fit_lstm(epoch_iterator_callback)

            predictions = Predictions()
            predictions.values, predictions.rmse = self.prediciotns_repeat(model)
            repeat_iterator_callback(i, predictions)

    def prediciotns_repeat(self, lstm_model):

        # # forecast the entire training dataset to build up state for forecasting - ???????
        # train_reshaped = self.train_scaled[:, 0].reshape(len(self.train_scaled), 1, 1)
        # lstm_model.predict(train_reshaped, batch_size=1)

        # walk-forward validation on the test data
        predictions = list()
        for i in range(len(self.test_scaled)):
            # make one-step forecast
            X, y = self.test_scaled[i, 0:-1], self.test_scaled[i, -1]
            yhat = self.forecast_lstm(lstm_model, 1, X)
            # invert scaling
            yhat = self.invert_scale(self.scaler, X, yhat)
            # invert differencing
            yhat = self.inverse_difference(self.raw_values, yhat, len(self.test_scaled) + 1 - i)
            # store forecast
            predictions.append(yhat)
            expected = self.raw_values[len(self.train) + i + 1]
            # print('Month=%d, Predicted=%f, Expected=%f' % (i + 1, yhat, expected))

        # report performance
        rmse = sqrt(mean_squared_error(self.raw_values[-self.sv_len:].values.tolist(), predictions))
        # print('Test RMSE: %.3f' % rmse)

        # line plot of observed vs predicted
        # pyplot.plot(raw_values[-sv_len:])
        # pyplot.plot(predictions)
        # pyplot.show()

        return predictions, rmse


class NeuralNetworkTeacher(QtCore.QThread):
    signal_epoch = QtCore.pyqtSignal(int)
    signal_repeat = QtCore.pyqtSignal(int, Predictions)
    signal_complete = QtCore.pyqtSignal()

    def __init__(self, neural_network: NeuralNetwork, parent=None):
        super().__init__(parent)
        self.neural_network = neural_network

    def run(self):
        self.neural_network.make_multi_predictions(lambda i, predictions: self.signal_repeat.emit(i, predictions),
                                                   lambda i: self.signal_epoch.emit(i))
        self.signal_complete.emit()
