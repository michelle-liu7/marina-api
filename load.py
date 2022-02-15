from flask import Blueprint, request
from google.cloud import datastore
import constants

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')

@bp.route('', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        if "application/json" in request.accept_mimetypes:
            content = request.get_json()
            if {"volume", "content", "creation_date"} <= content.keys():
                new_load = datastore.entity.Entity(key=client.key(constants.loads))
                new_load.update({"volume": content["volume"], "content": content["content"], "creation_date": content["creation_date"], "carrier": None})
                client.put(new_load)
                new_load["id"] = new_load.key.id
                new_load["self"] = request.host_url + "loads/" + str(new_load.key.id)
                return new_load, 201
            else:
                return {"Error": "The request object is missing at least one of the required attributes"}, 400
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406
    elif request.method == 'GET':
        if "application/json" in request.accept_mimetypes:
            query = client.query(kind=constants.loads)
            total_results = list(query.fetch())
            q_limit = int(request.args.get('limit', '5'))
            q_offset = int(request.args.get('offset', '0'))
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
                e["self"] = request.host_url + "loads/" + str(e.key.id)
                if e["carrier"]:
                    e["carrier"] = {"id": e["carrier"], "self": request.host_url + "boats/" + str(e["carrier"])}
            output = {"loads": results, "total_items": len(total_results)}
            if next_url:
                output["next"] = next_url
            return output, 200
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406

@bp.route('/<id>', methods=['GET','DELETE', 'PATCH', 'PUT'])
def load_get_delete(id):
    load_key = client.key(constants.loads, int(id))
    load = client.get(key=load_key)
    if request.method == 'GET':
        if "application/json" in request.accept_mimetypes:
            if load:
                load["id"] = load.key.id
                load["self"] = request.host_url + "loads/" + str(load.key.id)
                if load["carrier"]:
                    boat_key = client.key(constants.boats, load["carrier"])
                    boat = client.get(key=boat_key)
                    load["carrier"] = {"id": load["carrier"], "name": boat["name"],"self": request.host_url + "boats/" + str(load["carrier"])}
                return load, 200
            else:
                return {"Error": "No load with this load_id exists"}, 404
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406
    elif request.method == 'DELETE':
        if load:
            if load["carrier"]:
                boat_key = client.key(constants.boats, load["carrier"])
                boat = client.get(key=boat_key)
                boat["loads"].remove(int(id))
                client.put(boat)
            client.delete(load_key)
            return '', 204
        else:
            return {"Error": "No load with this load_id exists"}, 404
    elif request.method == 'PUT':
        if "application/json" in request.accept_mimetypes:
            if load:
                content = request.get_json()
                if {"volume", "content", "creation_date"} <= content.keys():
                    load.update({"volume": content["volume"], "content": content["content"], "creation_date": content["creation_date"]})
                    client.put(load)
                    load["id"] = load.key.id
                    load["self"] = request.host_url + "loads/" + str(load.key.id)
                    if load["carrier"]:
                        load["carrier"] = {"id": load["carrier"], "self": request.host_url + "boats/" + str(load["carrier"])}
                    return load, 200
                else:
                    return {"Error": "The request object is missing at least one of the required attributes"}, 400
            else:
                return {"Error": "No load with this load_id exists"}, 404
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406
    elif request.method == 'PATCH':
        if "application/json" in request.accept_mimetypes:
            if load:
                content = request.get_json()
                attr_to_be_updated = {"volume", "content", "creation_date"}.intersection(set(content.keys()))
                if attr_to_be_updated:
                    for attr in attr_to_be_updated:
                        load[attr] = content[attr]
                    client.put(load)
                    load["id"] = load.key.id
                    load["self"] = request.host_url + "loads/" + str(load.key.id)
                    if load["carrier"]:
                        load["carrier"] = {"id": load["carrier"], "self": request.host_url + "boats/" + str(load["carrier"])}
                    return load, 200
                else:
                    return {"Error": "The request object does not contain any of the valid attributes"}, 400
            else:
                return {"Error": "No load with this load_id exists"}, 404
        else:
            return {"Error": "Please verify the accept header. The server only offers response in JSON"}, 406
