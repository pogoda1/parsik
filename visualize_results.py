import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime
import numpy as np
import base64
from io import BytesIO

# Настройка для отображения русских символов
plt.rcParams["font.family"] = ["DejaVu Sans", "Arial Unicode MS", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


def load_view_test_data():
    """Загружает данные из viewTest.json"""
    try:
        with open("data/viewTest.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл data/viewTest.json не найден")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return None


def create_time_chart(df):
    """Создает график времени обработки и возвращает base64 строку"""
    successful_data = df[df["has_error"] == False]
    
    if successful_data.empty:
        return None
    
    plt.figure(figsize=(12, 6))
    
    # Группируем по модели и вычисляем статистики
    model_stats = successful_data.groupby("model_name").agg({
        "processing_time": ["mean", "std", "count"]
    }).round(2)
    
    model_stats.columns = ["avg_time", "std_time", "count"]
    
    # Создаем bar chart
    colors = plt.cm.Set3(np.linspace(0, 1, len(model_stats)))
    bars = plt.bar(range(len(model_stats)), model_stats["avg_time"], 
                   yerr=model_stats["std_time"], capsize=5, color=colors, alpha=0.7)
    
    plt.title("Среднее время обработки событий по моделям", fontsize=14, fontweight="bold")
    plt.ylabel("Время (секунды)")
    plt.xlabel("Модель")
    plt.xticks(range(len(model_stats)), model_stats.index, rotation=45, ha="right")
    
    # Добавляем значения на столбцы
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}s', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Сохраняем график в base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64


def create_html_report(data):
    """Создает HTML отчет с результатами тестирования"""
    
    # Подготавливаем данные для анализа
    results = []
    for model_name, model_data in data["models"].items():
        for result in model_data["results"]:
            row = {
                "model_name": model_name,
                "event_id": result["event_id"],
                "input_text": result["input_text"],
                "has_error": "error" in result,
                "processing_time": result.get("processing_time_seconds"),
                "tested_at": model_data["tested_at"]
            }
            
            if "output_json" in result:
                output = result["output_json"].get("data", {})
                row["output_text"] = json.dumps(output, ensure_ascii=False, indent=2)
                row["error"] = None
            else:
                row["output_text"] = ""
                row["error"] = result.get("error", "Неизвестная ошибка")
            
            results.append(row)
    
    df = pd.DataFrame(results)
    
    # Создаем график времени
    time_chart_base64 = create_time_chart(df)
    
    # Создаем HTML таблицу
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Результаты тестирования моделей</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 1.1em;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 30px;
                background-color: #f8f9fa;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }}
            .stat-label {{
                color: #666;
                margin-top: 5px;
            }}
            .chart-section {{
                padding: 30px;
                text-align: center;
            }}
            .chart-section h2 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .chart-section img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .table-section {{
                padding: 30px;
            }}
            .table-section h2 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .results-table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .results-table th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 500;
            }}
            .results-table td {{
                padding: 15px;
                border-bottom: 1px solid #eee;
                vertical-align: top;
            }}
            .results-table tr:hover {{
                background-color: #f8f9fa;
            }}
            .model-name {{
                font-weight: bold;
                color: #667eea;
            }}
            .event-id {{
                font-weight: bold;
                color: #333;
            }}
            .input-text {{
                max-width: 300px;
                word-wrap: break-word;
                font-size: 0.9em;
                line-height: 1.4;
            }}
            .output-text {{
                max-width: 400px;
                word-wrap: break-word;
                font-size: 0.8em;
                line-height: 1.3;
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #28a745;
            }}
            .error-text {{
                color: #dc3545;
                font-weight: bold;
                background-color: #f8d7da;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #dc3545;
            }}
            .processing-time {{
                font-weight: bold;
                color: #28a745;
            }}
            .success {{
                color: #28a745;
                font-weight: bold;
            }}
            .error {{
                color: #dc3545;
                font-weight: bold;
            }}
            .timestamp {{
                font-size: 0.8em;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Результаты тестирования моделей</h1>
                <p>Анализ производительности и качества парсинга событий</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">""" + str(len(data['models'])) + """</div>
                    <div class="stat-label">Моделей протестировано</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(len(results)) + """</div>
                    <div class="stat-label">Событий обработано</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(len([r for r in results if not r['has_error']])) + """</div>
                    <div class="stat-label">Успешных обработок</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">""" + str(len([r for r in results if r['has_error']])) + """</div>
                    <div class="stat-label">Ошибок</div>
                </div>
            </div>
            
            <div class="chart-section">
                <h2>⏱️ Время обработки по моделям</h2>
                <img src="data:image/png;base64,""" + (time_chart_base64 or '') + """" alt="График времени обработки">
            </div>
            
            <div class="table-section">
                <h2>📋 Детальные результаты</h2>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Модель</th>
                            <th>ID события</th>
                            <th>Входной текст</th>
                            <th>Результат</th>
                            <th>Время (с)</th>
                            <th>Статус</th>
                            <th>Дата тестирования</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for result in results:
        status_class = "success" if not result["has_error"] else "error"
        status_text = "✅ Успех" if not result["has_error"] else "❌ Ошибка"
        
        html_content += """
                        <tr>
                            <td class="model-name">""" + result['model_name'] + """</td>
                            <td class="event-id">""" + str(result['event_id']) + """</td>
                            <td class="input-text">""" + result['input_text'][:200] + ('...' if len(result['input_text']) > 200 else '') + """</td>
                            <td>
        """
        
        if result["has_error"]:
            html_content += '<div class="error-text">' + result["error"] + '</div>'
        else:
            html_content += '<div class="output-text">' + result["output_text"][:500] + ("..." if len(result["output_text"]) > 500 else "") + '</div>'
        
        html_content += """
                            </td>
                            <td class="processing-time">""" + (f"{result['processing_time']:.2f}" if result['processing_time'] else 'N/A') + """</td>
                            <td class="""" + status_class + """">""" + status_text + """</td>
                            <td class="timestamp">""" + result['tested_at'] + """</td>
                        </tr>
        """
    
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


def main():
    """Основная функция создания HTML отчета"""
    print("🚀 Создание HTML отчета результатов тестирования...")
    
    # Загружаем данные
    data = load_view_test_data()
    if data is None:
        return
    
    print(f"✅ Загружены данные для {len(data['models'])} моделей")
    
    # Создаем HTML отчет
    html_content = create_html_report(data)
    
    # Сохраняем HTML файл
    with open("data/test_results_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML отчет создан: data/test_results_report.html")
    print("📊 Отчет содержит:")
    print("   • Статистику по моделям")
    print("   • График времени обработки")
    print("   • Детальную таблицу результатов")
    print("   • Входные и выходные данные для каждого события")


if __name__ == "__main__":
    main()
