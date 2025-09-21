document.addEventListener('DOMContentLoaded', () => { 

    // Backend URLs for different services
    const BACKEND_PROXY_URL = '/api/agent';
    const RAG_QUERY_URL = '/api/rag-query';
    const TABLE_DATA_URL = '/api/table';
    const TABLES_URL = '/api/tables'; 

 

    // --- Element References --- 

    const searchBar = document.getElementById('search-bar'); 

    const voiceBtn = document.getElementById('voice-btn'); 

    const contentArea = document.getElementById('content-area'); 

    const filterButtons = document.querySelectorAll('.quick-filters button'); 

    const userGreeting = document.getElementById('user-greeting'); 

    const mainBody = document.getElementById('main-body'); 

    const dashboardBtn = document.getElementById('dashboard-btn');

    const dashboardPage = document.getElementById('dashboard-page');

    const backToMainBtn = document.getElementById('back-to-main');

    const tableButtons = document.querySelectorAll('.table-btn');

    let fullDataset = []; 

 

    // --- Robust Count-Up Animation --- 

    function animateCounts() { 

        const countElements = document.querySelectorAll('.count-number'); 

        countElements.forEach(el => { 

            const target = parseInt(el.dataset.target); 

            const duration = 2000; // 2 seconds 

            let startTime = null; 

 

            function animationStep(timestamp) { 

                if (!startTime) startTime = timestamp; 

                const progress = Math.min((timestamp - startTime) / duration, 1); 

                const currentVal = Math.floor(progress * target); 

                el.innerHTML = currentVal.toLocaleString(); 

                if (progress < 1) { 

                    window.requestAnimationFrame(animationStep); 

                } 

            } 

            window.requestAnimationFrame(animationStep); 

        }); 

    } 

    animateCounts(); 

 

    // --- 1. Load Available Tables and Initialize --- 
    let availableTables = [];
    
    async function loadAvailableTables() {
        try {
            const response = await fetch(TABLES_URL);
            const data = await response.json();
            availableTables = data.tables;
            console.log('Available tables:', availableTables);
            
            // Load default table data (order_request)
            if (availableTables.includes('order_request')) {
                await loadTableData('order_request');
            }
        } catch (error) {
            console.error('Error loading tables:', error);
            contentArea.innerHTML = '<p style="color:orange;">Error connecting to database. Please check if the server is running.</p>';
        }
    }
    
    async function loadTableData(tableName) {
        try {
            const response = await fetch(`${TABLE_DATA_URL}/${tableName}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            fullDataset = data.data;
            displayTable(fullDataset.slice(0, 50), `${tableName} (First 50)`);
        } catch (error) {
            console.error('Error loading table data:', error);
            contentArea.innerHTML = `<p style="color:orange;">Error loading ${tableName} data: ${error.message}</p>`;
        }
    }
    
    // Initialize the application
    loadAvailableTables();
    
    // Real-time update mechanism
    let currentChartQuery = null;
    let autoRefreshInterval = null;
    
    function startAutoRefresh(query) {
        currentChartQuery = query;
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
        }
        
        // Refresh every 30 seconds for real-time updates
        autoRefreshInterval = setInterval(() => {
            if (currentChartQuery) {
                handleSearchQuery(currentChartQuery);
            }
        }, 30000); // 30 seconds
    }
    
    function stopAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
        currentChartQuery = null;
    } 

 

    // --- Voice Assistant Logic --- 

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition; 

    const SpeechSynthesis = window.speechSynthesis; 

    const SpeechGrammarList = window.SpeechGrammarList || window.webkitSpeechGrammarList; 

    const SpeechGrammar = window.SpeechGrammar || window.webkitSpeechGrammar; 

    let recognitionTimeout; 

     

    // Flag to manage the state of the voice recognition 

    let isListeningForQuery = false; 

    let recognitionActive = null;
    let wakeWordRecognitionActive = false;
    let queryRecognitionActive = false; 

 

    if (SpeechRecognition && SpeechGrammarList) { 

        // Define grammar for wake word 

        const grammarStr = '#JSGF V1.0; grammar wake; public <wake> = hey accurate | accurate;'; 

        const speechRecognitionList = new SpeechGrammarList(); 

        speechRecognitionList.addFromString(grammarStr, 1); 

 

        // Function to handle speaking with a promise 

        const speak = (text) => { 

            return new Promise(resolve => { 

                const utterance = new SpeechSynthesisUtterance(text); 

                utterance.onstart = () => { 

                    mainBody.classList.add('is-active-listening'); 

                    voiceBtn.classList.add('is-speaking'); 

                }; 

                utterance.onend = () => { 

                    mainBody.classList.remove('is-active-listening'); 

                    voiceBtn.classList.remove('is-speaking'); 

                    resolve(); // Resolve the promise when speech ends 

                }; 

                SpeechSynthesis.speak(utterance); 

            }); 

        }; 

 

        // Recognition for the wake word "hey accurate" 

        const wakeWordRecognition = new SpeechRecognition(); 

        wakeWordRecognition.grammars = speechRecognitionList; 

        wakeWordRecognition.lang = 'en-US'; 

        wakeWordRecognition.continuous = true; 

        wakeWordRecognition.interimResults = false; 

 

        wakeWordRecognition.onstart = () => { 

            console.log('Listening for wake word "hey accurate"...'); 

            recognitionActive = wakeWordRecognition; 
            wakeWordRecognitionActive = true;

            // Do not add is-speaking here to avoid constant glow 

        }; 

 

        wakeWordRecognition.onresult = (event) => { 

            const transcript = event.results[event.results.length - 1][0].transcript.trim().toLowerCase(); 

            console.log('Transcript:', transcript); 

            if (transcript.includes('hey accurate') || transcript.includes('accurate') && !isListeningForQuery) { 

                isListeningForQuery = true; 

                wakeWordRecognition.stop(); 

                 

                speak('Hey user, how can I help you?').then(() => { 

                    userGreeting.textContent = 'How can I help you?'; 

                    searchBar.placeholder = 'Listening...'; 

                     

                    setTimeout(() => { 
                        if (!queryRecognitionActive) {
                            queryRecognition.start(); 
                        }
                    }, 500);  

                }); 

            } 

        }; 

 

        wakeWordRecognition.onend = () => { 

             // We only restart the wake word recognition if the query isn't active 

            wakeWordRecognitionActive = false;
            if (!isListeningForQuery && !wakeWordRecognitionActive) { 

                setTimeout(() => {
                    if (!wakeWordRecognitionActive && !isListeningForQuery) {
                        wakeWordRecognition.start(); 
                    }
                }, 100);

            } 

        }; 

 

        wakeWordRecognition.onerror = (event) => { 

            console.error('Wake word recognition error:', event.error); 
            wakeWordRecognitionActive = false;

            if (!isListeningForQuery && !wakeWordRecognitionActive) { 

                setTimeout(() => {
                    if (!wakeWordRecognitionActive && !isListeningForQuery) {
                        wakeWordRecognition.start(); 
                    }
                }, 1000);

            } 

        }; 

         

        // Recognition for the user's query 

        const queryRecognition = new SpeechRecognition(); 

        queryRecognition.lang = 'en-US'; 

        queryRecognition.continuous = false; 

        queryRecognition.interimResults = false; 

 

        queryRecognition.onstart = () => { 

            console.log('Listening for query...'); 
            queryRecognitionActive = true;

            clearTimeout(recognitionTimeout); 

            mainBody.classList.add('is-active-listening'); 

            searchBar.placeholder = 'Listening...'; 

            userGreeting.textContent = 'How can I help you?'; 

            voiceBtn.classList.add('is-speaking'); 

             

            // Set a timeout to stop listening after 5 seconds of silence 

            recognitionTimeout = setTimeout(() => { 

                queryRecognition.stop(); 

            }, 10000); 

        }; 

 

        queryRecognition.onresult = (event) => { 

            clearTimeout(recognitionTimeout); 

            const transcript = event.results[0][0].transcript; 

            console.log('User said:', transcript); 

            searchBar.value = transcript; 

            handleSearchQuery(transcript); 

        }; 

 

        queryRecognition.onend = () => { 

            clearTimeout(recognitionTimeout); 
            queryRecognitionActive = false;

            isListeningForQuery = false; 

            searchBar.placeholder = 'Ask anything about your data...'; 

            userGreeting.textContent = 'Hey User, How can I help you?'; 

            mainBody.classList.remove('is-active-listening'); 

            voiceBtn.classList.remove('is-speaking'); 

            if (!wakeWordRecognitionActive) {
                setTimeout(() => {
                    if (!wakeWordRecognitionActive && !isListeningForQuery) {
                        wakeWordRecognition.start(); 
                    }
                }, 500);
            }

        }; 

 

        queryRecognition.onerror = (event) => { 

            console.error('Query recognition error:', event.error); 
            queryRecognitionActive = false;

            isListeningForQuery = false; 

            searchBar.placeholder = 'Ask anything about your data...'; 

            userGreeting.textContent = 'Hey User, How can I help you?'; 

            mainBody.classList.remove('is-active-listening'); 

            voiceBtn.classList.remove('is-speaking'); 

            if (!wakeWordRecognitionActive) {
                setTimeout(() => {
                    if (!wakeWordRecognitionActive && !isListeningForQuery) {
                        wakeWordRecognition.start(); 
                    }
                }, 1000);
            }

        }; 

 

        // Start listening for the wake word when the page loads 
        if (!wakeWordRecognitionActive) {
            wakeWordRecognition.start();
        } 

         

        // Manual button click to start a query 

        voiceBtn.addEventListener('click', () => { 

            if (wakeWordRecognitionActive) {
                wakeWordRecognition.stop(); 
            }

            isListeningForQuery = true; 

            speak('How can I help you?').then(() => { 

                userGreeting.textContent = 'How can I help you?'; 

                searchBar.placeholder = 'Listening...'; 

                setTimeout(() => { 
                    if (!queryRecognitionActive) {
                        queryRecognition.start(); 
                    }
                }, 500); 

            }); 

        }); 

    } 

 

    // --- 3. The RAG Query Handler --- 

    searchBar.addEventListener('keypress', (e) => { 

        if (e.key === 'Enter') handleSearchQuery(searchBar.value); 

    }); 

 

    async function handleSearchQuery(query) { 

        contentArea.innerHTML = `<h2><i class="fas fa-spinner fa-spin"></i> Thinking...</h2>`; 

 

        try { 

            // Call the RAG endpoint for natural language queries

            const response = await fetch(RAG_QUERY_URL, { 

                method: 'POST', 

                headers: { 'Content-Type': 'application/json' }, 

                body: JSON.stringify({ query: query }) 

            }); 

            

            if (!response.ok) { 

                throw new Error(`RAG query failed! status: ${response.status}`); 

            } 

            

            const result = await response.json(); 

             

            if (result.error) { 

                contentArea.innerHTML = `<p style="color:orange;">${result.error}</p>`;

                if (result.suggested_tables) {

                    contentArea.innerHTML += `<p>Available tables: ${result.suggested_tables.join(', ')}</p>`;

                }

                return;

            } 

 

            // Handle different types of RAG responses

            handleRAGResponse(result, query);
            
            // Start auto-refresh for chart queries
            if (result.type === 'chart') {
                startAutoRefresh(query);
            } else {
                stopAutoRefresh();
            }

             

        } catch (error) { 

            console.error('Error with RAG Query:', error); 

            contentArea.innerHTML = `<p style="color:orange;">There was an error communicating with the RAG backend. Is the Python server running? Check the console for details.</p>`; 

        } 

    }
    
    function handleRAGResponse(result, originalQuery) {
        const { type, message, data, columns, value, chart_type } = result;
        
        switch (type) {
            case 'count':
                displayCountResult(value, message);
                break;
                
            case 'unique':
                displayUniqueValues(result.column, result.values, message);
                break;
                
            case 'chart':
                displayChart(result);
                break;
                
            case 'error':
                displayError(result);
                break;
                
            case 'distribution':
                if (chart_type === 'histogram') {
                    displayHistogram(result.column, data, message);
                } else {
                    displayBarChart(result.column, data, message);
                }
                break;
                
            case 'time_filter':
                displayTimeFilterResult(result.count, message);
                break;
                
            case 'sample':
            default:
                displayTable(data, message);
                break;
        }
    }
    
    function displayCountResult(count, message) {
        contentArea.innerHTML = `
            <div class="count-result">
                <h2><i class="fas fa-chart-bar"></i> Query Result</h2>
                <div class="count-display">
                    <span class="count-number">${count.toLocaleString()}</span>
                    <p class="count-message">${message}</p>
                </div>
            </div>
        `;
    }
    
    function displayUniqueValues(column, values, message) {
        contentArea.innerHTML = `
            <div class="unique-result">
                <h2><i class="fas fa-list"></i> Unique Values</h2>
                <p class="result-message">${message}</p>
                <div class="unique-values">
                    ${values.map(value => `<span class="unique-value">${value}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    function displayTimeFilterResult(count, message) {
        contentArea.innerHTML = `
            <div class="time-filter-result">
                <h2><i class="fas fa-clock"></i> Time Filter Result</h2>
                <div class="count-display">
                    <span class="count-number">${count.toLocaleString()}</span>
                    <p class="count-message">${message}</p>
                </div>
            </div>
        `;
    }
    
    function displayError(errorResult) {
        const { message, suggested_chart, column, table } = errorResult;
        
        let suggestionHtml = '';
        if (suggested_chart) {
            suggestionHtml = `
                <div class="error-suggestion">
                    <p><strong>💡 Suggestion:</strong> Try asking for a "${suggested_chart} chart" instead, or select a different column.</p>
                    <button class="suggestion-btn" onclick="handleSearchQuery('${suggested_chart} chart of ${column}')">
                        <i class="fas fa-chart-pie"></i> Create ${suggested_chart} chart
                    </button>
                </div>
            `;
        }
        
        contentArea.innerHTML = `
            <div class="error-result">
                <h2><i class="fas fa-exclamation-triangle"></i> Chart Error</h2>
                <div class="error-message">
                    <p>${message}</p>
                    ${suggestionHtml}
                </div>
            </div>
        `;
    }
    
    function displayChart(chartData) {
        const { chart_type, title, labels, data, column, table, total_records, insights, is_numeric } = chartData;
        
        // Generate insights HTML
        let insightsHtml = '';
        if (insights && insights.length > 0) {
            insightsHtml = `
                <div class="insights-section">
                    <h3><i class="fas fa-lightbulb"></i> Data Insights</h3>
                    <div class="insights-list">
                        ${insights.map(insight => `<div class="insight-item">${insight}</div>`).join('')}
                    </div>
                </div>
            `;
        }
        
        contentArea.innerHTML = `
            <div class="chart-container">
                <div class="chart-header">
                    <h2><i class="fas fa-chart-${chart_type === 'line' ? 'line' : chart_type === 'pie' ? 'pie' : 'bar'}"></i> ${title}</h2>
                    <div class="chart-controls">
                        <button id="refresh-chart" class="refresh-btn" title="Refresh Chart">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                        <button id="auto-refresh" class="auto-refresh-btn" title="Auto Refresh (30s)">
                            <i class="fas fa-clock"></i>
                        </button>
                    </div>
                </div>
                <div class="chart-info">
                    <span class="info-item"><i class="fas fa-table"></i> Table: ${table}</span>
                    <span class="info-item"><i class="fas fa-columns"></i> Column: ${column}</span>
                    <span class="info-item"><i class="fas fa-database"></i> Records: ${total_records.toLocaleString()}</span>
                    <span class="info-item"><i class="fas fa-chart-${is_numeric ? 'line' : 'bar'}"></i> Type: ${is_numeric ? 'Numerical' : 'Categorical'}</span>
                </div>
                <div class="chart-wrapper">
                    <canvas></canvas>
                </div>
                ${insightsHtml}
                <p class="last-updated">Last updated: ${new Date().toLocaleTimeString()}</p>
            </div>
        `;
        
        // Get the canvas from the wrapper
        const canvas = contentArea.querySelector('.chart-wrapper canvas');
        
        // Add event listeners for refresh controls
        const refreshBtn = document.getElementById('refresh-chart');
        const autoRefreshBtn = document.getElementById('auto-refresh');
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (currentChartQuery) {
                    handleSearchQuery(currentChartQuery);
                }
            });
        }
        
        if (autoRefreshBtn) {
            autoRefreshBtn.addEventListener('click', () => {
                if (autoRefreshInterval) {
                    stopAutoRefresh();
                    autoRefreshBtn.innerHTML = '<i class="fas fa-clock"></i>';
                    autoRefreshBtn.title = 'Start Auto Refresh (30s)';
                } else {
                    startAutoRefresh(currentChartQuery);
                    autoRefreshBtn.innerHTML = '<i class="fas fa-pause"></i>';
                    autoRefreshBtn.title = 'Stop Auto Refresh';
                }
            });
        }
        
        let chartConfig = {
            type: chart_type,
            data: {
                labels: labels,
                datasets: [{
                    label: column,
                    data: data,
                    backgroundColor: chart_type === 'line' ? 'rgba(0, 169, 255, 0.1)' : 
                                   chart_type === 'pie' ? [
                                       'rgba(0, 169, 255, 0.8)',
                                       'rgba(228, 0, 124, 0.8)',
                                       'rgba(32, 201, 151, 0.8)',
                                       'rgba(255, 193, 7, 0.8)',
                                       'rgba(108, 117, 125, 0.8)'
                                   ] : 'rgba(0, 169, 255, 0.6)',
                    borderColor: chart_type === 'line' ? 'rgba(0, 169, 255, 1)' : 'rgba(0, 169, 255, 1)',
                    borderWidth: chart_type === 'line' ? 3 : 1,
                    fill: chart_type === 'line' ? true : false,
                    tension: chart_type === 'line' ? 0.4 : 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 10
                    }
                },
                scales: chart_type !== 'pie' ? {
                    y: { 
                        ticks: { color: '#E2E8F0', maxTicksLimit: 8 }, 
                        grid: { color: 'rgba(226, 232, 240, 0.2)' } 
                    },
                    x: { 
                        ticks: { color: '#E2E8F0', maxTicksLimit: 10 }, 
                        grid: { color: 'transparent' } 
                    }
                } : {},
                plugins: { 
                    legend: { 
                        labels: { color: '#E2E8F0' },
                        position: chart_type === 'pie' ? 'bottom' : 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#E2E8F0',
                        bodyColor: '#E2E8F0'
                    }
                }
            }
        };
        
        new Chart(canvas, chartConfig);
    }

    function displayHistogram(column, data, message) {
        const canvas = document.createElement('canvas');
        contentArea.innerHTML = `<h2><i class="fas fa-chart-area"></i> ${message}</h2>`;
        contentArea.appendChild(canvas);
        
        const labels = Object.keys(data);
        const values = Object.values(data);
        
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: `Distribution of ${column}`,
                    data: values,
                    backgroundColor: 'rgba(0, 169, 255, 0.6)',
                    borderColor: 'rgba(0, 169, 255, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { 
                        ticks: { color: '#E2E8F0' }, 
                        grid: { color: 'rgba(226, 232, 240, 0.2)' } 
                    },
                    x: { 
                        ticks: { color: '#E2E8F0' }, 
                        grid: { color: 'transparent' } 
                    }
                },
                plugins: { 
                    legend: { labels: { color: '#E2E8F0' } } 
                }
            }
        });
    } 

 

    // --- 4. "Tools" - The JavaScript functions the AI can call --- 

    function showTable(statusFilter = 'All') { 

        filterButtons.forEach(btn => btn.classList.remove('active')); 

        const targetButton = document.querySelector(`.quick-filters button[data-status="${statusFilter}"]`); 

        if(targetButton) targetButton.classList.add('active'); 

         

        const data = (statusFilter === 'All') ? fullDataset : fullDataset.filter(row => row.Order_Status === statusFilter); 

         

        // Check for no data and speak the message 

        if (data.length === 0) { 

            speak("Sorry, couldn't find the relevant data."); 

        } 

         

        displayTable(data.slice(0, 50), `${statusFilter} Orders`); 

    } 

 

    function createGraph(groupByField) { 

        createBarChart(fullDataset, groupByField, `Orders by ${groupByField}`); 

    } 

 

    function showPassFailRate() { 

        createDonutChart(countBy(fullDataset, 'Final_Result'), 'Completion Status Summary'); 

    } 

 

    function calculateAverageTAT() { 

        const avgTime = calculateAverage(fullDataset, 'TurnaroundTime'); 

        displayStats({ 'Average Turnaround Time': `${avgTime.toFixed(2)} Days` }, 'TAT Analysis'); 

    } 

 

    // --- 5. Content Generation & Other Functions --- 

    function displayTable(data, title) { 

        contentArea.innerHTML = ''; 

        if (!data || data.length === 0) { 

            contentArea.innerHTML = `<h2>${title}</h2><p>No data available.</p>`; 

            return; 

        } 

        const headers = Object.keys(data[0]); 

        let tableHTML = `<h2>${title}</h2><table><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>`; 

        data.forEach(row => { 

            tableHTML += `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`; 

        }); 

        tableHTML += `</tbody></table>`; 

        contentArea.innerHTML = tableHTML; 

    } 

 

    function createDonutChart(data, title) { 

        const canvas = document.createElement('canvas'); 

        contentArea.innerHTML = `<h2>${title}</h2>`; 

        contentArea.appendChild(canvas); 

        new Chart(canvas, { 

            type: 'doughnut', 

            data: { 

                labels: Object.keys(data), 

                datasets: [{ 

                    label: 'Count', 

                    data: Object.values(data), 

                    backgroundColor: ['#00A9FF', '#E4007C', '#20c997'], 

                    borderColor: '#0A1931', 

                    borderWidth: 4 

                }] 

            }, 

            options: { 

                responsive: true, 

                plugins: { legend: { labels: { color: '#E2E8F0' } } } 

            } 

        }); 

    } 

     

    function createBarChart(data, categoryField, title) { 

        const counts = countBy(data, categoryField); 

        const canvas = document.createElement('canvas'); 

        contentArea.innerHTML = `<h2>${title}</h2>`; 

        contentArea.appendChild(canvas); 

        new Chart(canvas, { 

            type: 'bar', 

            data: { 

                labels: Object.keys(counts), 

                datasets: [{ 

                    label: title, 

                    data: Object.values(counts), 

                    backgroundColor: 'rgba(0, 169, 255, 0.6)', 

                    borderColor: 'rgba(0, 169, 255, 1)', 

                    borderWidth: 1, 

                    borderRadius: 5 

                }] 

            }, 

            options: { 

                scales: { 

                    y: { ticks: { color: '#E2E8F0' }, grid: { color: 'rgba(226, 232, 240, 0.2)' } }, 

                    x: { ticks: { color: '#E2E8F0' }, grid: { color: 'transparent' } } 

                }, 

                plugins: { legend: { labels: { color: '#E2E8F0' } } } 

            } 

        }); 

    } 

 

    function displayStats(stats, title) { 

        contentArea.innerHTML = ''; 

        let statsHTML = `<h2>${title}</h2><div class="stats-grid">`; 

        for (const [key, value] of Object.entries(stats)) { 

            statsHTML += `<div class="stat-card"><h3>${key}</h3><p>${value}</p></div>`; 

        } 

        statsHTML += `</div>`; 

        contentArea.innerHTML = statsHTML; 

    } 

     

    filterButtons.forEach(button => { 

        button.addEventListener('click', () => { 

            showTable(button.dataset.status); 

        }); 

    }); 

 

    function countBy(data, key) { 

        const counts = {}; 

        for(const row of data){ 

            const value = row[key] || 'N/A'; 

            counts[value] = (counts[value] || 0) + 1; 

        } 

        return counts; 

    } 

 

    function calculateAverage(data, key) { 

        let total = 0; 

        let count = 0; 

        data.forEach(row => { 

            const value = parseFloat(row[key]); 

            if (!isNaN(value)) { 

                total += value; 

                count++; 

            } 

        }); 

        return count > 0 ? total / count : 0; 

    } 

    // --- Dashboard Navigation ---
    
    // Show dashboard page
    dashboardBtn.addEventListener('click', () => {
        dashboardPage.classList.remove('hidden');
        mainBody.style.overflow = 'hidden';
    });

    // Hide dashboard page and return to main
    backToMainBtn.addEventListener('click', () => {
        dashboardPage.classList.add('hidden');
        mainBody.style.overflow = 'auto';
    });

    // Handle table button clicks
    tableButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const tableName = button.dataset.table;
            console.log(`Clicked on table: ${tableName}`);
            
            // Map display names to actual table names
            const tableMapping = {
                'Search_status': 'search_status',
                'Search Table': 'search_status', 
                'Search_Type Table': 'search_type',
                'Subject Table': 'subject',
                'Company Table': 'company',
                'Package Table': 'package',
                'Order_Request Table': 'order_request'
            };
            
            const actualTableName = tableMapping[tableName] || tableName.toLowerCase().replace(' table', '');
            
            if (availableTables.includes(actualTableName)) {
                await loadTableData(actualTableName);
            } else {
                contentArea.innerHTML = `<p style="color:orange;">Table ${actualTableName} not found. Available tables: ${availableTables.join(', ')}</p>`;
            }
            
            // Return to main page after clicking
            dashboardPage.classList.add('hidden');
            mainBody.style.overflow = 'auto';
        });
    });

    // Close dashboard when clicking outside (optional)
    dashboardPage.addEventListener('click', (e) => {
        if (e.target === dashboardPage) {
            dashboardPage.classList.add('hidden');
            mainBody.style.overflow = 'auto';
        }
    });

}); 