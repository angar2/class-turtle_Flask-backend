from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
from bson import ObjectId
from flask import Flask, abort, jsonify, request
from flask_cors import CORS
import jwt
from pymongo import MongoClient

SECRET_KEY = 'turtle' # token 생성 시 사용

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
client = MongoClient('localhost', 27017)
db = client.turtlegram


def authorize(f):
    @wraps(f) # decorator 함수인 'authorize()'를 여러 함수에서 사용하기 위함(import 필요)
    def decorated_function():
        if not 'Authorization' in request.headers:
            abort(401) # 중단(import 해야함)
        token = request.headers['Authorization']
        try:
            user = jwt.decode(token, SECRET_KEY, algorithms = ['HS256']) # 로그인 당시 만들었던 'payload' 객체를 반환
        except:
            abort(401)
        return f(user)
    return decorated_function


@app.route("/")
@authorize
def hello_world(user):
    print(user)
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
@authorize
def get_user_info(user):
    # token = request.headers.get("Authorization")

    # if not token:
    #     return jsonify({"message": "no token"}), 402

    # user = jwt.decode(token, SECRET_KEY, algorithms=['HS256']) # 로그인 당시 만들었던 'payload' 객체를 반환
    result = db.users.find_one({
        '_id': ObjectId(user["id"]) # DBmongo에서 objectId를 가져오기 위한 방법(pymongo와 함께 설치되는 bson의 'ObjectId()')
    })
    
    return jsonify({"message": "success", "email": result["email"]})


# 게시물 업로드
@app.route("/article", methods=["POST"])
@authorize
def post_article(user):
    data = json.loads(request.data)

    result = db.users.find_one({
        '_id': ObjectId(user["id"]) # DBmongo에서 objectId를 가져오기 위한 방법(pymongo와 함께 설치되는 bson의 'ObjectId()')
    })
    now = datetime.now().strftime("%H:%M:%S") # strftime: 해당 format code에 기초한 formatted string을 리턴함

    doc = {
        'title': data.get('title', None), # None: 값이 없으면 None값으로 처리함
        'content': data.get('content', None),
        'user_id': user['id'],
        'user_email': result['email'],
        'time': now,
    }
    db.articles.insert_one(doc)

    return jsonify({"message": "success"})


# 게시물 불러오기
@app.route("/article", methods=["GET"])
def get_article():
    articles = list(db.articles.find())
    for article in articles:
        article["_id"] = str(article["_id"]) # objectId을 읽을 수 있는 값으로 변환

    return jsonify({"message": "success", "articles": articles})


# 특정 게시물 불러오기
@app.route("/article/<article_id>", methods=["GET"]) # 변수명으로 url을 받음
def get_article_detail(article_id):
    article = db.articles.find_one({"_id": ObjectId(article_id)})
    article["_id"] = str(article["_id"])

    return jsonify({"message": "success", "article": article})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)