import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datetime import datetime
import numpy as np

# Настройка для отображения русских символов
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def load_view_test_data():
    """Загружает данные из viewTest.json"""
    try:
        with open('data/viewTest.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Файл data/viewTest.json не найден")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return None

def prepare_data_for_analysis(data):
    """Подготавливает данные для анализа"""
    results = []
    
    for model_name, model_data in data['models'].items():
        for result in model_data['results']:
            row = {
                'model_name': model_name,
                'event_id': result['event_id'],
                'has_error': 'error' in result,
                'processing_time': result.get('processing_time_seconds'),
                'tested_at': model_data['tested_at']
            }
            
            # Анализируем успешные результаты
            if 'output_json' in result:
                output = result['output_json'].get('data', {})
                row.update({
                    'event_title': output.get('eventTitle', ''),
                    'event_categories': output.get('eventCategories', []),
                    'event_themes': output.get('eventThemes', []),
                    'event_price': output.get('eventPrice', [0])[0] if output.get('eventPrice') else 0,
                    'event_age_limit': output.get('eventAgeLimit', ''),
                    'has_location': bool(output.get('eventLocation', {}).get('name')),
                    'has_link': bool(output.get('linkSource')),
                    'date_parsed': bool(output.get('eventDate'))
                })
            else:
                row.update({
                    'event_title': '',
                    'event_categories': [],
                    'event_themes': [],
                    'event_price': 0,
                    'event_age_limit': '',
                    'has_location': False,
                    'has_link': False,
                    'date_parsed': False
                })
            
            results.append(row)
    
    return pd.DataFrame(results)

def create_performance_comparison(df):
    """Создает график сравнения производительности моделей"""
    plt.figure(figsize=(12, 8))
    
    # Группируем по модели и вычисляем статистики
    model_stats = df.groupby('model_name').agg({
        'processing_time': ['mean', 'std', 'count'],
        'has_error': 'sum'
    }).round(2)
    
    model_stats.columns = ['avg_time', 'std_time', 'total_events', 'errors']
    model_stats['success_rate'] = ((model_stats['total_events'] - model_stats['errors']) / model_stats['total_events'] * 100).round(1)
    
    # Создаем график
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # График времени обработки
    colors = plt.cm.Set3(np.linspace(0, 1, len(model_stats)))
    bars1 = ax1.bar(range(len(model_stats)), model_stats['avg_time'], 
                    yerr=model_stats['std_time'], capsize=5, color=colors, alpha=0.7)
    ax1.set_title('Среднее время обработки событий по моделям', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Время (секунды)')
    ax1.set_xticks(range(len(model_stats)))
    ax1.set_xticklabels(model_stats.index, rotation=45, ha='right')
    
    # Добавляем значения на столбцы
    for i, bar in enumerate(bars1):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}s', ha='center', va='bottom', fontweight='bold')
    
    # График успешности
    bars2 = ax2.bar(range(len(model_stats)), model_stats['success_rate'], 
                    color=colors, alpha=0.7)
    ax2.set_title('Процент успешных обработок по моделям', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Успешность (%)')
    ax2.set_xticks(range(len(model_stats)))
    ax2.set_xticklabels(model_stats.index, rotation=45, ha='right')
    ax2.set_ylim(0, 100)
    
    # Добавляем значения на столбцы
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('data/model_performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return model_stats

def create_error_analysis(df):
    """Анализирует ошибки по моделям"""
    error_data = df[df['has_error'] == True]
    
    if error_data.empty:
        print("✅ Ошибок не найдено")
        return
    
    plt.figure(figsize=(12, 6))
    
    # Подсчитываем ошибки по моделям
    error_counts = error_data['model_name'].value_counts()
    
    colors = plt.cm.Reds(np.linspace(0.3, 0.8, len(error_counts)))
    bars = plt.bar(range(len(error_counts)), error_counts.values, color=colors, alpha=0.7)
    
    plt.title('Количество ошибок по моделям', fontsize=14, fontweight='bold')
    plt.ylabel('Количество ошибок')
    plt.xticks(range(len(error_counts)), error_counts.index, rotation=45, ha='right')
    
    # Добавляем значения на столбцы
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                str(int(height)), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('data/error_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_quality_analysis(df):
    """Анализирует качество парсинга"""
    successful_data = df[df['has_error'] == False]
    
    if successful_data.empty:
        print("❌ Нет успешных результатов для анализа качества")
        return
    
    # Создаем метрики качества
    quality_metrics = successful_data.groupby('model_name').agg({
        'has_location': 'mean',
        'has_link': 'mean',
        'date_parsed': 'mean',
        'event_categories': lambda x: x.apply(lambda cats: len(cats) > 0).mean(),
        'event_themes': lambda x: x.apply(lambda themes: len(themes) > 0).mean()
    }).round(3) * 100
    
    quality_metrics.columns = ['Локация', 'Ссылка', 'Дата', 'Категории', 'Темы']
    
    # Создаем тепловую карту
    plt.figure(figsize=(12, 8))
    sns.heatmap(quality_metrics.T, annot=True, fmt='.1f', cmap='RdYlGn', 
                cbar_kws={'label': 'Процент успешного парсинга (%)'})
    plt.title('Качество парсинга по моделям', fontsize=14, fontweight='bold')
    plt.ylabel('Тип данных')
    plt.xlabel('Модель')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('data/quality_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return quality_metrics

def create_time_distribution(df):
    """Создает распределение времени обработки"""
    successful_data = df[df['has_error'] == False]
    
    if successful_data.empty:
        print("❌ Нет успешных результатов для анализа времени")
        return
    
    plt.figure(figsize=(12, 6))
    
    # Создаем box plot
    models = successful_data['model_name'].unique()
    data_to_plot = [successful_data[successful_data['model_name'] == model]['processing_time'].dropna() 
                   for model in models]
    
    plt.boxplot(data_to_plot, labels=models)
    plt.title('Распределение времени обработки по моделям', fontsize=14, fontweight='bold')
    plt.ylabel('Время (секунды)')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('data/time_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()

def print_summary_statistics(df, model_stats, quality_metrics):
    """Выводит сводную статистику"""
    print("\n" + "="*80)
    print("📊 СВОДНАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ МОДЕЛЕЙ")
    print("="*80)
    
    print(f"\n📈 Общая статистика:")
    print(f"   • Всего протестировано моделей: {len(df['model_name'].unique())}")
    print(f"   • Всего обработано событий: {len(df)}")
    print(f"   • Успешных обработок: {len(df[df['has_error'] == False])}")
    print(f"   • Ошибок: {len(df[df['has_error'] == True])}")
    print(f"   • Общий процент успеха: {(len(df[df['has_error'] == False]) / len(df) * 100):.1f}%")
    
    print(f"\n🏆 Лучшие модели по времени:")
    fastest_models = model_stats.nsmallest(3, 'avg_time')
    for i, (model, stats) in enumerate(fastest_models.iterrows(), 1):
        print(f"   {i}. {model}: {stats['avg_time']:.2f}s ± {stats['std_time']:.2f}s")
    
    print(f"\n🎯 Лучшие модели по успешности:")
    best_models = model_stats.nlargest(3, 'success_rate')
    for i, (model, stats) in enumerate(best_models.iterrows(), 1):
        print(f"   {i}. {model}: {stats['success_rate']:.1f}% ({stats['total_events'] - stats['errors']}/{stats['total_events']})")
    
    if quality_metrics is not None:
        print(f"\n📋 Среднее качество парсинга:")
        avg_quality = quality_metrics.mean()
        for metric, value in avg_quality.items():
            print(f"   • {metric}: {value:.1f}%")

def main():
    """Основная функция визуализации"""
    print("🚀 Запуск визуализации результатов тестирования моделей...")
    
    # Загружаем данные
    data = load_view_test_data()
    if data is None:
        return
    
    print(f"✅ Загружены данные для {len(data['models'])} моделей")
    
    # Подготавливаем данные
    df = prepare_data_for_analysis(data)
    print(f"📊 Подготовлено {len(df)} записей для анализа")
    
    # Создаем визуализации
    print("\n📈 Создание графиков...")
    
    # Сравнение производительности
    model_stats = create_performance_comparison(df)
    
    # Анализ ошибок
    create_error_analysis(df)
    
    # Анализ качества
    quality_metrics = create_quality_analysis(df)
    
    # Распределение времени
    create_time_distribution(df)
    
    # Выводим сводку
    print_summary_statistics(df, model_stats, quality_metrics)
    
    print(f"\n✅ Визуализация завершена! Графики сохранены в папке data/")
    print(f"   • model_performance_comparison.png")
    print(f"   • error_analysis.png") 
    print(f"   • quality_analysis.png")
    print(f"   • time_distribution.png")

if __name__ == "__main__":
    main()
