// Obtener los elementos del DOM
const processButton = document.getElementById('processButton');
const folderPicker = document.getElementById('folderPicker');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultContainer = document.getElementById('tabla-resultado');
const columnSelector = document.getElementById('Seleccionador');
const variableXSelector = document.getElementById('variableX');
const variableYSelector = document.getElementById('variableY');
const plotContainer = document.getElementById('interactive-plot');

// Manejar el clic en el botón para procesar los archivos
processButton.addEventListener('click', async () => {
    const files = folderPicker.files;

    if (files.length === 0) {
        alert("Por favor, selecciona una carpeta de archivos.");
        return;
    }

    loadingIndicator.style.display = 'inline-block';

    try {
        const folderData = Array.from(files).map(file => ({
            name: file.name,
            relativePath: file.webkitRelativePath
        }));

        const response = await fetch('/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folderData })
        });

        if (response.ok) {
            const result = await response.json();
            renderResults(JSON.parse(result.data));
            fetchColumnsAndFeatures();
        } else {
            const error = await response.json();
            alert(`Error del servidor: ${error.details}`);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error en el procesamiento de los archivos.");
    } finally {
        loadingIndicator.style.display = 'none';
    }
});

// Obtener las columnas y características del backend
async function fetchColumnsAndFeatures() {
    try {
        const response = await fetch('/get_columns');
        if (response.ok) {
            const result = await response.json();
            updateColumnSelector(result.columns);
            updateFeatureSelectors(result.features);
        } else {
            alert('Error al obtener las columnas y características.');
        }
    } catch (error) {
        console.error("Error al obtener las columnas:", error);
        alert("Error al obtener las columnas.");
    }
}

// Actualizar el selector de columnas
function updateColumnSelector(columns) {
    columnSelector.innerHTML = '';
    columns.forEach(column => {
        const option = document.createElement('option');
        option.value = column;
        option.textContent = column;
        columnSelector.appendChild(option);
    });
}

// Actualizar los selectores de variables X e Y
function updateFeatureSelectors(features) {
    variableXSelector.innerHTML = '';
    variableYSelector.innerHTML = '';

    features.forEach(feature => {
        const optionX = document.createElement('option');
        const optionY = document.createElement('option');
        optionX.value = feature;
        optionY.value = feature;
        optionX.textContent = feature;
        optionY.textContent = feature;
        variableXSelector.appendChild(optionX);
        variableYSelector.appendChild(optionY);
    });
}

// Mostrar los resultados en una tabla
function renderResults(data) {
    if (!data || data.length === 0) {
        resultContainer.innerHTML = '<p>No hay datos para mostrar.</p>';
        return;
    }

    let html = '<table border="1"><thead><tr>';
    const keys = Object.keys(data[0]);
    keys.forEach(key => html += `<th>${key}</th>`);
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        keys.forEach(key => html += `<td>${row[key]}</td>`);
        html += '</tr>';
    });
    html += '</tbody></table>';

    resultContainer.innerHTML = html;
}

// Manejar la selección de columnas y generar el gráfico
columnSelector.addEventListener('change', async () => {
    const selectedColumns = Array.from(columnSelector.selectedOptions).map(option => option.value);
    const variableX = variableXSelector.value || 'dias';
    const variableY = variableYSelector.value || 'Ext%Cu_IL';

    if (selectedColumns.length === 0) {
        alert("Seleccione al menos una columna.");
        return;
    }

    try {
        const response = await fetch('/get_filtered_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ columns: selectedColumns, variableX, variableY })
        });

        if (response.ok) {
            const data = await response.json();
            renderScatterPlot(data);
        } else {
            const error = await response.json();
            alert(`Error del servidor: ${error.details}`);
        }
    } catch (error) {
        console.error("Error al obtener datos filtrados:", error);
    }
});

// Renderizar el gráfico interactivo
function renderScatterPlot(data) {
    const trace = {
        x: data.x,
        y: data.y,
        mode: 'markers',
        type: 'scatter',
        text: data.label,
        marker: { size: 10 }
    };

    const layout = {
        title: 'Gráfico Interactivo',
        xaxis: { title: variableXSelector.value || 'Días' },
        yaxis: { title: variableYSelector.value || 'Ext%Cu_IL' },
        margin: { l: 40, r: 40, t: 40, b: 40 }
    };

    Plotly.newPlot(plotContainer, [trace], layout);
}