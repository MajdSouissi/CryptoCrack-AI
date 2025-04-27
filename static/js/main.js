document.addEventListener('DOMContentLoaded', function() {
    // Mode et méthode de traitement
    const modeSelect = document.getElementById('mode-select');
    const decryptOptions = document.getElementById('decrypt-options');
    const encryptOptions = document.getElementById('encrypt-options');
    const decryptMethodSelect = document.getElementById('decrypt-method-select');
    const processBtnText = document.getElementById('process-btn-text');
    const keyInput = document.getElementById('key-input');
    const keyHelp = document.getElementById('key-help');
    const cipherSelect = document.getElementById('cipher-select');

    // Éléments d'entrée et de résultat
    const inputText = document.getElementById('input-text');
    const resultText = document.getElementById('result-text');
    const processBtn = document.getElementById('process-btn');
    const copyBtn = document.getElementById('copy-btn');
    const loading = document.getElementById('loading');

    // Éléments d'analyse
    const detectionInfo = document.getElementById('detection-info');
    const detectedCipher = document.getElementById('detected-cipher');
    const confidenceBar = document.getElementById('confidence-bar');
    const confidenceValue = document.getElementById('confidence-value');
    const detectedLanguage = document.getElementById('detected-language');
    const usedKey = document.getElementById('used-key');

    // Variables pour les graphiques
    let frequencyChart, bigramChart, entropyChart, autocorrChart;

    // Gestion de la visibilité des options
    function toggleModeOptions() {
        if (modeSelect.value === 'decrypt') {
            decryptOptions.classList.remove('hidden');
            encryptOptions.classList.add('hidden');
            keyInput.classList.add('hidden');
            processBtnText.textContent = 'Déchiffrer';
        } else {
            decryptOptions.classList.add('hidden');
            encryptOptions.classList.remove('hidden');
            keyInput.classList.remove('hidden');
            processBtnText.textContent = 'Chiffrer';
        }
        updateKeyHelp();
    }

    // Initialisation
    modeSelect.addEventListener('change', toggleModeOptions);
    cipherSelect.addEventListener('change', updateKeyHelp);
    toggleModeOptions();

    // Initialiser les graphiques
    initCharts();

    // Bouton de copie
    copyBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(resultText.value).then(function() {
            copyBtn.innerHTML = '<i class="fas fa-check text-green-500"></i>';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            }, 2000);
        }).catch(err => {
            console.error('Erreur de copie : ', err);
        });
    });

    // Fonction de traitement principal
    async function processText() {
        const text = inputText.value.trim();

        if (!text) {
            showToast('Veuillez entrer un texte à traiter', 'error');
            return;
        }

        // Afficher l'indicateur de chargement
        loading.classList.remove('hidden');
        processBtn.disabled = true;

        const mode = modeSelect.value;

        try {
            // Préparer les données pour l'API
            const apiData = {
                text: text,
                mode: mode
            };

            // Ajouter des informations supplémentaires pour le mode chiffrement
            if (mode === 'encrypt') {
                apiData.encrypt_method = cipherSelect.value;
                apiData.key = keyInput.value;
            } else if (mode === 'decrypt') {
                apiData.decrypt_method = decryptMethodSelect.value;
            }

            // Appel API pour traiter le texte
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(apiData)
            });

            if (!response.ok) {
                throw new Error('Erreur lors du traitement');
            }

            const data = await response.json();

            // Afficher le résultat
            resultText.value = data.result || 'Aucun résultat';

            // Mettre à jour les informations de détection en mode déchiffrement
            if (mode === 'decrypt') {
                detectionInfo.classList.remove('hidden');

                // Mettre à jour les informations détectées
                detectedCipher.textContent = formatCipherName(data.detected_cipher);

                const confidence = Math.round(data.confidence * 100 || 0);
                confidenceBar.style.width = `${confidence}%`;
                confidenceValue.textContent = `${confidence}%`;

                // Changer la couleur de la barre de confiance en fonction du niveau
                confidenceBar.classList.remove('bg-red-600', 'bg-blue-600', 'bg-green-600');
                if (confidence < 40) {
                    confidenceBar.classList.add('bg-red-600');
                } else if (confidence < 70) {
                    confidenceBar.classList.add('bg-blue-600');
                } else {
                    confidenceBar.classList.add('bg-green-600');
                }

                detectedLanguage.textContent = data.language || 'Inconnu';

                // Afficher la clé si elle a été trouvée
                if (data.detected_cipher === 'caesar' && 'key' in data) {
                    usedKey.textContent = `Décalage: ${data.key}`;
                } else if (data.detected_cipher === 'vigenere' && 'key' in data) {
                    usedKey.textContent = `"${data.key}"`;
                } else {
                    usedKey.textContent = '-';
                }

                // Mettre à jour les visualisations
                if (data.frequencies) updateVisualization('frequency', data.frequencies);
                if (data.bigrams) updateVisualization('biagram', data.bigrams);
                if (data.entropy) updateVisualization('entropy', data.entropy);
                if (data.autocorrelation) updateVisualization('autocorr', data.autocorrelation);
            } else {
                // Cacher les informations de détection en mode chiffrement
                detectionInfo.classList.add('hidden');
            }

            showToast('Traitement terminé avec succès!', 'success');

        } catch (error) {
            console.error('Erreur:', error);
            showToast('Erreur lors du traitement: ' + error.message, 'error');
        } finally {
            // Cacher l'indicateur de chargement
            loading.classList.add('hidden');
            processBtn.disabled = false;
        }
    }

    // Attacher l'événement de traitement
    processBtn.addEventListener('click', processText);

    /**
     * Met à jour le texte d'aide pour la saisie de la clé
     */
    function updateKeyHelp() {
        const cipher_type = cipherSelect.value;

        switch (cipher_type) {
            case 'caesar':
                keyHelp.textContent = 'Entrez un nombre entier (ex: 3) pour le décalage.';
                keyInput.placeholder = 'Nombre entier (ex: 3)';
                break;
            case 'vigenere':
                keyHelp.textContent = 'Entrez un mot-clé alphabétique (ex: CRYPT).';
                keyInput.placeholder = 'Mot-clé (ex: CRYPT)';
                break;
            case 'playfair':
                keyHelp.textContent = 'Entrez un mot-clé pour la grille Playfair.';
                keyInput.placeholder = 'Mot-clé (ex: CRYPTOGRAPHIE)';
                break;
            case 'substitution':
                keyHelp.textContent = 'Entrez l\'alphabet de substitution (26 lettres) ou laissez vide pour génération.';
                keyInput.placeholder = 'Alphabet (26 lettres)';
                break;
            case 'rsa':
                keyHelp.textContent = 'Format: "e,n" pour la clé publique.';
                keyInput.placeholder = 'e,n';
                break;
            case 'des':
                keyHelp.textContent = 'Clé DES (8 caractères ou 16 chiffres hexadécimaux).';
                keyInput.placeholder = 'Clé DES';
                break;
            case 'aes':
                keyHelp.textContent = 'Clé AES (16, 24 ou 32 caractères).';
                keyInput.placeholder = 'Clé AES';
                break;
            default:
                keyHelp.textContent = 'La clé dépend du type de chiffrement choisi.';
                keyInput.placeholder = 'Entrez la clé';
        }
    }

    /**
     * Initialise les graphiques vides
     */
    function initCharts() {
        // Configuration commune pour les graphiques
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        };

        // Graphique de fréquence
        const freqCtx = document.getElementById('frequency-chart').getContext('2d');
        frequencyChart = new Chart(freqCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Fréquence',
                    data: [],
                    backgroundColor: 'rgba(66, 153, 225, 0.6)',
                    borderColor: 'rgba(66, 153, 225, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        // Graphique de bigrammes
        const bigramCtx = document.getElementById('bigram-chart').getContext('2d');
        bigramChart = new Chart(bigramCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Fréquence',
                    data: [],
                    backgroundColor: 'rgba(168, 85, 247, 0.6)',
                    borderColor: 'rgba(168, 85, 247, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        // Graphique d'entropie
        const entropyCtx = document.getElementById('entropy-chart').getContext('2d');
        entropyChart = new Chart(entropyCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Entropie',
                    data: [],
                    backgroundColor: 'rgba(52, 211, 153, 0.4)',
                    borderColor: 'rgba(52, 211, 153, 1)',
                    borderWidth: 2,
                    tension: 0.2,
                    fill: true
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });

        // Graphique d'autocorrélation
        const autocorrCtx = document.getElementById('autocorr-chart').getContext('2d');
        autocorrChart = new Chart(autocorrCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Autocorrélation',
                    data: [],
                    backgroundColor: 'rgba(249, 115, 22, 0.4)',
                    borderColor: 'rgba(249, 115, 22, 1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: 'rgba(249, 115, 22, 1)',
                    fill: false
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    /**
     * Met à jour une visualisation spécifique avec de nouvelles données
     * @param {string} type - Type de visualisation ('frequency', 'bigram', 'entropy', 'autocorr')
     * @param {Object} data - Données pour la visualisation
     */
    function updateVisualization(type, data) {
        let chart, labels, values;

        // Trier les données si nécessaire et extraire les labels et valeurs
        if (Array.isArray(data)) {
            // Pour les formats de type série temporelle
            labels = data.map((item, index) => index);
            values = data;
        } else {
            // Pour les formats de type dictionnaire
            labels = Object.keys(data);
            values = Object.values(data);

            // Trier par valeur décroissante pour les fréquences et bigrammes
            if (type === 'frequency' || type === 'bigram') {
                // Créer des paires [clé, valeur] et trier
                const sortedPairs = labels.map((key, i) => [key, values[i]])
                    .sort((a, b) => b[1] - a[1]);

                // Limiter à 15 éléments pour la lisibilité
                const limitedPairs = sortedPairs.slice(0, 15);

                // Extraire les clés et valeurs triées
                labels = limitedPairs.map(pair => pair[0]);
                values = limitedPairs.map(pair => pair[1]);
            }
        }

        // Sélectionner le graphique approprié
        switch (type) {
            case 'frequency':
                chart = frequencyChart;
                break;
            case 'bigram':
                chart = bigramChart;
                break;
            case 'entropy':
                chart = entropyChart;
                break;
            case 'autocorr':
                chart = autocorrChart;
                break;
            default:
                console.error('Type de visualisation non reconnu:', type);
                return;
        }

        // Mettre à jour les données du graphique
        chart.data.labels = labels;
        chart.data.datasets[0].data = values;
        chart.update();
    }

    /**
     * Affiche un message toast temporaire
     * @param {string} message - Message à afficher
     * @param {string} type - Type de message ('success' ou 'error')
     */
    function showToast(message, type = 'success') {
        // Vérifier si un toast existe déjà et le supprimer
        const existingToast = document.getElementById('toast');
        if (existingToast) {
            existingToast.remove();
        }

        // Créer un nouvel élément toast
        const toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg transition-opacity duration-300 z-50 ${
            type === 'success' ? 'bg-green-600' : 'bg-red-600'
        }`;
        toast.textContent = message;

        // Ajouter au corps du document
        document.body.appendChild(toast);

        // Animer l'entrée
        setTimeout(() => {
            toast.classList.add('opacity-90');
        }, 10);

        // Animer la sortie et supprimer
        setTimeout(() => {
            toast.classList.remove('opacity-90');
            toast.classList.add('opacity-0');

            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }

    /**
     * Formate le nom du chiffrement pour l'affichage
     * @param {string} cipher_type - Type de chiffrement
     * @returns {string} Nom formaté
     */
    function formatCipherName(cipher_type) {
        const names = {
            'caesar': 'César',
            'vigenere': 'Vigenère',
            'playfair': 'Playfair',
            'substitution': 'Substitution',
            'transposition': 'Transposition',
            'hill': 'Hill',
            'enigma': 'Enigma',
            'rsa': 'RSA',
            'unknown': 'Inconnu'
        };

        return names[cipher_type] || cipher_type;
    }

    // Créer des particules de fond
    createParticles();

    /**
     * Crée des particules animées en arrière-plan
     */
    function createParticles() {
        // Créer un conteneur pour les particules s'il n'existe pas
        let particles = document.querySelector('.particles');
        if (!particles) {
            particles = document.createElement('div');
            particles.className = 'particles';
            document.body.appendChild(particles);
        }

        // Créer 15 particules
        for (let i = 0; i < 15; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';

            // Positionner aléatoirement
            const size = Math.random() * 10 + 5;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;

            // Opacité aléatoire
            particle.style.opacity = Math.random() * 0.5 + 0.1;

            // Animation retardée
            particle.style.animationDelay = `${Math.random() * 5}s`;
            particle.style.animationDuration = `${Math.random() * 10 + 5}s`;

            // Ajouter au conteneur
            particles.appendChild(particle);
        }
    }
});
// Gestion du toggle du chat
document.addEventListener('DOMContentLoaded', function() {
    // Get the chat elements
    const chatButton = document.getElementById('chat-button');
    const chatWidget = document.getElementById('chat-widget');
    const closeChat = document.getElementById('close-chat');
    const userMessage = document.getElementById('user-message');
    const sendMessage = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');

    // Create a div to display the live preview of user input
    const createChatPreview = () => {
        const previewContainer = document.createElement('div');
        previewContainer.id = 'chat-input-preview';
        previewContainer.className = 'text-gray-500 px-4 py-2 italic hidden';
        previewContainer.textContent = 'Typing...';

        // Insert it before the messages container
        chatMessages.parentNode.insertBefore(previewContainer, chatMessages.nextSibling);
        return previewContainer;
    };

    const chatPreview = createChatPreview();

    // Toggle chat widget visibility when clicking the chat button
    if (chatButton) {
        chatButton.addEventListener('click', function() {
            chatWidget.style.display = chatWidget.style.display === 'flex' ? 'none' : 'flex';

            // Focus on the input field when opened
            if (chatWidget.style.display === 'flex') {
                userMessage.focus();
            }
        });
    }

    // Close chat when clicking the close button
    if (closeChat) {
        closeChat.addEventListener('click', function() {
            chatWidget.style.display = 'none';
        });
    }

    // Send message when clicking the send button
    if (sendMessage) {
        sendMessage.addEventListener('click', sendUserMessage);
    }

    // Real-time display of typed text
    if (userMessage) {
        userMessage.addEventListener('input', function() {
            const message = userMessage.value.trim();

            if (message) {
                chatPreview.textContent = message;
                chatPreview.classList.remove('hidden');
            } else {
                chatPreview.classList.add('hidden');
            }
        });

        // Hide preview when input loses focus
        userMessage.addEventListener('blur', function() {
            chatPreview.classList.add('hidden');
        });

        // Focus will show preview if text exists
        userMessage.addEventListener('focus', function() {
            if (userMessage.value.trim()) {
                chatPreview.classList.remove('hidden');
            }
        });

        // Send message when pressing Enter in the input field
        userMessage.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendUserMessage();
            }
        });
    }

    // Function to send user message and get response
    function sendUserMessage() {
        const message = userMessage.value.trim();
        if (!message) return;

        // Hide the preview
        chatPreview.classList.add('hidden');

        // Add user message to chat
        addMessage(message, 'user');
        userMessage.value = '';

        // Get bot response
        getBotResponse(message);
    }

    // Add a message to the chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = text;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Get response from the bot/server
    async function getBotResponse(message) {
        // Show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'message bot-message';
        loadingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        chatMessages.appendChild(loadingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            // Remove loading indicator
            chatMessages.removeChild(loadingIndicator);

            if (!response.ok) {
                throw new Error('Error communicating with server');
            }

            const data = await response.json();
            addMessage(data.response, 'bot');
        } catch (error) {
            // Remove loading indicator if still present
            if (chatMessages.contains(loadingIndicator)) {
                chatMessages.removeChild(loadingIndicator);
            }

            console.error('Error:', error);
            addMessage("Sorry, I couldn't process your request. Please try again.", 'bot');
        }
    }

    // Add some basic CSS for the typing indicator
    const style = document.createElement('style');
    style.textContent = `
        .typing-indicator {
            display: flex;
            padding: 6px;
        }
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background: #999;
            border-radius: 50%;
            margin: 0 2px;
            animation: bounce 1.3s linear infinite;
        }
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.15s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.3s;
        }
        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-4px); }
        }
    `;
    document.head.appendChild(style);
});