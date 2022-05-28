from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json
from bson import ObjectId
from flask import Flask, abort, jsonify, request
from flask_cors import CORS
import jwt
from pymongo import MongoClient
from bson.json_util import loads, dumps

SECRET_KEY = 'turtle' # token 생성 시 사용

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
client = MongoClient('localhost', 27017)
db = client.turtlegram


def authorize(f):
    @wraps(f) # decorator 함수인 'authorize()'를 여러 함수에서 사용하기 위함(import 필요)
    # *(argumants): 가변인자를 위한 변수로서 함수에 인자를 몇 개 받을지 모르는 경우 list형태로 인자를 얼마든지 담아줌
    # **(keyword argumants): '*'와 마찬가지로 가변인자를 받으며 Key와 value의 dic형태로 담아줌
    def decorated_function(*args, **kwargs): 
        if not 'Authorization' in request.headers:
            abort(401) # 중단(import 해야함)
        token = request.headers['Authorization']
        try:
            user = jwt.decode(token, SECRET_KEY, algorithms = ['HS256']) # 로그인 당시 만들었던 'payload' 객체를 반환
        except:
            abort(401)
        return f(user, *args, **kwargs)
    return decorated_function


@app.route("/")
@authorize
def hello_world(user):
    # print(user)
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
    result = db.users.find_one({
        '_id': ObjectId(user["id"]) # DBmongo에서 objectId를 가져오기 위한 방법(pymongo와 함께 설치되는 bson의 'ObjectId()')
    })
    
    return jsonify({"message": "success", "email": result["email"], "id": user["id"]})


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


# 전체 게시물 데이터 불러오기
@app.route("/article", methods=["GET"])
def get_article():
    articles = list(db.articles.find())
    for article in articles:
        article["_id"] = str(article["_id"]) # objectId을 읽을 수 있는 값으로 변환(json으로 넘기기 위해선 필수)

    return jsonify({"message": "success", "articles": articles})


# 특정 게시물 데이터 불러오기
@app.route("/article/<article_id>", methods=["GET"]) # 변수명으로 url을 받음
def get_article_detail(article_id):
    article = db.articles.find_one({"_id": ObjectId(article_id)})
    comments = list(db.comments.find({"article_id": article_id})) # 해당 article에 달린 comment들을 articles에 담아서 한번에 보내주고자 함
    likes = list(db.likes.find({"article_id": article_id})) # 해당 article에 달린 liks의 개수를 articles에 담아서 한번에 보내주고자 함
    if article:
        article["_id"] = str(article["_id"])
        article["comments"] = json.loads(dumps(comments)) # dumps: ObjectId를 json 형식으로 만드는 방법 중 하나
        article["likes_count"] = len(likes) # likes의 개수를 추가
        return jsonify({"message": "success", "article": article})
    else:
        return jsonify({"message": "fail"}), 404 # else도 결국 성공임으로 'status:200'을 보여줄 것이기에 'status:404'을 띄워줌  


# 게시글 수정
@app.route("/article/<article_id>", methods=["PATCH"])
@authorize
def patch_article_detail(user, article_id):
    data = json.loads(request.data)
    title = data.get("title")
    content = data.get("content")

    article = db.articles.update_one({"_id": ObjectId(article_id), "user_id": user["id"]}, {
        "$set": {"title": title, "content": content}
    })

    # print(article.matched_count) # matched_count: doc의 개수를 검색하는 기능(업데이트 성공할 경우: 1, 성공하지 못할 경우: 0 

    if article.matched_count:
        return jsonify({"message": "success"})
    else:
        return jsonify({"message": "fail"}), 403 # else도 결국 성공임으로 'status:200'을 보여줄 것이기에 'status:403'을 띄워줌


# 게시글 삭제
@app.route("/article/<article_id>", methods=["DELETE"])
@authorize
def delete_article_detail(user, article_id):

    article = db.articles.delete_one({"_id": ObjectId(article_id), "user_id": user["id"]})

    # print(article.deleted_count) # deleted_count: doc의 삭제된 개수를 검색하는 기능(삭제에 성공할 경우: 1, 성공하지 못할 경우: 0 

    if article.deleted_count:
        return jsonify({"message": "success"})
    else:
        return jsonify({"message": "fail"}), 403 # else도 결국 성공임으로 'status:200'을 보여줄 것이기에 'status:403'을 띄워줌


# 댓글 작성
@app.route("/article/<article_id>/comment", methods=["POST"])
@authorize
def post_comment(user, article_id):
    data = json.loads(request.data)
    db_user = db.users.find_one({"_id": ObjectId(user.get('id'))})
    now = datetime.now().strftime("%H:%M:%S")

    doc = {
        'article_id': article_id,
        'content': data.get('content', None),
        'user_id': user['id'],
        'user_email': db_user['email'],
        'time': now
    }

    db.comments.insert_one(doc)

    return jsonify({"message": "success"})


# 댓글 불러오기
@app.route("/article/<article_id>/comment", methods=["GET"])
def get_comment(article_id):
    comments = list(db.comment.find({"article_id": article_id}))
    json_comments = json.loads(dumps(comments))
    return jsonify({"message": "success", "comments": json_comments})


# 좋아요 올리기
@app.route("/article/<article_id>/like", methods=["POST"])
@authorize
def post_like(user, article_id):
    db_user = db.users.find_one({'_id':ObjectId(user.get('id'))})
    print(article_id)
    now = datetime.now().strftime("%H:%M:%S")

    doc = {
        'article_id': article_id,
        'user_id': user['id'],
        'user_email': db_user['email'],
        'time': now
    }
    db.likes.insert_one(doc)

    return jsonify({"message": "success"})


# 좋아요 취소하기
@app.route("/article/<article_id>/like", methods=["DELETE"])
@authorize
def delete_like(user, article_id):
    result = db.likes.delete_one({"article_id": article_id, "user_id": user['id']})
    
    if result.deleted_count:
        return jsonify({"message": "success"})
    else:
        return jsonify({"message": "fail"}), 400


# 좋아요 불러오기(해당 유저의 좋아요 여부 체크)
@app.route("/article/<article_id>/like", methods=["GET"])
@authorize
def get_like(user, article_id):
    result = db.likes.find_one({"article_id": article_id, "user_id": user['id']})
    
    if result:
        return jsonify({"message": "success", "liked": True})
    else:
        return jsonify({"message": "fail", "liked": False})


# 유저 데이터 불러오기
@app.route("/user/<user_id>", methods=["GET"])
def user_protile(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)}, {"password": False})
    user_articles = list(db.articles.find({"user_id": user_id}))
    user['articles'] = user_articles # 유저 정보에 해당 유저가 작성한 게시글 추가
    user = json.loads(dumps(user)) # 유저의 ObjectId를 응답할 수 있도록 함

    return jsonify({"messege": "success", "user": user})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)