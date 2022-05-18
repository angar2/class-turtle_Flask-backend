from datetime import datetime, timedelta
import hashlib
import json
from bson import ObjectId
from flask import Flask, jsonify, request
from flask_cors import CORS
import jwt
from pymongo import MongoClient

SECRET_KEY = 'turtle' # token 생성 시 사용

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
client = MongoClient('localhost', 27017)
db = client.turtlegram

@app.route("/")
def hello_world():
    return jsonify({'msg': 'success'})


# 회원가입
@app.route("/signup", methods=["POST"])
def sign_up():
    
    # 요청 형식이 'form-data'일 경우 출력법
    # print(request.form.get('id')) # 입력값에 'id'가 없으면 서버에러가 발생하지만 get()을 사용하면 none을 출력해줌.
    
    # 요청 형식이 'raw'일 경우 출력법
    data = json.loads(request.data)
    # print(data.get('email'))
    # print(data.get('password'))

    email = data.get("email")
    password = data.get('password', None)
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    doc = {
        'email': email,
        'password': hashed_password
    }
    user = db.users.insert_one(doc)

    return jsonify({'msg': 'success'})


# 로그인
@app.route("/login", methods=["POST"])
def login():
    data = json.loads(request.data)

    email = data.get("email")
    password = data.get("password")
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    result = db.users.find_one({
        'email': email,
        'password': hashed_password
    })

    if result is None:
        return jsonify({"message": "일치하는 회원정보가 없습니다."})

    payload = {
        'id': str(result['_id']),
        'exp': datetime.utcnow() + timedelta(seconds = 60 * 60 * 24)  # 유지시간 = 초 * 분 * 시간
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return jsonify({"message": "success", "token": token})


# 유저 이름 가져오기
@app.route("/getuserinfo", methods=["GET"])
def get_user_info():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"message": "no token"}), 402

    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256']) # 로그인 당시 만들었던 'payload' 객체를 반환
    result = db.users.find_one({
        '_id': ObjectId(payload["id"]) # DBmongo에서 objectId를 가져오기 위한 방법(pymongo와 함께 설치되는 bson의 'ObjectId()')
    })
    
    return jsonify({"message": "success", "email": result["email"]})
    

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)