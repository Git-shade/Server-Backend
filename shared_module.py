my_variable = None 

def set_variable(value):
    global my_variable
    my_variable = value

def get_variable():
    return my_variable