<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// --- СОСТОЯНИЕ ПРИЛОЖЕНИЯ (Реактивные переменные) ---
const uploadZoneActive = ref(true)   // Показывать ли зону загрузки
const isLoading = ref(false)         // Показывать ли спиннер
const resultData = ref(null)         // Хранит готовый результат от сервера
const selectedStyle = ref('brief')   // Выбранный стиль объявления
const errorMessage = ref('')         // Текст ошибки для вывода
const previewUrl = ref(null)         // URL для отображения превью загруженной картинки
const fileInput = ref(null)          // Ссылка на скрытый <input type="file">

// --- ЛОГИКА ИНТЕРФЕЙСА ---

// Имитация клика по скрытому <input>, когда пользователь кликает по зоне загрузки
const triggerFileInput = () => fileInput.value.click()

// Обработчик события выбора файла (клик или drag-and-drop)
const handleFileUpload = (event) => {
  const file = event.target.files?.[0] || event.dataTransfer?.files?.[0]
  if (file) processFile(file)
}

// Главная функция: отправка файла на сервер
const processFile = async (file) => {
  // 1. Клиентская валидация
  if (!file.type.startsWith('image/')) {
    showError('Пожалуйста, выберите файл изображения.')
    return
  }

  // 2. Смена состояния интерфейса (показываем загрузку)
  errorMessage.value = ''
  uploadZoneActive.value = false
  isLoading.value = true
  previewUrl.value = URL.createObjectURL(file) // Создаем локальное превью

  // 3. Формируем данные для отправки (multipart/form-data)
  const formData = new FormData()
  formData.append('image', file)
  formData.append('style', selectedStyle.value)

  try {
    // 4. Отправляем POST запрос. 
    const res = await axios.post('/api/generate-ad', formData)
    const taskId = res.data.task_id
    
    // 5. Сохраняем ID задачи в SessionStorage, чтобы не потерять при обновлении страницы (F5)
    sessionStorage.setItem('activeTaskId', taskId)
    sessionStorage.setItem('tempImageURL', previewUrl.value)
    
    // 6. Запускаем опрос сервера
    pollResults(taskId)
  } catch (err) {
    showError(err.response?.data?.detail || err.message)
  }
}

// --- ОПРОС СЕРВЕРА (Polling) ---
const pollResults = (taskId) => {
  // Запускаем интервал, который срабатывает каждые 3 секунды
  const interval = setInterval(async () => {
    try {
      const res = await axios.get(`/api/results/${taskId}`)
      
      if (res.status === 200) {
        // Результат готов
        clearInterval(interval) // Останавливаем таймер
        resultData.value = res.data // Сохраняем данные
        isLoading.value = false     // Скрываем спиннер
        sessionStorage.clear()      // Очищаем сессию
      }
      // Если статус 202, просто ничего не делаем, ждем следующего тика
    } catch (err) {
      // ПРОИЗОШЛА ОШИБКА (например, 500 от сервера)
      clearInterval(interval)
      showError(err.response?.data?.detail || 'Внутренняя ошибка сервера')
      sessionStorage.clear()
    }
  }, 3000)
}

// --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

// Функция для отображения ошибки и возврата к зоне загрузки
const showError = (msg) => {
  errorMessage.value = msg
  isLoading.value = false
  uploadZoneActive.value = true
}

// Сброс интерфейса для загрузки новой картинки
const reset = () => {
  resultData.value = null
  uploadZoneActive.value = true
  previewUrl.value = null
  if (fileInput.value) fileInput.value.value = ''
}

// Копирование текста в буфер обмена
const copyToClipboard = async () => {
  await navigator.clipboard.writeText(resultData.value.ad_text)
  alert('Текст скопирован!')
}

// --- ЖИЗНЕННЫЙ ЦИКЛ КОМПОНЕНТА ---
// onMounted срабатывает один раз при загрузке страницы.
// Мы проверяем SessionStorage: если там есть неоконченная задача, возобновляем опрос.
onMounted(() => {
  const savedId = sessionStorage.getItem('activeTaskId')
  if (savedId) {
    previewUrl.value = sessionStorage.getItem('tempImageURL')
    uploadZoneActive.value = false
    isLoading.value = true
    pollResults(savedId)
  }
})
</script>

