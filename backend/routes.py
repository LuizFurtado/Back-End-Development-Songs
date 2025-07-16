from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health")
def check_health():
    return {"status":"ok"}, 200

@app.route("/count")
def count():
    try:
        songs = db.songs.find({})
        count = len(list(songs))
        return {"count": count}, 200
    except Exception as error:
        return {"error": str(error)}, 500

@app.route("/song", methods=["GET"])
def songs():
    try:
        songs = db.songs.find()
        response_body = json_util.dumps({"songs": list(songs)})
        response = make_response(response_body, 200)
        response.headers["Content-Type"] = "application/json"
        return response
    except Exception as error:
        return {"error": str(error)}, 500

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        song = db.songs.find_one({"id":id})
        if song is None:
            return {"message": f"song with id {id} not found"}, 404
        response = make_response(json_util.dumps(song), 200)
        response.headers["Content-Type"] = "application/json"
        return response
    except Exception as error:
        return {"error": str(error)}, 500

@app.route("/song", methods=["POST"])
def create_song():
    song = request.json
    try:
        song_result=db.songs.find_one({"id":song["id"]})
        if song_result:
            return {"message": f"song with id {song['id']} already present"}, 302
        result = db.songs.insert_one(song)
        inserted_id = {"$oid": str(result.inserted_id)}
        response_body = {"inserted id": inserted_id}
        response = make_response(json.dumps(response_body), 200)
        response.headers["Content-Type"] = "application/json"
        return response
    except Exception as error:
        return {"error": str(error)}, 500

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        updated_data = request.json
        song = db.songs.find_one({"id": id})

        if song is None:
            return {"message": "song not found"}, 404

        result = db.songs.update_one(
            {"id": id},
            {"$set": updated_data}
        )

        if result.modified_count == 0:
            return {"message": "song found, but nothing updated"}, 200

        updated_song = db.songs.find_one({"id": id})
        response_body = json_util.dumps(updated_song)
        response = make_response(response_body, 201)
        response.headers["Content-Type"] = "application/json"
        return response

    except Exception as error:
        return {"error": str(error)}, 500

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    try:
        result = db.songs.delete_one({"id": id})

        if result.deleted_count == 0:
            return {"message": "song not found"}, 404

        response = make_response('', 204)
        return response

    except Exception as error:
        return {"error": str(error)}, 500


        
        