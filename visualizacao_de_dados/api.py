from httpx import get

from visualizacao_de_dados.config import config


def get_data(endpoint):
    try:
        return get(
            f'https://olivar.foccoerp.com.br/FoccoIntegrador/api/v1/Exportacao/{endpoint}',
            headers={
                'Authorization': f'Bearer {config["TOKEN"]}',
            },
            params={'Chave': config['KEY']},
            timeout=10000,
        ).json()['value']
    except KeyError:
        return get_data(endpoint)


def get_volume_data():
    return get_data('dados_volumes')


def get_stock_data():
    return get_data('dados_estoque')


def get_order_data():
    return get_data('dados_ordens')


def get_pdv_data():
    return get_data('dados_pdv')


def get_nfs_data():
    return get_data('dados_nfs')


def get_charge_data():
    return get_data('dados_carga')


def get_main_data():
    data = get_volume_data()
    result = []
    pdv_data = get_pdv_data()
    stock_data = get_stock_data()
    order_data = get_order_data()
    nfs_data = get_nfs_data()
    for item in data:
        fat_stock = sum(
            [
                int(d['almox15'])
                for d in stock_data
                if d['cod_item'] == item['codigo_produto']
                and d['mascara'] == item['mascara']
            ]
        )
        emp_1 = sum(
            int(d['almox5'])
            for d in stock_data
            if d['cod_item'] == item['codigo_produto']
            and d['mascara'] == item['mascara']
        )
        emp_2 = sum(
            int(d['almoxtodos'])
            for d in stock_data
            if d['cod_item'] == item['codigo_produto']
            and d['mascara'] == item['mascara']
        )
        general_stock = fat_stock + emp_1 + emp_2
        pdv_amount = sum(
            [
                d['qtde']
                for d in pdv_data
                if d['cod_item'] == item['codigo_produto']
                and d['mascara'] == item['mascara']
            ]
        )
        order_amount = sum(
            [
                d['qtde_pendente']
                for d in order_data
                if d['cod_item'] == item['codigo_produto']
                and d['mascara'] == item['mascara']
            ]
        )
        monthly_average = sum(
            [
                d['media']
                for d in nfs_data
                if d['cod_item'] == item['codigo_produto']
                and d['mascara'] == item['mascara']
            ]
        )
        result.append(
            {
                'COD EMP': item['codigo_empresa'],
                'COD ITEM': item['codigo_produto'],
                'DESC TECNICA': item['produto'],
                'CONFIGURACAO': item['mascara'],
                'VOLUME': item['vol'],
                'ID MASCARA': item['tmasc_item_id'],
                'EM LINHA': item['em_linha'],
                'QTDE PDV': pdv_amount,
                'ESTOQUE FAT': fat_stock,
                'ESTOQUE GERAL': general_stock,
                'DISPONIVEL': general_stock - pdv_amount,
                'QTDE ORDEM': order_amount,
                'DISPONIVEL PREVISTO': general_stock
                - pdv_amount
                + order_amount,
                'MEDIA MENSAL': monthly_average,
                'NECESSIDADE': general_stock
                - pdv_amount
                + order_amount
                - monthly_average,
                'SUGESTÃO': 'Produzir'
                if general_stock - pdv_amount + order_amount - monthly_average
                < 0
                else '',
                'PRODUZIR CALCULADO': '',
            }
        )
    return result
