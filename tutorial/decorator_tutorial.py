def wrapper_function(func):
    def decorated_function():
        print("A")
        func()
        print("C")
    return decorated_function

def basic_function():
    print("B")


new_function = wrapper_function(basic_function)
new_function()
