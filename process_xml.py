import xml.etree.ElementTree as ET
import pandas as pd

def parse_xml_data(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    data = {}
    header = root.find('.//header')
    if header:
        data['dtposicao'] = header.find('dtposicao').text
        data['valorcota'] = float(header.find('valorcota').text)
        data['patliq'] = float(header.find('patliq').text)
    return data


def load_and_process_all_xmls(file_paths):
    all_data = []
    for f_path in file_paths:
        all_data.append(parse_xml_data(f_path))

    df = pd.DataFrame(all_data)
    df['dtposicao'] = pd.to_datetime(df['dtposicao'])
    df = df.sort_values(by='dtposicao').set_index('dtposicao')

    # Calculate daily returns
    df['valorcota_return'] = df['valorcota'].pct_change() * 100
    df['patliq_return'] = df['patliq'].pct_change() * 100

    return df


# Placeholder for main execution or further functions
if __name__ == '__main__':
    # This part will be executed when the script is run directly
    # In the agent context, we will call functions directly.
    pass




def calculate_var(df, confidence_level=0.95, days=21):
    # Assuming daily returns are already calculated in the DataFrame
    # For VAR, we need the historical returns of the fund's value (valorcota)
    returns = df["valorcota_return"].dropna()

    if len(returns) < days:
        return None, "Não há dados suficientes para calcular o VAR para 21 dias úteis."

    # Calculate the percentile for VAR
    var_percentile = (1 - confidence_level) * 100
    var_value = returns.quantile(var_percentile / 100)

    # VAR is typically expressed as a positive loss, so we take the absolute value
    return abs(var_value), "Histórico"




def get_stress_scenario_data(df):
    # This function is a placeholder. In a real scenario, stress test data
    # would come from a different source or be explicitly defined.
    # For now, we'll simulate some values based on the available data.

    # Worst case for IBOVESPA (simulated as worst historical daily return of valorcota)
    ibovespa_worst_scenario = df["valorcota_return"].min()

    # For Juros-Pré, Cupom Cambial, Dólar, Outros, and specific stress scenarios
    # we need external data or explicit definitions from the XML.
    # Since the XML does not provide this, we will return placeholders or indicate missing data.

    # Placeholder for Juros-Pré, Cupom Cambial, Dólar, Outros
    # In a real scenario, these would be derived from specific tags in a more detailed XML
    # or from external stress test reports.
    juros_pre_scenario = "Não disponível no XML fornecido"
    cupom_cambial_scenario = "Não disponível no XML fornecido"
    dolar_scenario = "Não disponível no XML fornecido"
    outros_scenario = "Não disponível no XML fornecido"

    # Variação diária percentual esperada para o valor da cota (média histórica)
    expected_daily_return_cota = df["valorcota_return"].mean()

    # Variação diária percentual esperada para o valor da cota do fundo no pior cenário de estresse
    # (usando o pior retorno histórico da cota como proxy para o pior cenário)
    worst_stress_cota_return = df["valorcota_return"].min()

    # Variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% na taxa anual de juros (pré)
    # This requires sensitivity analysis, which is not possible with the current XML data.
    # Placeholder for now.
    patrimonio_juros_stress = "Não calculável com os dados do XML"

    # Variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% na taxa de câmbio (US$/Real)
    patrimonio_cambio_stress = "Não calculável com os dados do XML"

    # Variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% no preço das ações (IBOVESPA)
    patrimonio_ibovespa_stress = "Não calculável com os dados do XML"

    # Variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% no principal fator de risco que o fundo está exposto
    patrimonio_outros_stress = "Não calculável com os dados do XML"
    fator_risco_outros = "Não identificado no XML"

    return {
        "ibovespa_worst_scenario": ibovespa_worst_scenario,
        "juros_pre_scenario": juros_pre_scenario,
        "cupom_cambial_scenario": cupom_cambial_scenario,
        "dolar_scenario": dolar_scenario,
        "outros_scenario": outros_scenario,
        "expected_daily_return_cota": expected_daily_return_cota,
        "worst_stress_cota_return": worst_stress_cota_return,
        "patrimonio_juros_stress": patrimonio_juros_stress,
        "patrimonio_cambio_stress": patrimonio_cambio_stress,
        "patrimonio_ibovespa_stress": patrimonio_ibovespa_stress,
        "patrimonio_outros_stress": patrimonio_outros_stress,
        "fator_risco_outros": fator_risco_outros,
    }


