document.addEventListener('DOMContentLoaded', () => {

    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const loader = document.getElementById('loader');
    const resultArea = document.getElementById('result-area');
    const resetButton = document.getElementById('reset-button');
    
    // Элементы для вывода результата
    const resultImage = document.getElementById('result-image');
    const characteristicsList = document.getElementById('characteristics-list');
    const adTextArea = document.getElementById('ad-text-area');
    const copyButton = document.getElementById('copy-button');

    // Элементы для вывода ошибок
    const errorAlert = document.getElementById('error-alert');
    const errorMessage = document.getElementById('error-message');

    uploadZone.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            handleFile(file);
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
    });
    uploadZone.addEventListener('drop', (event) => {
        const file = event.dataTransfer.files[0];
        if (file) {
            handleFile(file);
        }
    });

    resetButton.addEventListener('click', () => {
        resultArea.style.display = 'none';
        uploadZone.style.display = 'block';
        if (errorAlert) errorAlert.style.display = 'none';
        fileInput.value = '';
    });
    
    copyButton.addEventListener('click', () => {
        adTextArea.select();
        navigator.clipboard.writeText(adTextArea.value).then(() => {
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '<i class="bi bi-check-lg"></i> Скопировано!';
            setTimeout(() => {
                copyButton.innerHTML = originalText;
            }, 2000);
        }).catch(err => {
            console.error('Не удалось скопировать текст: ', err);
            displayError("Ошибка при копировании текста. Возможно, ваш браузер не поддерживает эту функцию.");
        });
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    async function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            displayError('Пожалуйста, выберите файл изображения.');
            return;
        }
        if (errorAlert) errorAlert.style.display = 'none';
        uploadZone.style.display = 'none';
        resultArea.style.display = 'none';
        loader.style.display = 'block';

        const formData = new FormData();
        formData.append('image', file);
        const selectedStyle = document.querySelector('input[name="style"]:checked').value;
        formData.append('style', selectedStyle);

        const tempImageURL = URL.createObjectURL(file);

        try {
            // 1. Отправляем файл и получаем ID задачи
            const response = await fetch('/generate-ad', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`);
            }
            const taskData = await response.json();
            const taskId = taskData.task_id;

            sessionStorage.setItem('activeTaskId', taskId);
            sessionStorage.setItem('tempImageURL', tempImageURL);

            // 2. Начинаем "опрашивать" сервер о готовности результата
            pollForResult(taskId, file);

        } catch (error) {
            console.error('Ошибка при отправке файла:', error);
            displayError(error.message);
        }
    }

    function checkSessionForActiveTask() {
        const activeTaskId = sessionStorage.getItem('activeTaskId');
        const tempImageURL = sessionStorage.getItem('tempImageURL');

        if (activeTaskId && tempImageURL) {
            console.log(`Найдена активная задача ${activeTaskId}. Возобновляем опрос...`);
            const pseudoFile = { isPseudo: true, url: tempImageURL };
            
            uploadZone.style.display = 'none';
            loader.style.display = 'block';
            pollForResult(activeTaskId, pseudoFile);
        }
    }
    
    /**
     * Периодически запрашивает результат для задачи с указанным ID
     * @param {string} taskId - ID задачи
     * @param {File} originalFile - Исходный файл для превью
     */
    function pollForResult(taskId, originalFile) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/results/${taskId}`);

                if (response.status === 200) {
                    // Результат готов
                    clearInterval(interval);

                    sessionStorage.removeItem('activeTaskId');
                    sessionStorage.removeItem('tempImageURL');

                    const data = await response.json();
                    displayResult(data, originalFile);
                    loader.style.display = 'none';
                } else if (response.status === 202) {
                    // Еще в процессе, просто ждем следующего опроса
                    console.log(`Задача ${taskId} еще в процессе...`);
                } else {
                    clearInterval(interval);

                    sessionStorage.removeItem('activeTaskId');
                    sessionStorage.removeItem('tempImageURL');

                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Неизвестная ошибка на сервере при обработке.");
                }
            } catch (error) {
                clearInterval(interval);

                sessionStorage.removeItem('activeTaskId');
                sessionStorage.removeItem('tempImageURL');

                console.error('Ошибка при опросе результата:', error);
                displayError(error.message);
            }
        }, 3000);
    }

    function displayResult(data, originalFile) {
        resultImage.src = originalFile.isPseudo ? originalFile.url : URL.createObjectURL(originalFile);

        characteristicsList.innerHTML = '';
        for (const [key, value] of Object.entries(data.characteristics)) {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.innerHTML = `<strong>${key}:</strong> ${value}`;
            characteristicsList.appendChild(li);
        }

        adTextArea.value = data.ad_text;
        resultArea.style.display = 'block';
    }

    function displayError(message) {
        if (errorMessage) {
            errorMessage.textContent = message;
        }
        if (errorAlert) {
            errorAlert.style.display = 'block';
        }

        loader.style.display = 'none';
        uploadZone.style.display = 'block';
        resultArea.style.display = 'none';
    }
    checkSessionForActiveTask();
});