import logging
def user_input_receiever(user_input:str)->str:
    if not user_input:
        logging.error("no input came in ")
    return user_input