import os
import hashlib
from flask import Flask, request, send_file
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restx import Api, Resource

app = Flask(__name__)
auth = HTTPBasicAuth()

UPLOAD_FOLDER = 'store'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

users = {
    "user1": generate_password_hash("password1"),
    "user2": generate_password_hash("password2")
}

api = Api(app, doc='/swagger')

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

def calculate_file_hash(file):
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_path(file_hash):
    subfolder = file_hash[:2]
    return os.path.join(app.config['UPLOAD_FOLDER'], subfolder, file_hash)

@api.route('/upload')
class Upload(Resource):
    @auth.login_required
    @api.response(200, 'File uploaded successfully')
    @api.response(400, 'No file part or no selected file')
    def post(self):
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400

        file_hash = calculate_file_hash(file)
        file.seek(0)

        subfolder = file_hash[:2]
        path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(path, exist_ok=True)

        file.save(get_file_path(file_hash))
        return file_hash, 200

@api.route('/delete/<string:file_hash>')
class Delete(Resource):
    @auth.login_required
    @api.response(200, 'File deleted successfully')
    @api.response(404, 'File not found')
    def delete(self, file_hash):
        file_path = get_file_path(file_hash)
        if os.path.exists(file_path):
            os.remove(file_path)
            return 'File deleted', 200
        else:
            return 'File not found', 404

@api.route('/download/<string:file_hash>')
class Download(Resource):
    @api.response(200, 'File downloaded successfully')
    @api.response(404, 'File not found')
    def get(self, file_hash):
        file_path = get_file_path(file_hash)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return 'File not found', 404

if __name__ == '__main__':
    app.run()