<template>
  <main class="container my-5">
    <!-- Заголовок -->
    <div class="text-center mb-4">
      <h1 class="display-5 fw-bold">🏠 AI House Ad Generator</h1>
    </div>

    <!-- Блок отображения ошибок (появляется только если errorMessage не пустой) -->
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible fade show">
      <strong><i class="bi bi-exclamation-triangle-fill"></i> Ошибка:</strong> {{ errorMessage }}
      <button @click="errorMessage = ''" type="button" class="btn-close"></button>
    </div>

    <!-- БЛОК ВЫБОРА СТИЛЯ И ЗАГРУЗКИ (виден только если uploadZoneActive === true) -->
    <div v-if="uploadZoneActive">
      
      <!-- Выбор стиля -->
      <div class="text-center my-4">
        <p class="mb-2"><strong>Выберите стиль объявления:</strong></p>
        <div class="btn-group">
          <!-- Итерация (цикл) для создания кнопок. v-model связывает радио-кнопки с переменной selectedStyle -->
          <input type="radio" class="btn-check" value="brief" v-model="selectedStyle" id="s-brief">
          <label class="btn btn-outline-primary" for="s-brief">Краткий</label>
          
          <input type="radio" class="btn-check" value="professional" v-model="selectedStyle" id="s-prof">
          <label class="btn btn-outline-primary" for="s-prof">Профессиональный</label>

          <input type="radio" class="btn-check" value="social" v-model="selectedStyle" id="s-soc">
          <label class="btn btn-outline-primary" for="s-soc">Для соцсетей</label>
        </div>
      </div>

      <!-- Зона загрузки Drag & Drop -->
      <div @click="triggerFileInput"
           @dragover.prevent
           @drop.prevent="handleFileUpload"
           class="p-5 border border-2 border-dashed border-primary rounded-3 text-center drop-zone bg-light">
        <i class="bi bi-cloud-arrow-up-fill fs-1 text-primary"></i>
        <p class="mt-3 mb-1">Перетащите фото сюда или нажмите для выбора</p>
        <input type="file" ref="fileInput" @change="handleFileUpload" accept="image/*" class="d-none">
      </div>
    </div>

    <!-- БЛОК СПИННЕРА (виден только если isLoading === true) -->
    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div>
      <p class="mt-3">Анализируем изображение и пишем текст... Это может занять до минуты.</p>
    </div>

    <!-- БЛОК РЕЗУЛЬТАТОВ (виден только если resultData не null) -->
    <div v-if="resultData" class="card shadow-sm mt-4">
      <div class="card-body">
        <div class="row g-4">
          <!-- Левая колонка: Картинка -->
          <div class="col-lg-5">
            <h5 class="mb-3">Ваше изображение:</h5>
            <!-- v-bind:src или просто :src связывает атрибут с переменной previewUrl -->
            <img :src="previewUrl" class="img-fluid rounded border w-100 object-fit-cover" style="max-height: 400px;">
          </div>
          
          <!-- Правая колонка: Характеристики и текст -->
          <div class="col-lg-7">
            <h5 class="mb-3">🔍 Извлеченные характеристики:</h5>
            <ul class="list-group list-group-flush mb-4">
              <!-- Цикл по ключам и значениям словаря характеристик -->
              <li v-for="(val, key) in resultData.characteristics" :key="key" class="list-group-item">
                <strong>{{ key }}:</strong> {{ val }}
              </li>
            </ul>

            <div class="d-flex justify-content-between align-items-center mb-2">
              <h5 class="mb-0">✍️ Сгенерированное объявление:</h5>
              <button @click="copyToClipboard" class="btn btn-sm btn-outline-secondary">
                <i class="bi bi-clipboard"></i> Копировать
              </button>
            </div>
            <!-- v-model связывает textarea с текстом объявления -->
            <textarea v-model="resultData.ad_text" class="form-control" rows="8" readonly></textarea>
          </div>
        </div>
        
        <!-- Кнопка возврата -->
        <div class="text-center mt-4">
          <button @click="reset" class="btn btn-primary">Загрузить другое фото</button>
        </div>
      </div>
    </div>
  </main>
</template>

<style>
/* Стили для зоны загрузки */
.border-dashed { border-style: dashed !important; }
.drop-zone { transition: background-color 0.2s; cursor: pointer; }
.drop-zone:hover { background-color: #e9ecef !important; }
</style>