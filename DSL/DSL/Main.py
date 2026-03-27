from src import *
import sys
import logging
import sqlite3

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(levelname)s: [%(name)s] %(message)s'
# )


def select_rand_number():
    conn = sqlite3.connect('data/random_users.db')
    cur = conn.cursor()
    cur.execute("SELECT number FROM users ORDER BY RANDOM() LIMIT 1")
    number = cur.fetchone()[0]
    conn.close()
    return number

def welcome():
    str = input("模拟用户通话:")
    return str != '退出'

if __name__ == '__main__':
    conf = ConfigLoader('./config.yaml')

    interpreter = Interpreter(conf)


    while True:
        if not welcome():
            break
        number = select_rand_number()
        runtime = Command(number, conf)
        interpreter.accept(runtime)
