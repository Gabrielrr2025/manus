
from flask import Flask, request, render_template, send_file
import os
import pandas as pd
from process_xml import load_and_process_all_xmls, calculate_var, get_stress_scenario_data

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def upload_xml():
    if request.method == "POST":
        file = request.files.get("xmlfile")
        if file and file.filename.endswith(".xml"):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Processa o XML
            df = load_and_process_all_xmls([file_path])
            var_valor, modelo = calculate_var(df)
            stress = get_stress_scenario_data(df)

            # Monta DataFrame com respostas
            results = [
                ["VaR (21 dias úteis, 95% confiança)", f"{var_valor:.4f} %"],
                ["Modelo utilizado", modelo]
            ]
            for k, v in stress.items():
                results.append([k, v])

            df_results = pd.DataFrame(results, columns=["Pergunta", "Resposta"])
            output_path = os.path.join(UPLOAD_FOLDER, "resultado.xlsx")
            df_results.to_excel(output_path, index=False)

            return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
