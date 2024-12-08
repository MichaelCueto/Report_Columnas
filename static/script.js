// Obtener los elementos del DOM
const processButton = document.getElementById('processButton');
const folderPicker = document.getElementById('folderPicker');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultContainer = document.getElementById('tabla-resultado');
const columnSelector = document.getElementById('Seleccionador');

// Manejar el clic en el botón para procesar los archivos
processButton.addEventListener('click', async () => {
    const files = folderPicker.files;

    if (files.length === 0) {
        alert("Por favor, selecciona archivos para procesar.");
        return;
    }

    loadingIndicator.style.display = 'inline-block'; // Mostrar el indicador de carga

    try {
        const formData = new FormData();
        Array.from(files).forEach(file => {
            console.log(`Archivo seleccionado: ${file.name}`);
            formData.append('files', file);
        });

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            renderResults(JSON.parse(result.data));
        } else {
            const error = await response.json();
            alert(`Error del servidor: ${error.details}`);
        }
    } catch (error) {
        console.error("Error en el frontend:", error);
        alert("Error en el procesamiento de los archivos.");
    } finally {
        loadingIndicator.style.display = 'none'; // Ocultar el indicador de carga
    }
});

columnSelector.addEventListener('click', async () => {
    try {
        const response = await fetch('/get_columns', {
            method: 'GET'
        });

        if (response.ok) {
            const result = await response.json();

            // Limpiar las opciones existentes
            columnSelector.innerHTML = '<option value="" disabled selected>Seleccione las columnas</option>';

            // Agregar las nuevas opciones
            result.columns.forEach(column => {
                const option = document.createElement('option');
                option.value = column;
                option.textContent = column;
                columnSelector.appendChild(option);
            });
        } else {
            alert('Error al obtener las columnas.');
        }
    } catch (error) {
        console.error('Error al obtener las columnas:', error);
        alert('Hubo un problema al obtener las columnas.');
    }
});

// Mostrar los resultados en una tabla
function renderResults(data) {
    if (!data || data.length === 0) {
        resultContainer.innerHTML = '<p>No hay datos para mostrar.</p>';
        return;
    }

    let resultHTML = '<table border="1"><thead><tr>';
    const keys = Object.keys(data[0]);
    keys.forEach(key => {
        resultHTML += `<th>${key}</th>`;
    });
    resultHTML += '</tr></thead><tbody>';

    data.forEach(row => {
        resultHTML += '<tr>';
        keys.forEach(key => {
            resultHTML += `<td>${row[key]}</td>`;
        });
        resultHTML += '</tr>';
    });
    resultHTML += '</tbody></table>';

    resultContainer.innerHTML = resultHTML;
}
