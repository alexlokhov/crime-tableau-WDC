from flask import Flask
from flask import request

import requests
import json
import datetime
import dateutil.relativedelta

application = Flask(__name__)

@application.route('/', methods=['GET'])
def main_thread ():
  postcode = request.args.get('postcode','')
  months = int(request.args.get('months',''))
  coords = geocode (postcode)
  police_session = requests.session()
  today = datetime.datetime.now()
  results = []
  for n in range(1, months+1):
    d = today - dateutil.relativedelta.relativedelta(months = n)
    d_string = d.strftime('%Y-%m')
    results.extend (fetch_data(police_session, d_string, coords, results))
  results_t = transform_tableau(results)
  response = application.make_response(json.dumps(results_t))
  response.mimetype = ('application/json')
  response.headers.add('Access-Control-Allow-Origin', '*')
  return response

def geocode (postcode):
  geocode_session = requests.session()
  r = geocode_session.get('http://maps.googleapis.com/maps/api/geocode/json?address=' + postcode)
  response = json.loads(r.text)
  coords = {}
  coords = response['results'][0]['geometry']['location']
  return coords

def fetch_data (police_session, d_string, coords, results):
  payload = {
    'date': d_string,
    'lat': coords['lat'],
    'lng': coords['lng']
  }
  try:
    r = police_session.get('https://data.police.uk/api/crimes-street/all-crime', params = payload)
    return json.loads(r.text)
  except:
    return ('Error')

def transform_tableau (records):
  records_t = []
  for record in records:
    record_t = {
      'Category': record['category'],
      'Context': record['context'],
      'Id': record['id'],
      'Latitude': record['location']['latitude'],
      'Longitude': record['location']['longitude'],
      'Street id': record['location']['street']['id'],
      'Street Name': record['location']['street']['name'],
      'Location Subtype': record['location_subtype'],
      'Location Type' : record['location_type'],
      'Persistent id' : record['persistent_id']
    }
    if record['outcome_status'] is not None:
      record_t['Outcome Status'] = record['outcome_status']['category']
    d = datetime.datetime.strptime(record['month'],'%Y-%m')
    record_t['Month'] = d.strftime('%d/%m/%Y')
    records_t.append(record_t)
  return records_t

if __name__ == "__main__":
  application.run(host='0.0.0.0', debug=True)
