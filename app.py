
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import zipfile
import xml.etree.ElementTree as ET
import tempfile
import shutil
import numpy as np
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

NAMESPACES = {
    'ISO': 'urn:iso:std:iso:20022:tech:xsd:semt.003.001.04',
    'ns': 'http://www.anbima.com.br/SchemaPosicaoAtivos'
}

def extract_nav_info(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        nav_elem = root.find('.//ISO:BalForAcct/ISO:PricDtls[ISO:Tp/ISO:Cd="NAVL"]/ISO:Val/ISO:Amt', NAMESPACES)
        date_elem = root.find('.//ISO:StmtDtTm/ISO:Dt', NAMESPACES)
        pl_elem = root.find('.//ISO:BalForAcct/ISO:TtlValOfFnds/ISO:Amt', NAMESPACES)
        units_elem = root.find('.//ISO:BalForAcct/ISO:UnitsNb', NAMESPACES)

        return {
            'date': datetime.strptime(date_elem.text, '%Y-%m-%d') if date_elem is not None else None,
            'nav': float(nav_elem.text) if nav_elem is not None else None,
            'pl': float(pl_elem.text) if pl_elem is not None else None,
            'units': float(units_elem.text) if units_elem is not None else None
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename.endswith('.zip'):
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, secure_filename(uploaded_file.filename))
            uploaded_file.save(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            nav_series = []
            for root_dir, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.xml'):
                        path = os.path.join(root_dir, file)
                        info = extract_nav_info(path)
                        if 'nav' in info and info['nav']:
                            nav_series.append(info)

            shutil.rmtree(temp_dir)

            if len(nav_series) < 2:
                flash('Erro: Menos de 2 arquivos com dados válidos encontrados.', 'danger')
                return redirect(url_for('index'))

            df = pd.DataFrame(nav_series)
            df.sort_values("date", inplace=True)
            df["log_return"] = np.log(df["nav"] / df["nav"].shift(1))
            volatility = df["log_return"].std()
            expected_return = df["log_return"].mean()
            var_1d_95 = 1.645 * volatility

            results = {
                'volatility': f"{volatility * 100:.4f}%",
                'expected_return': f"{expected_return * 100:.4f}%",
                'var_1d_95pct': f"{var_1d_95 * 100:.4f}%",
                'worst_observed': f"{df['log_return'].min() * 100:.4f}%"
            }

            return render_template('results.html', results=results)

        else:
            flash('Por favor, envie um arquivo .zip com os XMLs.', 'warning')
            return redirect(request.url)

    return render_template('index.html')
