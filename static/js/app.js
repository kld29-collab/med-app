// Medication Interaction Tracker - Frontend JavaScript

// DOM Elements
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const chatMessages = document.getElementById('chatMessages');
const sendButton = document.getElementById('sendButton');
const charCount = document.getElementById('charCount');
const loadingOverlay = document.getElementById('loadingOverlay');
const profileSidebar = document.getElementById('profileSidebar');
const toggleSidebar = document.getElementById('toggleSidebar');
const openSidebar = document.getElementById('openSidebar');
const saveProfileBtn = document.getElementById('saveProfile');
const clearProfileBtn = document.getElementById('clearProfile');
const profileStatus = document.getElementById('profileStatus');

// User context stored in localStorage (for Vercel serverless compatibility)
let userContext = (function() {
    try {
        const stored = localStorage.getItem('userContext');
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        // Handle corrupted localStorage data
        console.warn('Failed to parse userContext from localStorage, resetting to empty object:', e);
        localStorage.removeItem('userContext'); // Clean up corrupted data
        return {};
    }
})();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadUserContext();
    setupEventListeners();
    updateCharCount();
});

// Event Listeners
function setupEventListeners() {
    // Chat form submission
    chatForm.addEventListener('submit', handleSubmit);
    
    // Character count
    userInput.addEventListener('input', updateCharCount);
    
    // Handle Enter to submit, Shift+Enter for new lines
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
        // Shift+Enter will allow default behavior (new line)
    });
    
    // Sidebar toggle
    toggleSidebar.addEventListener('click', () => {
        profileSidebar.classList.add('hidden');
    });
    
    openSidebar.addEventListener('click', () => {
        profileSidebar.classList.remove('hidden');
    });
    
    // Profile management
    saveProfileBtn.addEventListener('click', saveProfile);
    clearProfileBtn.addEventListener('click', clearProfile);
}

// Character count
function updateCharCount() {
    const count = userInput.value.length;
    charCount.textContent = count;
    if (count > 450) {
        charCount.style.color = '#dc3545';
    } else {
        charCount.style.color = '#666';
    }
}

// Handle chat form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    const query = userInput.value.trim();
    if (!query) return;
    
    // Disable input
    userInput.disabled = true;
    sendButton.disabled = true;
    loadingOverlay.style.display = 'flex';
    
    // Add user message to chat
    addMessage(query, 'user');
    userInput.value = '';
    updateCharCount();
    
    try {
        // Get user context (from localStorage for Vercel compatibility)
        const context = getUserContext();
        
        console.log('Sending query to /api/query:', { query, context });
        
        // Send query to backend
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                user_context: context
            })
        });
        
        console.log('Response status:', response.status);
        
        const data = await response.json();
        
        console.log('Response data:', data);
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Display explanation with sources panel
        if (data.explanation) {
            // Pass full explanation object to display with sources
            const formatted = formatExplanationWithSources(data.explanation);
            addMessage(formatted, 'bot', false, data.explanation);
        } else {
            addMessage('I received your query but could not generate a response. Please try again.', 'bot');
        }
        
    } catch (error) {
        console.error('Error during query submission:', error);
        addMessage(`Error: ${error.message}. Please try again or consult your healthcare provider.`, 'bot', true);
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendButton.disabled = false;
        loadingOverlay.style.display = 'none';
        userInput.focus();
    }
}

