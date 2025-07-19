import json
from time import sleep

from visualizacao_de_dados.api import get_main_data

while True:
    data = get_main_data()
    json.dump(data, open('result.json', 'w'))
    sleep(30 * 60)
