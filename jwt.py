from google.cloud import datastore
import flask
import requests
from flask import Flask, render_template, request, Blueprint, jsonify
import random
import string
import json
import os

client = datastore.Client()

bp = Blueprint('boat', __name__, template_folder='templates')

with open(os.path.dirname(os.path.realpath(__file__)) + '/client_secret.json') as f:
   data = json.load(f)

CLIENT_ID = data["web"]["client_id"]
CLIENT_SECRET = data["web"]["client_secret"]
SCOPE = 'profile'
REDIRECT_URI = 'https://liumiche-portfolio.wl.r.appspot.com/oauth'


@bp.route('/')
def index():
  return render_template("welcome.html", link = request.base_url + "/oauth")


@bp.route('/oauth')
def oauth():
  if 'code' not in flask.request.args:
    state = generate_random_state()
    query = client.query(kind="state")
    result = list(query.fetch())  
    if result:
      result[0]["state"] = state
      client.put(result[0])
    else:
      new_state = datastore.entity.Entity(key=client.key("state"))
      new_state.update({"state": state})
      client.put(new_state)
    auth_uri = ('https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
                '&client_id={}&redirect_uri={}&scope={}&state={}').format(CLIENT_ID, REDIRECT_URI, SCOPE, state)
    return flask.redirect(auth_uri)
  else:
    auth_code = flask.request.args.get('code')
    state_returned = flask.request.args.get('state')
    query = client.query(kind="state")
    result = list(query.fetch())  
    if state_returned == result[0]["state"]:
      data = {'code': auth_code,
              'client_id': CLIENT_ID,
              'client_secret': CLIENT_SECRET,
              'redirect_uri': REDIRECT_URI,
              'grant_type': 'authorization_code'}
      r = requests.post('https://oauth2.googleapis.com/token', data=data)
      id_token = r.json()["id_token"]
      query = client.query(kind="id_token")
      result = list(query.fetch())
      if result:
        result[0]["id_token"] = id_token
        client.put(result[0])
      else:
        new_id_token = datastore.entity.Entity(key=client.key("id_token"))
        new_id_token.update({"id_token": id_token})
        client.put(new_id_token)
    return flask.redirect(flask.url_for('.user_info'))

@bp.route('/user_info')
def user_info():
  query = client.query(kind="id_token")
  id_token = list(query.fetch())[0]["id_token"]
  jwt = verify_JWT(id_token)
  user_id = jwt["sub"]
  first_name = jwt["given_name"]
  last_name = jwt["family_name"]
  query = client.query(kind="users")
  query.add_filter("user_id", "=", user_id)
  result = list(query.fetch())
  if not result:
    new_user = datastore.entity.Entity(key=client.key("users"))
    new_user.update({"first_name": first_name, "last_name": last_name, "user_id": user_id})
    client.put(new_user)
  result = {"id_token": id_token, "user_id": user_id}
  return render_template("user_info.html", result = result)

@bp.route('/users', methods=['GET'])
def get_users():
  if request.method == 'GET':
    query = client.query(kind="users")
    results = list(query.fetch())
    for u in results:
      u["id"] = u.key.id
    return jsonify(results), 200 

def generate_random_state():
  return ''.join(random.choices(string.ascii_letters + string.digits, k = 8))

def verify_JWT(jwt):
    r = requests.post('https://oauth2.googleapis.com/tokeninfo', params={"id_token": jwt})
    if r.status_code == 200:
        return r.json()
    else:
        return None