// Add message to chat
function addMessage(content, type, isError = false, explanationData = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message${isError ? ' error-message' : ''}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Convert markdown-like formatting to HTML
    const formattedContent = formatMessageContent(content);
    contentDiv.innerHTML = formattedContent;
    
    // Add sources panel if explanation data is provided
    if (explanationData && explanationData.metadata && explanationData.metadata.sources) {
        const sourcesPanel = createSourcesPanel(explanationData);
        contentDiv.appendChild(sourcesPanel);
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Escape HTML characters to prevent XSS attacks
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format message content (simple markdown-like formatting)
function formatMessageContent(text) {
    // First escape HTML to prevent XSS attacks
    // This must happen before any markdown processing
    text = escapeHtml(text);
    
    // Convert **bold** to <strong> (after escaping, so we can safely add HTML tags)
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert bullet points to <li> tags first (before line break conversion)
    text = text.replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>');
    
    // Wrap consecutive <li> tags (with optional whitespace/newlines between) in <ul> tags
    // This handles multiple bullet point groups correctly by matching only consecutive list items
    // Pattern matches: one or more <li> tags with optional whitespace/newlines between them
    // Replace newlines between list items with nothing (they're not needed in HTML lists)
    text = text.replace(/((?:<li>.*?<\/li>\s*)+)/g, function(match) {
        // Remove newlines within the matched list group
        return '<ul>' + match.replace(/\n/g, '') + '</ul>';
    });
    
    // Convert remaining line breaks to <br> (after list processing to avoid breaking list structure)
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Format explanation object
function formatExplanation(explanation) {
    let formatted = '';
    
    if (explanation.summary) {
        formatted += `**Summary:**\n${explanation.summary}\n\n`;
    }
    
    if (explanation.interactions && explanation.interactions.length > 0) {
        formatted += '**Interactions:**\n';
        explanation.interactions.forEach((interaction, i) => {
            const items = interaction.items ? interaction.items.join(' and ') : 'Unknown';
            formatted += `${i + 1}. **${items}** (${interaction.type || 'unknown'})\n`;
            if (interaction.explanation) {
                formatted += `   ${interaction.explanation}\n`;
            }
            if (interaction.severity) {
                formatted += `   Severity: ${interaction.severity}\n`;
            }
            if (interaction.recommendation) {
                formatted += `   Recommendation: ${interaction.recommendation}\n`;
            }
            formatted += '\n';
        });
    }
    
    if (explanation.uncertainties && explanation.uncertainties.length > 0) {
        formatted += '**Note:**\n';
        explanation.uncertainties.forEach(uncertainty => {
            formatted += `- ${uncertainty}\n`;
        });
        formatted += '\n';
    }
    
    if (explanation.recommendation) {
        formatted += `**Recommendation:**\n${explanation.recommendation}\n\n`;
    }
    
    if (explanation.disclaimer) {
        formatted += `**Disclaimer:**\n${explanation.disclaimer}`;
    }
    
    return formatted;
}

// Format explanation with sources panel
function formatExplanationWithSources(explanation) {
    // Use the same format as formatExplanation
    return formatExplanation(explanation);
}

// Create expandable sources panel
function createSourcesPanel(explanationData) {
    const panel = document.createElement('details');
    panel.className = 'sources-panel';
    
    const summary = document.createElement('summary');
    summary.className = 'sources-summary';
    
    // Count total sources
    const sources = explanationData.metadata?.sources || [];
    const totalCount = sources.reduce((sum, s) => sum + (s.count || 0), 0);
    
    summary.innerHTML = `📚 View Sources (${sources.length})`;
    panel.appendChild(summary);
    
    // Create sources list
    const sourcesList = document.createElement('div');
    sourcesList.className = 'sources-list';
    
    sources.forEach(source => {
        const sourceItem = document.createElement('div');
        sourceItem.className = `source-item source-${source.type.toLowerCase()}`;
        
        const sourceTitle = document.createElement('div');
        sourceTitle.className = 'source-title';
        sourceTitle.innerHTML = `<strong>${escapeHtml(source.name)}</strong> <span class="source-count">${source.count} ${source.count === 1 ? 'item' : 'items'}</span>`;
        sourceItem.appendChild(sourceTitle);
        
        const sourceDesc = document.createElement('div');
        sourceDesc.className = 'source-description';
        sourceDesc.textContent = source.description;
        sourceItem.appendChild(sourceDesc);
        
        // Add source-specific details with actual information
        if (source.type === 'drug-interactions' && explanationData.raw_sources?.drugbank) {
            const drugbankItems = explanationData.raw_sources.drugbank.slice(0, 5);
            if (drugbankItems.length > 0) {
                const details = document.createElement('div');
                details.className = 'source-details';
                drugbankItems.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'detail-item';
                    
                    const drugs = document.createElement('div');
                    drugs.className = 'detail-drugs';
                    const drug1 = item.drug1_id || 'Unknown';
                    const drug2 = item.drug2_name || 'Unknown';
                    drugs.innerHTML = `<strong>${escapeHtml(drug1)}</strong> ↔ <strong>${escapeHtml(drug2)}</strong>`;
                    itemDiv.appendChild(drugs);
                    
                    if (item.description) {
                        const desc = document.createElement('div');
                        desc.className = 'detail-description';
                        desc.textContent = item.description.substring(0, 100);
                        if (item.description.length > 100) desc.textContent += '...';
                        itemDiv.appendChild(desc);
                    }
                    
                    details.appendChild(itemDiv);
                });
                sourceItem.appendChild(details);
            }
        } else if (source.type === 'drug-labels' && explanationData.raw_sources?.fda) {
            const fdaItems = explanationData.raw_sources.fda.slice(0, 5);
            if (fdaItems.length > 0) {
                const details = document.createElement('div');
                details.className = 'source-details';
                fdaItems.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'detail-item';
                    
                    const drugName = document.createElement('div');
                    drugName.className = 'detail-drugs';
                    drugName.innerHTML = `<strong>${escapeHtml(item.drug_name || 'Unknown')}</strong>`;
                    itemDiv.appendChild(drugName);
                    
                    // Show FDA warnings if available
                    if (item.warnings && item.warnings.length > 0) {
                        const warning = document.createElement('div');
                        warning.className = 'detail-warning';
                        warning.textContent = '⚠️ ' + item.warnings[0].substring(0, 80);
                        if (item.warnings[0].length > 80) warning.textContent += '...';
                        itemDiv.appendChild(warning);
                    } else if (item.precautions && item.precautions.length > 0) {
                        const precaution = document.createElement('div');
                        precaution.className = 'detail-precaution';
                        precaution.textContent = item.precautions[0].substring(0, 80);
                        if (item.precautions[0].length > 80) precaution.textContent += '...';
                        itemDiv.appendChild(precaution);
                    }
                    
                    details.appendChild(itemDiv);
                });
                sourceItem.appendChild(details);
            }
        } else if (source.type === 'web-results' && explanationData.raw_sources?.web) {
            const webItems = explanationData.raw_sources.web.slice(0, 5);
            if (webItems.length > 0) {
                const details = document.createElement('div');
                details.className = 'source-details';
                webItems.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'detail-item detail-web';
                    
                    if (item.title) {
                        const title = document.createElement('div');
                        title.className = 'detail-title';
                        title.textContent = item.title.substring(0, 70);
                        if (item.title.length > 70) title.textContent += '...';
                        itemDiv.appendChild(title);
                    }
                    
                    if (item.snippet) {
                        const snippet = document.createElement('div');
                        snippet.className = 'detail-snippet';
                        snippet.textContent = item.snippet.substring(0, 100);
                        if (item.snippet.length > 100) snippet.textContent += '...';
                        itemDiv.appendChild(snippet);
                    }
                    
                    details.appendChild(itemDiv);
                });
                sourceItem.appendChild(details);
            }
        } else if (source.type === 'citations' && explanationData.raw_sources?.citations) {
            const citationItems = explanationData.raw_sources.citations.slice(0, 5);
            if (citationItems.length > 0) {
                const details = document.createElement('div');
                details.className = 'source-details';
                citationItems.forEach(item => {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'detail-item detail-citation';
                    
                    const citationText = document.createElement('div');
                    citationText.className = 'detail-citation-text';
                    citationText.textContent = (typeof item === 'string' ? item : item.text || JSON.stringify(item)).substring(0, 100);
                    itemDiv.appendChild(citationText);
                    
                    details.appendChild(itemDiv);
                });
                sourceItem.appendChild(details);
            }
        }
        
        sourcesList.appendChild(sourceItem);
    });
    
    panel.appendChild(sourcesList);
    return panel;
}

