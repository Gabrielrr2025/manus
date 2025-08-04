import os
from process_xml import load_and_process_all_xmls, calculate_var, get_stress_scenario_data

def run_analysis(xml_dir):
    xml_files = [os.path.join(xml_dir, f) for f in os.listdir(xml_dir) if f.endswith(".xml")]
    
    if not xml_files:
        print("Nenhum arquivo XML encontrado no diretório especificado.")
        return

    df = load_and_process_all_xmls(xml_files)

    # 1. Qual é o VAR (Valor de risco) de um dia como percentual do PL calculado para 21 dias úteis e 95% de confiança?
    var_value, var_model_class = calculate_var(df)
    if var_value is not None:
        print(f"1. VAR (Valor de Risco) de um dia como percentual do PL (21 dias úteis, 95% de confiança): {var_value:.4f}% (Modelo: {var_model_class})")
    else:
        print(f"1. VAR (Valor de Risco) de um dia como percentual do PL (21 dias úteis, 95% de confiança): {var_model_class}")

    # 2. Qual classe de modelos foi utilizada para o cálculo do VAR reportado na questão anterior?
    print(f"2. Classe de modelos utilizada para o cálculo do VAR: {var_model_class}")

    # Get stress scenario data and other expected variations
    stress_data = get_stress_scenario_data(df)

    # 3. Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) IBOVESPA que gere o pior resultado para o fundo, indique o cenário utilizado.
    print(f"3. Cenário de estresse IBOVESPA (pior resultado): {stress_data['ibovespa_worst_scenario']:.4f}% (baseado no pior retorno histórico da cota)")

    # 4. Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Juros-Pré que gere o pior resultado para o fundo, indique o cenário utilizado.
    print(f"4. Cenário de estresse Juros-Pré (pior resultado): {stress_data['juros_pre_scenario']}")

    # 5. Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Cupom Cambial que gere o pior resultado para o fundo, indique o cenário utilizado.
    print(f"5. Cenário de estresse Cupom Cambial (pior resultado): {stress_data['cupom_cambial_scenario']}")

    # 6. Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Dólar que gere o pior resultado para o fundo, indique o cenário utilizado.
    print(f"6. Cenário de estresse Dólar (pior resultado): {stress_data['dolar_scenario']}")

    # 7. Considerando os cenários de estresse definidos pela BM&FBOVESPA para o fator primitivo de risco (FPR) Outros que gere o pior resultado para o fundo, indique o cenário utilizado.
    print(f"7. Cenário de estresse Outros (pior resultado): {stress_data['outros_scenario']}")

    # 8. Qual a variação diária percentual esperada para o valor da cota?
    print(f"8. Variação diária percentual esperada para o valor da cota: {stress_data['expected_daily_return_cota']:.4f}%")

    # 9. Qual a variação diária percentual esperada para o valor da cota do fundo no pior cenário de estresse definido pelo seu administrador?
    print(f"9. Variação diária percentual esperada para o valor da cota no pior cenário de estresse: {stress_data['worst_stress_cota_return']:.4f}%")

    # 10. Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% na taxa anual de juros (pré)? Considerar o último dia útil do mês de referência.
    print(f"10. Variação diária percentual esperada para o patrimônio do fundo (Juros-Pré -1%): {stress_data['patrimonio_juros_stress']}")

    # 11. Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% na taxa de câmbio (US$/Real)? Considerar o último dia útil do mês de referência.
    print(f"11. Variação diária percentual esperada para o patrimônio do fundo (Câmbio -1%): {stress_data['patrimonio_cambio_stress']}")

    # 12. Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% no preço das ações (IBOVESPA)? Considerar o último dia útil do mês de referência.
    print(f"12. Variação diária percentual esperada para o patrimônio do fundo (IBOVESPA -1%): {stress_data['patrimonio_ibovespa_stress']}")

    # 13. Qual a variação diária percentual esperada para o patrimônio do fundo caso ocorra uma variação negativa de 1% no principal fator de risco que o fundo está exposto, caso não seja nenhum dos 3 citados anteriormente (juros, câmbio, bolsa)? Considerar o último dia útil do mês de referência. Informar também qual foi o fator de risco considerado.
    print(f"13. Variação diária percentual esperada para o patrimônio do fundo (Outros -1%): {stress_data['patrimonio_outros_stress']}")
    print(f"    Fator de risco considerado: {stress_data['fator_risco_outros']}")


if __name__ == '__main__':
    # Assuming XML files are in the /home/ubuntu/upload directory
    run_analysis('/home/ubuntu/upload')


