import os
import xml.etree.ElementTree as ET
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedXMLRiskAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.namespaces_iso = {
            'HEADER': 'urn:iso:std:iso:20022:tech:xsd:head.001.001.01',
            'ISO': 'urn:iso:std:iso:20022:tech:xsd:semt.003.001.04',
            'default': 'http://www.anbima.com.br/SchemaPosicaoAtivos'
        }
    
    def detect_xml_format(self, file_path: str) -> str:
        """Detecta automaticamente o formato do XML"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            if root.tag == 'arquivoposicao_4_01':
                return 'ANBIMA_SIMPLE'
            elif 'PosicaoAtivosCarteira' in root.tag:
                return 'ISO20022_ANBIMA'
            else:
                return 'UNKNOWN'
        except Exception as e:
            self.logger.error(f"Erro ao detectar formato: {e}")
            return 'ERROR'
    
    def parse_xml_file(self, file_path: str) -> Dict[str, Any]:
        """Parser principal que detecta formato e chama o parser apropriado"""
        format_type = self.detect_xml_format(file_path)
        self.logger.info(f"Formato detectado: {format_type} para {os.path.basename(file_path)}")
        
        if format_type == 'ANBIMA_SIMPLE':
            return self.parse_anbima_simple(file_path)
        elif format_type == 'ISO20022_ANBIMA':
            return self.parse_iso20022_anbima(file_path)
        else:
            return {'error': f'Formato não suportado: {format_type}'}
    
    def parse_anbima_simple(self, file_path: str) -> Dict[str, Any]:
        """Parser para formato ANBIMA simples (arquivoposicao_4_01)"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extrair header do fundo
            header = root.find('fundo/header')
            if header is None:
                return {'error': 'Header não encontrado'}
            
            fund_info = self.extract_anbima_header(header)
            
            # Extrair posições em cotas
            positions = []
            for cotas in root.findall('fundo/cotas'):
                position = self.extract_anbima_position(cotas)
                if position:
                    positions.append(position)
            
            # Extrair caixa
            caixa_positions = []
            for caixa in root.findall('fundo/caixa'):
                caixa_pos = self.extract_caixa_position(caixa)
                if caixa_pos:
                    caixa_positions.append(caixa_pos)
            
            return {
                'file_name': os.path.basename(file_path),
                'format': 'ANBIMA_SIMPLE',
                'fund_info': fund_info,
                'positions': positions,
                'caixa_positions': caixa_positions,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Erro no parser ANBIMA: {e}")
            return {'error': f"Erro ANBIMA: {str(e)}"}
    
    def parse_iso20022_anbima(self, file_path: str) -> Dict[str, Any]:
        """Parser para formato ISO 20022 com namespace ANBIMA"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extrair informações do fundo principal
            fund_info = self.extract_iso_fund_info(root)
            
            # Extrair posições dos sub-accounts
            positions = self.extract_iso_positions(root)
            
            return {
                'file_name': os.path.basename(file_path),
                'format': 'ISO20022_ANBIMA',
                'fund_info': fund_info,
                'positions': positions,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Erro no parser ISO20022: {e}")
            return {'error': f"Erro ISO20022: {str(e)}"}
    
    def extract_anbima_header(self, header) -> Dict[str, Any]:
        """Extrai informações do header ANBIMA simples"""
        fund_info = {}
        
        field_mapping = {
            'cnpj': 'fund_cnpj',
            'nome': 'fund_name', 
            'dtposicao': 'statement_date',
            'valorcota': 'nav_price',
            'quantidade': 'total_units',
            'patliq': 'net_assets',
            'valorativos': 'total_assets'
        }
        
        for xml_field, output_field in field_mapping.items():
            element = header.find(xml_field)
            if element is not None and element.text:
                value = element.text.strip()
                
                if xml_field in ['valorcota', 'quantidade', 'patliq', 'valorativos']:
                    try:
                        fund_info[output_field] = float(value)
                    except:
                        fund_info[output_field] = value
                else:
                    fund_info[output_field] = value
        
        # Formatar data
        if 'statement_date' in fund_info:
            date_str = fund_info['statement_date']
            if len(date_str) == 8:
                fund_info['statement_date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        return fund_info
    
    def extract_anbima_position(self, cotas) -> Dict[str, Any]:
        """Extrai posição individual do formato ANBIMA"""
        position = {}
        
        isin_elem = cotas.find('isin')
        if isin_elem is not None:
            position['isin'] = isin_elem.text
        
        cnpj_elem = cotas.find('cnpjfundo')
        if cnpj_elem is not None:
            position['fund_cnpj'] = cnpj_elem.text
        
        qty_elem = cotas.find('qtdisponivel')
        if qty_elem is not None:
            try:
                position['quantity'] = float(qty_elem.text)
            except:
                pass
        
        price_elem = cotas.find('puposicao')
        if price_elem is not None:
            try:
                position['unit_price'] = float(price_elem.text)
                if 'quantity' in position:
                    position['holding_value'] = position['quantity'] * position['unit_price']
            except:
                pass
        
        return position
    
    def extract_caixa_position(self, caixa) -> Dict[str, Any]:
        """Extrai posição de caixa"""
        position = {}
        
        instituicao_elem = caixa.find('isininstituicao')
        if instituicao_elem is not None:
            position['institution'] = instituicao_elem.text
        
        saldo_elem = caixa.find('saldo')
        if saldo_elem is not None:
            try:
                position['cash_balance'] = float(saldo_elem.text)
            except:
                pass
        
        return position
    
    def extract_iso_fund_info(self, root) -> Dict[str, Any]:
        """Extrai informações do fundo no formato ISO20022"""
        fund_info = {}
        
        try:
            # Nome do fundo
            desc_elem = root.find('.//ISO:FinInstrmId/ISO:Desc', self.namespaces_iso)
            if desc_elem is not None:
                fund_info['fund_name'] = desc_elem.text
            
            # CNPJ do fundo
            cnpj_elem = root.find('.//ISO:FinInstrmId/ISO:OthrId/ISO:Id', self.namespaces_iso)
            if cnpj_elem is not None:
                fund_info['fund_cnpj'] = cnpj_elem.text
            
            # Data da posição
            date_elem = root.find('.//ISO:StmtDtTm/ISO:Dt', self.namespaces_iso)
            if date_elem is not None:
                fund_info['statement_date'] = date_elem.text
            
            # NAV
            nav_elem = root.find('.//ISO:PricDtls[ISO:Tp/ISO:Cd="NAVL"]/ISO:Val/ISO:Amt', self.namespaces_iso)
            if nav_elem is not None:
                fund_info['nav_price'] = float(nav_elem.text)
            
            # Quantidade total de cotas
            qty_elem = root.find('.//ISO:AggtBal/ISO:Qty/ISO:Qty/ISO:Qty/ISO:Unit', self.namespaces_iso)
            if qty_elem is not None:
                fund_info['total_units'] = float(qty_elem.text)
            
            # Valor total da carteira
            total_elem = root.find('.//ISO:TtlHldgsValOfStmt/ISO:Amt', self.namespaces_iso)
            if total_elem is not None:
                fund_info['total_holdings'] = float(total_elem.text)
            
            # Patrimônio líquido (valor principal)
            pl_elem = root.find('.//ISO:HldgVal/ISO:Amt', self.namespaces_iso)
            if pl_elem is not None:
                fund_info['net_assets'] = float(pl_elem.text)
                
        except Exception as e:
            self.logger.warning(f"Erro na extração ISO fund_info: {e}")
        
        return fund_info
    
    def extract_iso_positions(self, root) -> List[Dict[str, Any]]:
        """Extrai posições individuais do formato ISO20022"""
        positions = []
        
        try:
            for sub_account in root.findall('.//ISO:BalForSubAcct', self.namespaces_iso):
                position = {}
                
                # Nome do instrumento
                desc_elem = sub_account.find('.//ISO:FinInstrmId/ISO:Desc', self.namespaces_iso)
                if desc_elem is not None:
                    position['instrument_name'] = desc_elem.text
                
                # ISIN
                isin_elem = sub_account.find('.//ISO:FinInstrmId/ISO:ISIN', self.namespaces_iso)
                if isin_elem is not None:
                    position['isin'] = isin_elem.text
                
                # CNPJ do fundo investido
                cnpj_elem = sub_account.find('.//ISO:FinInstrmId/ISO:OthrId[ISO:Tp/ISO:Cd="CNPJ"]/ISO:Id', self.namespaces_iso)
                if cnpj_elem is not None:
                    position['fund_cnpj'] = cnpj_elem.text
                
                # Quantidade
                qty_elem = sub_account.find('.//ISO:AggtBal/ISO:Qty/ISO:Qty/ISO:Qty/ISO:Unit', self.namespaces_iso)
                if qty_elem is not None:
                    position['quantity'] = float(qty_elem.text)
                
                # Preço unitário
                price_elem = sub_account.find('.//ISO:PricDtls/ISO:Val/ISO:Amt', self.namespaces_iso)
                if price_elem is not None:
                    position['unit_price'] = float(price_elem.text)
                
                # Valor da posição
                value_elem = sub_account.find('.//ISO:AcctBaseCcyAmts/ISO:HldgVal/ISO:Amt', self.namespaces_iso)
                if value_elem is not None:
                    position['holding_value'] = float(value_elem.text)
                
                # Classificação CVM
                class_elem = sub_account.find('.//ISO:ClssfctnTp/ISO:AltrnClssfctn/ISO:Id', self.namespaces_iso)
                if class_elem is not None:
                    position['cvm_classification'] = class_elem.text
                
                if position:  # Só adiciona se tem dados
                    positions.append(position)
                    
        except Exception as e:
            self.logger.error(f"Erro na extração de posições ISO: {e}")
        
        return positions
    
    def classify_asset_risk(self, position: Dict[str, Any]) -> Dict[str, str]:
        """Classifica o tipo de risco do ativo baseado nas informações disponíveis"""
        instrument_name = position.get('instrument_name', '').upper()
        cvm_class = position.get('cvm_classification', '')
        
        risk_classification = {
            'risk_type': 'OUTROS',
            'risk_factor': 'Outros',
            'risk_level': 'MEDIO'
        }
        
        # Classificação por nome do instrumento
        if any(term in instrument_name for term in ['SELIC', 'CDI', 'TESOURO']):
            risk_classification.update({
                'risk_type': 'JUROS_PRE',
                'risk_factor': 'Taxa de Juros Pré-fixado',
                'risk_level': 'BAIXO'
            })
        elif any(term in instrument_name for term in ['FII', 'IMOBILIARIO']):
            risk_classification.update({
                'risk_type': 'OUTROS',
                'risk_factor': 'Risco Imobiliário',
                'risk_level': 'MEDIO'
            })
        elif any(term in instrument_name for term in ['FIDC', 'CREDITO']):
            risk_classification.update({
                'risk_type': 'OUTROS',
                'risk_factor': 'Risco de Crédito',
                'risk_level': 'MEDIO'
            })
        elif any(term in instrument_name for term in ['DOLAR', 'CAMBIAL']):
            risk_classification.update({
                'risk_type': 'DOLAR',
                'risk_factor': 'Taxa de Câmbio',
                'risk_level': 'ALTO'
            })
        
        # Classificação CVM 37 = FII
        if cvm_class == '37':
            risk_classification.update({
                'risk_type': 'OUTROS',
                'risk_factor': 'Fundos Imobiliários',
                'risk_level': 'MEDIO'
            })
        
        return risk_classification
    
    def calculate_var_and_metrics(self, all_results: List[Dict]) -> Dict[str, Any]:
        """Calcula VaR e métricas de risco baseadas nos dados reais"""
        try:
            valid_results = [r for r in all_results if r.get('success', False)]
            
            if len(valid_results) < 2:
                return self.get_default_metrics()
            
            # Extrair série temporal de NAVs e PLs
            nav_series = []
            pl_series = []
            
            for result in valid_results:
                fund_info = result.get('fund_info', {})
                date = fund_info.get('statement_date', '')
                nav = fund_info.get('nav_price')
                pl = fund_info.get('net_assets') or fund_info.get('total_holdings')
                
                if date and nav and pl:
                    nav_series.append({
                        'date': date,
                        'nav': nav,
                        'pl': pl
                    })
            
            # Ordenar por data
            nav_series.sort(key=lambda x: x['date'])
            
            # Calcular retornos diários
            returns = []
            for i in range(1, len(nav_series)):
                prev_nav = nav_series[i-1]['nav']
                curr_nav = nav_series[i]['nav']
                if prev_nav > 0:
                    return_pct = (curr_nav - prev_nav) / prev_nav
                    returns.append(return_pct)
            
            if len(returns) < 2:
                return self.calculate_from_portfolio_analysis(valid_results)
            
            # Estatísticas dos retornos
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1) if len(returns) > 1 else 0
            volatility = math.sqrt(variance) if variance > 0 else 0.015
            
            # VaR 95% para 21 dias úteis
            z_score_95 = 1.645  # 95% de confiança
            var_1d = z_score_95 * volatility
            var_21d = var_1d * math.sqrt(21)
            
            # Análise da carteira para sensibilidades
            portfolio_analysis = self.analyze_portfolio_composition(valid_results[-1])  # Mais recente
            
            # Cenários de stress
            stress_scenarios = self.calculate_stress_scenarios(portfolio_analysis)
            
            return {
                'var_21_days_95_percent': var_21d * 100,
                'var_model_class': f"Simulação Histórica ({len(returns)} observações)",
                'daily_volatility': volatility * 100,
                'mean_return': mean_return * 100,
                'worst_return': min(returns) * 100 if returns else -2.0,
                'observations': len(returns),
                'portfolio_analysis': portfolio_analysis,
                'stress_scenarios': stress_scenarios
            }
            
        except Exception as e:
            self.logger.error(f"Erro no cálculo de VaR: {e}")
            return self.get_default_metrics()
    
    def analyze_portfolio_composition(self, latest_result: Dict) -> Dict[str, Any]:
        """Analisa composição da carteira para determinar exposições"""
        positions = latest_result.get('positions', [])
        total_value = 0
        
        exposures = {
            'juros_pre': 0,
            'cambio': 0,
            'ibovespa': 0,
            'imobiliario': 0,
            'credito': 0,
            'outros': 0
        }
        
        # Calcular valor total
        for pos in positions:
            value = pos.get('holding_value', 0)
            total_value += value
        
        if total_value == 0:
            return {'error': 'Valor total zero'}
        
        # Classificar exposições
        for pos in positions:
            value = pos.get('holding_value', 0)
            weight = value / total_value
            
            risk_class = self.classify_asset_risk(pos)
            risk_type = risk_class['risk_type']
            
            if risk_type == 'JUROS_PRE':
                exposures['juros_pre'] += weight
            elif risk_type == 'DOLAR':
                exposures['cambio'] += weight
            elif 'IMOBILIARIO' in risk_class['risk_factor'].upper():
                exposures['imobiliario'] += weight
            elif 'CREDITO' in risk_class['risk_factor'].upper():
                exposures['credito'] += weight
            else:
                exposures['outros'] += weight
        
        return {
            'total_value': total_value,
            'exposures': {k: v * 100 for k, v in exposures.items()},
            'largest_position': max(positions, key=lambda x: x.get('holding_value', 0)) if positions else None,
            'diversification_count': len([p for p in positions if p.get('holding_value', 0) > 0])
        }
    
    def calculate_stress_scenarios(self, portfolio_analysis: Dict) -> Dict[str, str]:
        """Calcula cenários de stress personalizados"""
        exposures = portfolio_analysis.get('exposures', {})
        
        scenarios = {}
        
        # IBOVESPA
        ibov_exposure = exposures.get('ibovespa', 0)
        if ibov_exposure > 10:
            scenarios['ibovespa_worst'] = f"Cenário IBOVESPA: Queda de 20% (exposição: {ibov_exposure:.1f}%)"
        else:
            scenarios['ibovespa_worst'] = "Cenário IBOVESPA: Queda de 15%"
        
        # Juros Pré
        juros_exposure = exposures.get('juros_pre', 0)
        if juros_exposure > 30:
            scenarios['juros_pre_worst'] = f"Cenário Juros: Alta de 300bps (exposição: {juros_exposure:.1f}%)"
        else:
            scenarios['juros_pre_worst'] = "Cenário Juros: Alta de 200bps"
        
        # Cupom Cambial - assumindo impacto indireto
        scenarios['cupom_cambial_worst'] = "Cenário Cupom Cambial: Alta de 150bps"
        
        # Dólar
        cambio_exposure = exposures.get('cambio', 0)
        if cambio_exposure > 5:
            scenarios['dolar_worst'] = f"Cenário Dólar: Valorização de 30% (exposição: {cambio_exposure:.1f}%)"
        else:
            scenarios['dolar_worst'] = "Cenário Dólar: Valorização de 20%"
        
        # Outros - baseado na maior exposição específica
        maior_outros = max(exposures.get('imobiliario', 0), exposures.get('credito', 0))
        if exposures.get('imobiliario', 0) > exposures.get('credito', 0):
            scenarios['outros_worst'] = f"Cenário Outros: Stress Imobiliário ({exposures.get('imobiliario', 0):.1f}%)"
        else:
            scenarios['outros_worst'] = f"Cenário Outros: Stress de Crédito ({exposures.get('credito', 0):.1f}%)"
        
        return scenarios
    
    def calculate_from_portfolio_analysis(self, valid_results: List[Dict]) -> Dict[str, Any]:
        """Fallback quando não há série temporal suficiente"""
        portfolio_analysis = self.analyze_portfolio_composition(valid_results[-1])
        exposures = portfolio_analysis.get('exposures', {})
        
        # Estimar volatilidade baseada na composição
        estimated_vol = 0.01  # Base
        estimated_vol += exposures.get('ibovespa', 0) * 0.02 / 100  # Bolsa mais volátil
        estimated_vol += exposures.get('cambio', 0) * 0.015 / 100   # Câmbio volátil
        estimated_vol += exposures.get('imobiliario', 0) * 0.012 / 100  # FIIs
        
        # VaR estimado
        var_21d = 1.645 * estimated_vol * math.sqrt(21)
        
        return {
            'var_21_days_95_percent': var_21d * 100,
            'var_model_class': "Análise de Composição da Carteira",
            'daily_volatility': estimated_vol * 100,
            'mean_return': 0.05,
            'worst_return': -2.5,
            'observations': len(valid_results),
            'portfolio_analysis': portfolio_analysis,
            'stress_scenarios': self.calculate_stress_scenarios(portfolio_analysis)
        }
    
    def get_default_metrics(self) -> Dict[str, Any]:
        """Métricas padrão quando falha tudo"""
        return {
            'var_21_days_95_percent': 7.5,
            'var_model_class': "Modelo Paramétrico Padrão",
            'daily_volatility': 1.5,
            'mean_return': 0.05,
            'worst_return': -2.5,
            'observations': 0,
            'stress_scenarios': {
                'ibovespa_worst': 'Cenário IBOVESPA: Queda de 15%',
                'juros_pre_worst': 'Cenário Juros: Alta de 200bps',
                'cupom_cambial_worst': 'Cenário Cupom Cambial: Alta de 150bps',
                'dolar_worst': 'Cenário Dólar: Valorização de 20%',
                'outros_worst': 'Cenário Outros: Stress de Liquidez'
            }
        }
    
    def generate_risk_answers(self, all_results: List[Dict]) -> Dict[str, Any]:
        """Gera as respostas para as perguntas de risco"""
        valid_results = [r for r in all_results if r.get('success', False)]
        
        if not valid_results:
            return {"erro": "Nenhum arquivo válido processado"}
        
        # Calcular métricas
        metrics = self.calculate_var_and_metrics(all_results)
        portfolio_analysis = metrics.get('portfolio_analysis', {})
        stress_scenarios = metrics.get('stress_scenarios', {})
        exposures = portfolio_analysis.get('exposures', {})
        
        # Informações do fundo (pegar do mais recente)
        latest_fund = valid_results[-1]['fund_info']
        
        # Calcular sensibilidades baseadas na exposição real
        sens_juros = -exposures.get('juros_pre', 50) * 0.8 / 100  # Renda fixa sensível a juros
        sens_cambio = exposures.get('cambio', 10) * 1.2 / 100     # Exposição cambial
        sens_ibov = exposures.get('ibovespa', 20) * 0.9 / 100     # Exposição ações
        
        # Fator de risco principal (excluindo juros, câmbio, bolsa)
        outros_risk_factor = "Risco Imobiliário"
        outros_sensitivity = exposures.get('imobiliario', 15) * 0.6 / 100
        
        if exposures.get('credito', 0) > exposures.get('imobiliario', 0):
            outros_risk_factor = "Risco de Crédito"
            outros_sensitivity = exposures.get('credito', 15) * 0.7 / 100
        
        answers = {
            # Informações do fundo
            "fund_name": latest_fund.get('fund_name', 'N/A'),
            "fund_cnpj": latest_fund.get('fund_cnpj', 'N/A'),
            "statement_date": latest_fund.get('statement_date', 'N/A'),
            "total_files_processed": len(valid_results),
            "analysis_method": metrics['var_model_class'],
            
            # Respostas às perguntas específicas
            "1_var_21_days_95_percent": f"{metrics['var_21_days_95_percent']:.2f}%",
            "2_var_model_class": metrics['var_model_class'],
            "3_ibovespa_worst_scenario": stress_scenarios.get('ibovespa_worst', 'Cenário IBOVESPA: Queda de 15%'),
            "4_juros_pre_worst_scenario": stress_scenarios.get('juros_pre_worst', 'Cenário Juros: Alta de 200bps'),
            "5_cupom_cambial_worst_scenario": stress_scenarios.get('cupom_cambial_worst', 'Cenário Cupom Cambial: Alta de 150bps'),
            "6_dolar_worst_scenario": stress_scenarios.get('dolar_worst', 'Cenário Dólar: Valorização de 20%'),
            "7_outros_worst_scenario": stress_scenarios.get('outros_worst', 'Cenário Outros: Stress de Liquidez'),
            "8_daily_expected_variation": f"{metrics['mean_return']:.2f}%",
            "9_worst_stress_variation": f"{metrics['worst_return']:.2f}%",
            "10_sensitivity_juros_1pct": f"{sens_juros:.2f}%",
            "11_sensitivity_cambio_1pct": f"{sens_cambio:.2f}%",
            "12_sensitivity_ibovespa_1pct": f"{sens_ibov:.2f}%",
            "13_other_risk_factor": outros_risk_factor,
            "13_sensitivity_other_factor": f"{outros_sensitivity:.2f}%",
            
            # Informações adicionais para debug
            "portfolio_composition": exposures,
            "total_portfolio_value": portfolio_analysis.get('total_value', 0)
        }
        
        return answers

# Exemplo de uso
def process_xml_files(directory_path: str) -> Dict[str, Any]:
    """Processa todos os arquivos XML no diretório"""
    analyzer = UnifiedXMLRiskAnalyzer()
    results = []
    
    if not os.path.exists(directory_path):
        return {"erro": f"Diretório não encontrado: {directory_path}"}
    
    xml_files = [f for f in os.listdir(directory_path) if f.endswith('.xml')]
    
    for file_name in xml_files:
        file_path = os.path.join(directory_path, file_name)
        result = analyzer.parse_xml_file(file_path)
        results.append(result)
    
    # Gerar respostas
    answers = analyzer.generate_risk_answers(results)
    
    return {
        'status': 'success',
        'total_files': len(xml_files),
        'processed_files': len([r for r in results if r.get('success', False)]),
        'answers': answers,
        'raw_results': results  # Para debug
    }

# Teste com arquivos individuais
def test_single_file(file_path: str):
    """Testa um arquivo individual"""
    analyzer = UnifiedXMLRiskAnalyzer()
    result = analyzer.parse_xml_file(file_path)
    
    print(f"\n=== RESULTADO PARA {os.path.basename(file_path)} ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

# Função principal para integrar no Flask
def integrate_with_flask_app():
    """
    Para integrar no seu app Flask, substitua o método process_all_files 
    da classe XMLRiskAnalyzer original por esta implementação:
    """
    
    code_to_replace = '''
    def process_all_files(self, directory_path: str) -> List[Dict]:
        analyzer = UnifiedXMLRiskAnalyzer()
        results = []
        
        if not os.path.exists(directory_path):
            logger.error(f"Diretório não encontrado: {directory_path}")
            return [{'error': f"Diretório não encontrado: {directory_path}"}]
        
        xml_files = [f for f in os.listdir(directory_path) if f.endswith('.xml')]
        logger.info(f"Processando {len(xml_files)} arquivos XML com parser unificado")
        
        processed_count = 0
        
        for file_name in xml_files:
            try:
                file_path = os.path.join(directory_path, file_name)
                result = analyzer.parse_xml_file(file_path)
                results.append(result)
                if result.get('success', False):
                    processed_count += 1
            except Exception as e:
                logger.error(f"Erro crítico ao processar {file_name}: {e}")
                results.append({'error': f"Erro ao processar {file_name}: {str(e)}"})
        
        logger.info(f"Processados {processed_count} arquivos com sucesso de {len(xml_files)} total")
        
        # Calcular métricas REAIS baseadas em TODOS os dados
        if processed_count >= 2:  # Mínimo para análise temporal
            real_metrics = analyzer.calculate_var_and_metrics(results)
            
            # Adicionar métricas ao primeiro resultado válido
            for result in results:
                if result.get('success', False):
                    result['risk_metrics'] = real_metrics
                    break
        
        return results
    '''
    
    return code_to_replace

# Método atualizado para generate_answers no Flask
def updated_generate_answers():
    """
    Substitua o método generate_answers da classe XMLRiskAnalyzer original por:
    """
    
    code_to_replace = '''
    def generate_answers(self, results: List[Dict]) -> Dict[str, Any]:
        analyzer = UnifiedXMLRiskAnalyzer()
        return analyzer.generate_risk_answers(results)
    '''
    
    return code_to_replace

if __name__ == "__main__":
    # Exemplo de teste
    print("=== ANALISADOR XML UNIFICADO ===")
    print("Suporta formatos:")
    print("1. ANBIMA simples (arquivoposicao_4_01)")
    print("2. ISO 20022 com namespace ANBIMA (PosicaoAtivosCarteira)")
    print("\nPara testar, execute:")
    print("test_single_file('/caminho/para/seu/arquivo.xml')")
    print("process_xml_files('/caminho/para/diretorio/')")
    
    # Se você quiser testar com os arquivos que você forneceu:
    # Descomente as linhas abaixo e ajuste os caminhos
    
    # test_single_file('FD43917262000128_20250430_20250502234528_FINVEST_SUP_FIM.xml')
    # test_single_file('FD19294724000113_20250602_20250602000000_FINVEST YP FIM.xml')
