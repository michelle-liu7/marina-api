from flask import Blueprint, request
from google.cloud import datastore
import constants
import requests

client = datastore.Client()

bp = Blueprint('boats', __name__, url_prefix='/boats')

@bp.route('', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        if "application/json" in request.accept_mimetypes:
            if "Authorization" in request.headers:
                id_token = request.headers.get("Authorization").split()[1]
                id_token = verify_JWT(id_token)
                if id_token:
                    content = request.get_json()
                    if {"name", "type", "length"} <= content.keys():
                        new_boat = datastore.entity.Entity(key=client.key(constants.boats))
                        new_boat.update({"name": content["name"], "type": content["type"], "length": content["length"], "loads": [], "owner": id_token["sub"]})
                        client.put(new_boat)
                        new_boat["id"] = new_boat.key.id
                        new_boat["self"] = request.host_url + "boats/" + str(new_boat.key.id)
                        return new_boat, 201
                    else:
                        return {"Error": "The request object is missing at least one of the required attributes"}, 400
                else:
                    return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
            else:
                return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406
    elif request.method == 'GET':
        if "application/json" in request.accept_mimetypes:
            if "Authorization" in request.headers:
                id_token = request.headers.get("Authorization").split()[1]
                id_token = verify_JWT(id_token)
                if id_token:
                    query = client.query(kind=constants.boats)
                    q_limit = int(request.args.get('limit', '5'))
                    q_offset = int(request.args.get('offset', '0'))
                    query.add_filter("owner", "=", id_token["sub"])
                    total_results = list(query.fetch())
                    g_iterator = query.fetch(limit= q_limit, offset=q_offset)
                    pages = g_iterator.pages
                    results = list(next(pages))
                    if g_iterator.next_page_token:
                        next_offset = q_offset + q_limit
                        next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
                    else:
                        next_url = None
                    for e in results:
                        e["id"] = e.key.id
                        e["self"] = request.host_url + "boats/" + str(e.key.id)
                        if e["loads"]:
                            loads = []
                            for l in e["loads"]:
                                loads.append({"id": l, "self": request.host_url + "loads/" + str(l)})
                            e["loads"] = loads
                    output = {"boats": results, "total_items": len(total_results)}
                    if next_url:
                        output["next"] = next_url
                    return output, 200
                else:
                    return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401    
            else:
                return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406

@bp.route('/<id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def boat_get_update_delete(id):
    boat_key = client.key(constants.boats, int(id))
    boat = client.get(key=boat_key)
    if request.method == 'GET':
        if "application/json" in request.accept_mimetypes:
            if "Authorization" in request.headers:
                id_token = request.headers.get("Authorization").split()[1]
                id_token = verify_JWT(id_token)
                if id_token:
                    if boat and (boat["owner"] == id_token["sub"]):
                        boat["id"] = boat.key.id
                        boat["self"] = request.host_url + "boats/" + str(boat.key.id)
                        loads = []
                        for l in boat["loads"]:
                            loads.append({"id": l, "self": request.host_url + "loads/" + str(l)})
                        boat["loads"] = loads
                        return boat, 200
                    else:
                        return {"Error": "The boat is owned by someone else or no boat with this boat_id exists"}, 403
                else:
                    return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401    
            else:
                return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406
    elif request.method == 'DELETE':
        if "Authorization" in request.headers:
            id_token = request.headers.get("Authorization").split()[1]
            id_token = verify_JWT(id_token)
            if id_token:
                if boat and (boat["owner"] == id_token["sub"]):
                    for l in boat["loads"]:
                        load_key = client.key(constants.loads, l)
                        load = client.get(key=load_key)
                        load["carrier"] = None
                        client.put(load)
                    client.delete(boat_key)
                    return '', 204
                else:
                    return {"Error": "The boat is owned by someone else or no boat with this boat_id exists"}, 403
            else:
                return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
        else:
            return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
    elif request.method == 'PUT':
        if "application/json" in request.accept_mimetypes:
            if "Authorization" in request.headers:
                id_token = request.headers.get("Authorization").split()[1]
                id_token = verify_JWT(id_token)
                if id_token:
                    if boat and (boat["owner"] == id_token["sub"]):
                        content = request.get_json()
                        if {"name", "type", "length"} <= content.keys():
                            boat.update({"name": content["name"], "type": content["type"], "length": content["length"]})
                            client.put(boat)
                            boat["id"] = boat.key.id
                            boat["self"] = request.host_url + "boats/" + str(boat.key.id)
                            del boat["loads"]
                            return boat, 200
                        else:
                            return {"Error": "The request object is missing at least one of the required attributes"}, 400
                    else:
                        return {"Error": "The boat is owned by someone else or no boat with this boat_id exists"}, 403
                else:
                    return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
            else:
                return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406
    elif request.method == 'PATCH':
        if "application/json" in request.accept_mimetypes:
            if "Authorization" in request.headers:
                id_token = request.headers.get("Authorization").split()[1]
                id_token = verify_JWT(id_token)
                if id_token:
                    if boat and (boat["owner"] == id_token["sub"]):
                        content = request.get_json()
                        attr_to_be_updated = {"name", "type", "length"}.intersection(set(content.keys()))
                        if len(attr_to_be_updated) > 0:
                            for attr in attr_to_be_updated:
                                boat[attr] = content[attr]
                            client.put(boat)
                            boat["id"] = boat.key.id
                            boat["self"] = request.host_url + "boats/" + str(boat.key.id)
                            del boat["loads"]
                            return boat, 200
                        else:
                            return {"Error": "The request object does not contain any of the valid attributes"}, 400
                    else:
                        return {"Error": "The boat is owned by someone else or no boat with this boat_id exists"}, 403
                else:
                    return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
            else:
                return {"Error": "The request is missing a valid JWT or contains an invalid JWT"}, 401
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406

@bp.route('/<boat_id>/loads/<load_id>', methods=['PUT','DELETE'])
def add_delete_load(boat_id, load_id):
    boat_key = client.key(constants.boats, int(boat_id))
    boat = client.get(key=boat_key)
    load_key = client.key(constants.loads, int(load_id))
    load = client.get(key=load_key)
    if request.method == 'PUT':
        if boat and load and load["carrier"] is None:
            boat["loads"].append(int(load_id))
            load["carrier"] = int(boat_id)
            client.put_multi([boat, load])
            return "", 204
        elif boat and load and load["carrier"]:
            return {"Error": "The load is already loaded on another boat"}, 403
        else:
            return {"Error": "The specified boat and/or load does not exist"}, 404
    if request.method == 'DELETE':
        if boat and load and (int(load_id) in boat["loads"]):
            boat["loads"].remove(int(load_id))
            load["carrier"] = None
            client.put_multi([boat, load])
            return "", 204
        else:
            return {"Error": "No boat with this boat_id is loaded with the load with this load_id"}, 404

def verify_JWT(jwt):
    r = requests.post('https://oauth2.googleapis.com/tokeninfo', params={"id_token": jwt})
    if r.status_code == 200:
        return r.json()
    else:
        return None