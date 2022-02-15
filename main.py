from flask import Flask, jsonify
import boat
import load
import jwt

app = Flask(__name__)
app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
app.register_blueprint(jwt.bp)

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'Error': '405 Method Not Allowed'}), 405

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)