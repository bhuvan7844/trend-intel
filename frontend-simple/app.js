// API Configuration
const API_BASE = window.location.origin;

// Store data globally for filtering
let allRepos = [];
let allHNStories = [];
let allArticles = [];

// Fetch data from API
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Dashboard Functions
async function loadDashboard() {
    try {
        const analytics = await fetchAPI('/analytics');
        
        // Update stats
        document.getElementById('totalRepos').textContent = analytics.summary.total_repos;
        document.getElementById('hnStories').textContent = analytics.summary.hn_mentions;
        document.getElementById('devArticles').textContent = analytics.summary.devto_mentions;
        document.getElementById('totalTopics').textContent = analytics.summary.total_topics;
        
        // Display top languages
        const languagesHTML = analytics.top_languages
            .slice(0, 6)
            .map(lang => `
                <div class="language-item">
                    <h4>${lang.language || 'Unknown'}</h4>
                    <p>${lang.repo_count} repositories</p>
                </div>
            `).join('');
        document.getElementById('topLanguages').innerHTML = languagesHTML;
        
        // Display top topics
        const topicsHTML = analytics.top_topics
            .slice(0, 6)
            .map(topic => `
                <div class="topic-item">
                    <h4>${topic.name}</h4>
                    <p>Weekly: ${topic.weekly_count} | Total: ${topic.total_count}</p>
                </div>
            `).join('');
        document.getElementById('topTopics').innerHTML = topicsHTML;
        
    } catch (error) {
        document.getElementById('statsGrid').innerHTML = '<p class="error">Failed to load dashboard data</p>';
    }
}

// Repos Functions
async function loadRepos() {
    try {
        allRepos = await fetchAPI('/trending?limit=50');
        displayRepos(allRepos);
    } catch (error) {
        document.getElementById('reposList').innerHTML = '<p class="error">Failed to load repositories</p>';
    }
}

function displayRepos(repos) {
    const html = repos.map(repo => `
        <div class="card">
            <h3>${repo.name}</h3>
            <p>${repo.description || 'No description available'}</p>
            <div class="card-meta">
                ${repo.language ? `<span class="badge">${repo.language}</span>` : ''}
                ${repo.stars ? `<span class="badge">⭐ ${repo.stars}</span>` : ''}
                <span class="badge">📈 Score: ${repo.trending_score}</span>
            </div>
            ${repo.url ? `<p style="margin-top: 1rem;"><a href="${repo.url}" target="_blank">View on GitHub →</a></p>` : ''}
        </div>
    `).join('');
    
    document.getElementById('reposList').innerHTML = html || '<p class="loading">No repositories found</p>';
}

function filterRepos(query) {
    const filtered = allRepos.filter(repo => 
        repo.name.toLowerCase().includes(query.toLowerCase()) ||
        (repo.description && repo.description.toLowerCase().includes(query.toLowerCase()))
    );
    displayRepos(filtered);
}

// Hacker News Functions
async function loadHNStories() {
    try {
        allHNStories = await fetchAPI('/trends/hn?limit=50');
        displayHNStories(allHNStories);
    } catch (error) {
        document.getElementById('hnList').innerHTML = '<p class="error">Failed to load stories</p>';
    }
}

function displayHNStories(stories) {
    const html = stories.map(story => `
        <div class="card">
            <h3>${story.title}</h3>
            <div class="card-meta">
                <span class="badge">⬆️ ${story.points} points</span>
                ${story.num_comments ? `<span class="badge">💬 ${story.num_comments} comments</span>` : ''}
                ${story.author ? `<span class="badge">👤 ${story.author}</span>` : ''}
            </div>
            ${story.url ? `<p style="margin-top: 1rem;"><a href="${story.url}" target="_blank">Read Story →</a></p>` : ''}
        </div>
    `).join('');
    
    document.getElementById('hnList').innerHTML = html || '<p class="loading">No stories found</p>';
}

function filterHN(query) {
    const filtered = allHNStories.filter(story => 
        story.title.toLowerCase().includes(query.toLowerCase())
    );
    displayHNStories(filtered);
}

// DEV Articles Functions
async function loadArticles() {
    try {
        allArticles = await fetchAPI('/trends/devto?limit=50');
        displayArticles(allArticles);
    } catch (error) {
        document.getElementById('articlesList').innerHTML = '<p class="error">Failed to load articles</p>';
    }
}

function displayArticles(articles) {
    const html = articles.map(article => `
        <div class="card">
            <h3>${article.title}</h3>
            <div class="card-meta">
                <span class="badge">❤️ ${article.reactions} reactions</span>
                ${article.author ? `<span class="badge">✍️ ${article.author}</span>` : ''}
            </div>
            ${article.tags ? `<p style="margin-top: 0.5rem; color: #a1a1aa;">Tags: ${article.tags}</p>` : ''}
            ${article.url ? `<p style="margin-top: 1rem;"><a href="${article.url}" target="_blank">Read Article →</a></p>` : ''}
        </div>
    `).join('');
    
    document.getElementById('articlesList').innerHTML = html || '<p class="loading">No articles found</p>';
}

function filterArticles(query) {
    const filtered = allArticles.filter(article => 
        article.title.toLowerCase().includes(query.toLowerCase()) ||
        (article.tags && article.tags.toLowerCase().includes(query.toLowerCase()))
    );
    displayArticles(filtered);
}
