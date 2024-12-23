let currentSubject = '';

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    const subjectCards = document.querySelectorAll('.subject-card');
    const learningArea = document.getElementById('learning-area');
    const subjectGallery = document.getElementById('subject-gallery');
    const chatInput = document.getElementById('chat-input');
    const sendMessageBtn = document.getElementById('send-message-btn');
    const newDrillBtn = document.getElementById('new-drill-btn');
    const chatMessages = document.getElementById('chat-messages');

    // Settings elements
    const settingsBtn = document.getElementById('settings-btn');
    const settingsDropdown = document.getElementById('settings-dropdown');
    const languageSelect = document.getElementById('language-select');

    // Set initial language value
    languageSelect.value = document.documentElement.lang;

    // Toggle settings dropdown
    settingsBtn.addEventListener('click', () => {
        settingsDropdown.classList.toggle('hidden');
    });

    // Close settings when clicking outside
    document.addEventListener('click', (e) => {
        if (!settingsBtn.contains(e.target) && !settingsDropdown.contains(e.target)) {
            settingsDropdown.classList.add('hidden');
        }
    });

    // Handle language change
    languageSelect.addEventListener('change', async () => {
        const response = await fetch('/set_language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ language: languageSelect.value })
        });

        if (response.ok) {
            const data = await response.json();
            updatePageTranslations(data.translations, data.subjects);
            document.documentElement.lang = languageSelect.value;
        }
    });

    subjectCards.forEach(card => {
        card.addEventListener('click', () => {
            console.log('Subject card clicked:', card.dataset.subject);
            currentSubject = card.dataset.subject;
            subjectGallery.classList.add('hidden');
            learningArea.classList.remove('hidden');
            loadNewDrill();
        });
    });

    sendMessageBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    newDrillBtn.addEventListener('click', loadNewDrill);
});

function loadNewDrill() {
    console.log('Loading new drill for subject:', currentSubject);
    fetch(`/get_drill/${currentSubject}`)
        .then(response => response.json())
        .then(data => {
            console.log('New drill received:', data);
            document.getElementById('current-drill').textContent = data.drill;
            // Add the new problem as a tutor message
            addMessage('Here\'s your new problem:', 'tutor');
            addMessage(data.drill, 'problem');
        })
        .catch(error => console.error('Error loading drill:', error));
}

function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    chatInput.value = '';

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            subject: currentSubject,
            drill: document.getElementById('current-drill').textContent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addMessage('Sorry, I encountered an error. Please try again.', 'tutor');
        } else {
            addMessage(data.response, 'tutor');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'tutor');
    });
}

function addMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updatePageTranslations(translations, subjects) {
    // Update page title
    document.title = translations.app_title;
    
    // Update header
    document.querySelector('header h1').textContent = translations.app_title;
    document.querySelector('header p').textContent = translations.choose_subject;
    
    // Update buttons
    document.getElementById('settings-btn').textContent = translations.settings;
    document.getElementById('new-drill-btn').textContent = translations.new_problem;
    document.getElementById('send-message-btn').textContent = translations.send;
    
    // Update language label
    document.querySelector('label[for="language-select"]').textContent = translations.language;
    
    // Update chat input placeholder
    document.getElementById('chat-input').placeholder = translations.chat_placeholder;
    
    // Update practice problem heading
    document.querySelector('.current-problem h2').textContent = translations.practice_problem;
    
    // Update subject cards
    const subjectCards = document.querySelectorAll('.subject-card');
    subjectCards.forEach(card => {
        const subject = subjects[card.dataset.subject];
        card.querySelector('h3').textContent = subject.name;
        card.querySelector('p').textContent = subject.description;
    });
}