// Profile Management
function loadUserContext() {
    // Load from localStorage
    if (userContext.age) document.getElementById('age').value = userContext.age;
    if (userContext.weight) document.getElementById('weight').value = userContext.weight;
    if (userContext.height) document.getElementById('height').value = userContext.height;
    if (userContext.medications) {
        document.getElementById('medications').value = userContext.medications.join('\n');
    }
    if (userContext.conditions) {
        document.getElementById('conditions').value = userContext.conditions.join('\n');
    }
}

function getUserContext() {
    return {
        age: userContext.age || null,
        weight: userContext.weight || null,
        height: userContext.height || null,
        medications: userContext.medications || [],
        conditions: userContext.conditions || []
    };
}

async function saveProfile() {
    const age = document.getElementById('age').value;
    const weight = document.getElementById('weight').value;
    const height = document.getElementById('height').value;
    const medications = document.getElementById('medications').value
        .split('\n')
        .map(m => m.trim())
        .filter(m => m);
    const conditions = document.getElementById('conditions').value
        .split('\n')
        .map(c => c.trim())
        .filter(c => c);
    
    const context = {
        age: age ? parseInt(age) : null,
        weight: weight ? parseFloat(weight) : null,
        height: height ? parseFloat(height) : null,
        medications: medications,
        conditions: conditions
    };
    
    try {
        // Validate with backend (stateless - no server-side storage)
        const response = await fetch('/api/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(context)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to validate profile');
        }
        
        // Save to localStorage (primary storage for Vercel serverless)
        // Use validated context from server if provided, otherwise use local context
        userContext = data.user_context || context;
        localStorage.setItem('userContext', JSON.stringify(userContext));
        
        showProfileStatus('Profile saved successfully!', 'success');
        
    } catch (error) {
        console.error('Error saving profile:', error);
        showProfileStatus(`Error: ${error.message}`, 'error');
    }
}

async function clearProfile() {
    if (!confirm('Are you sure you want to clear your profile?')) {
        return;
    }
    
    // Clear form
    document.getElementById('age').value = '';
    document.getElementById('weight').value = '';
    document.getElementById('height').value = '';
    document.getElementById('medications').value = '';
    document.getElementById('conditions').value = '';
    
    // Clear storage
    userContext = {};
    localStorage.removeItem('userContext');
    
    try {
        // Clear on backend (returns default empty context)
        const response = await fetch('/api/clear-profile', {
            method: 'POST'
        });
        const data = await response.json();
        // Use validated empty context from server if provided
        if (data.user_context) {
            userContext = data.user_context;
        }
    } catch (error) {
        console.error('Error clearing profile:', error);
    }
    
    showProfileStatus('Profile cleared', 'success');
}

function showProfileStatus(message, type) {
    profileStatus.textContent = message;
    profileStatus.className = `profile-status ${type}`;
    
    setTimeout(() => {
        profileStatus.className = 'profile-status';
    }, 3000);
}

