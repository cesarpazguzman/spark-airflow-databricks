from flask import Flask
from flask_restful import Api, Resource, reqparse
import joblib
import numpy as np
from pandas import to_datetime
from pandas import DataFrame

print("Flask")
APP = Flask(__name__)
API = Api(APP)



class Predict(Resource):

    @staticmethod
    def post():
        print("Entra")
        parser = reqparse.RequestParser()
        parser.add_argument('date')
        parser.add_argument('store')
        parser.add_argument('item')

        args = parser.parse_args()

        model = joblib.load('/app/modelos/modelo_entrenado_{0}_{1}.pickle'.format(args['store'],args['item']))

        future = list()
        future.append([args['date']])
        future = DataFrame(future)
        future.columns = ['ds']
        future['ds']= to_datetime(future['ds'])

        forecast = model.predict(future)

        out = {'yhat': forecast["yhat"].iloc[0], 'yhat_lower': forecast["yhat_lower"].iloc[0],
            'yhat_upper': forecast["yhat_upper"].iloc[0]}

        return out, 200

API.add_resource(Predict, '/predict') #endpoint predict

if __name__ == '__main__':
    print("Empieza")
    APP.run(debug=True, port='1080', host='0.0.0.0')