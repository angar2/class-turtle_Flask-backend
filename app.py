import json
from flask import Flask, jsonify, request
from flask_cors import CORS


app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})

@app.route("/")
def hello_world():
    return jsonify({'msg': 'success'})


@app.route("/signup", methods=["POST"])
def sign_up():
    
    # 요청 형식이 'form-data'일 경우 출력법
    # print(request.form.get('id')) # 입력값에 'id'가 없으면 서버에러가 발생하지만 get()을 사용하면 none을 출력해줌.
    
    # 요청 형식이 'raw'일 경우 출력법
    data = json.loads(request.data)
    print(data.get('email'))
    print(data.get('pw'))


    return jsonify({'msg': 'success'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)