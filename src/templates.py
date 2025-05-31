MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Обработка событий AI</title>
<style>
  body { font-family: Arial, sans-serif; margin: 20px; }
  button { font-size: 16px; padding: 10px 20px; }
  pre { background: #f0f0f0; padding: 10px; white-space: pre-wrap; max-height: 500px; overflow-y: auto; }
  .error { color: red; }
  .processing { color: #666; }
  .success { color: green; }
  .correction { color: #ff8c00; }
  .event-container { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
  .timestamp { color: #666; font-size: 0.9em; }
  .counter { 
    position: fixed;
    top: 20px;
    right: 20px;
    background: #f8f9fa;
    padding: 10px 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    font-size: 14px;
  }
  .counter span {
    font-weight: bold;
    color: #007bff;
  }
</style>
</head>
<body>
  <h1>Обработка событий AI</h1>
  <button id="loadBtn">Загрузить и обработать события</button>
  <div id="counter" class="counter" style="display: none;">
    Обработано: <span id="processed">0</span> из <span id="total">0</span>
  </div>
  <div id="output"></div>

<script>
  const btn = document.getElementById('loadBtn');
  const output = document.getElementById('output');
  const counter = document.getElementById('counter');
  const processedSpan = document.getElementById('processed');
  const totalSpan = document.getElementById('total');
  let currentEventIndex = 0;
  let events = [];

  function updateCounter() {
    processedSpan.textContent = currentEventIndex;
    totalSpan.textContent = events.length;
  }

  function formatTime(seconds) {
    return seconds.toFixed(2) + ' сек';
  }

  function updateEventDisplay(event, status, result = null) {
    const eventContainer = document.getElementById(`event-${event.id}`) || createEventContainer(event);
    const statusDiv = eventContainer.querySelector('.status');
    const timestamp = new Date().toLocaleTimeString();
    
    let statusHtml = `
      <span class="timestamp">[${timestamp}]</span>
      <span class="${status.toLowerCase()}">${status}</span>
      ${result ? `<br>Время обработки: ${formatTime(result.processing_time)}` : ''}
    `;

    if (result && result.corrections) {
      statusHtml += '<br><span class="correction">Исправления:</span><ul>';
      result.corrections.forEach(msg => {
        statusHtml += `<li class="correction">${msg}</li>`;
      });
      statusHtml += '</ul>';
    }

    statusDiv.innerHTML = statusHtml;

    if (result) {
      const resultDiv = eventContainer.querySelector('.result');
      if (result.error) {
        resultDiv.innerHTML = `<p class="error"><strong>Ошибка:</strong> ${result.error}</p>`;
      } else {
        resultDiv.innerHTML = `<pre>${JSON.stringify(result.result, null, 2)}</pre>`;
      }
    }
  }

  function createEventContainer(event) {
    const container = document.createElement('div');
    container.id = `event-${event.id}`;
    container.className = 'event-container';
    container.innerHTML = `
      <h2>Событие ID: ${event.id}</h2>
      <p><strong>Описание:</strong><br>${event.description || 'Нет описания'}</p>
      <p><strong>Исходный текст:</strong><br>${event.input.replace(/\\n/g,'<br>')}</p>
      <div class="status"></div>
      <div class="result"></div>
    `;
    output.appendChild(container);
    return container;
  }

  async function processNextEvent() {
    if (currentEventIndex >= events.length) {
      return;
    }

    const event = events[currentEventIndex];
    updateEventDisplay(event, 'Обработка...');
    updateCounter();

    try {
      const response = await fetch(`/process_single/${event.id}`);
      const result = await response.json();
      updateEventDisplay(event, 'Готово', result);
    } catch (error) {
      updateEventDisplay(event, 'Ошибка', { error: error.message });
    }

    currentEventIndex++;
    if (currentEventIndex < events.length) {
      setTimeout(processNextEvent, 500);
    }
  }

  btn.addEventListener('click', async () => {
    output.innerHTML = '';
    currentEventIndex = 0;
    counter.style.display = 'block';
    
    try {
      const response = await fetch('/get_events');
      events = await response.json();
      console.log(events);
      if (!Array.isArray(events)) {
        output.innerHTML = '<p class="error">Ошибка сервера или файл не найден.</p>';
        counter.style.display = 'none';
        return;
      }
      updateCounter();
      processNextEvent();
    } catch (err) {
      output.innerHTML = '<p class="error">Ошибка при загрузке: ' + err.message + '</p>';
      counter.style.display = 'none';
    }
  });
</script>
</body>
</html>
""" 