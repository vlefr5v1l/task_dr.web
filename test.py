import pytest
from io import BytesIO
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers():
    return {
        'Authorization': 'Basic dXNlcjI6cGFzc3dvcmQy'
    }

def test_upload_file(client, auth_headers):
    data = {
        'file': (BytesIO(b"test123"), 'test.txt')
    }
    response = client.post('/upload', data=data, headers=auth_headers, content_type='multipart/form-data')
    assert response.status_code == 200
    file_hash = response.get_data(as_text=True)
    assert file_hash.strip() == '"ecd71870d1963316a97e3ac3408c9835ad8cf0f3c1bc703527c30265534f75ae"'

def test_upload_file_no_auth(client):
    data = {
        'file': (BytesIO(b"test123"), 'test.txt')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 401

def test_download_file(client, auth_headers):
    data = {
        'file': (BytesIO(b"test123"), 'test.txt')
    }
    response = client.post('/upload', data=data, headers=auth_headers, content_type='multipart/form-data')
    assert response.status_code == 200
    file_hash = response.get_data(as_text=True).strip()

    response = client.get(f'/download/{file_hash[1:len(file_hash)-1]}')
    assert response.status_code == 200
    assert response.data == b"test123"

def test_download_file_not_found(client):
    response = client.get('/download/invalidhash')
    assert response.status_code == 404

def test_delete_file(client, auth_headers):
    data = {
        'file': (BytesIO(b"test123"), 'test.txt')
    }
    response = client.post('/upload', data=data, headers=auth_headers, content_type='multipart/form-data')
    assert response.status_code == 200
    file_hash = response.get_data(as_text=True).strip()

    response = client.delete(f'/delete/{file_hash[1:len(file_hash)-1]}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_data(as_text=True).strip() == '"File deleted"'

def test_delete_file_not_found(client, auth_headers):
    response = client.delete('/delete/no_name_file', headers=auth_headers)
    assert response.status_code == 404
    assert response.get_data(as_text=True).strip() == '"File not found"'
