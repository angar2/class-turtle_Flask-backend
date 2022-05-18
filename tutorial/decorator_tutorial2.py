def wrapper_function(func):
    def decorated_function():
        print("A")
        func()
        print("C")
    return decorated_function

@wrapper_function # wrapper_function()에 인자로 basic_function를 넣어준 것과 같은 효과
def basic_function():
    print("B")

basic_function()
