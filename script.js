// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';  // Backend API URL

// Global Variables
let currentPage = 1;
let allExoplanets = [];
let filteredExoplanets = [];
let charts = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeNavbar();
    loadInitialData();
    initializeCharts();
});

// Create animated stars background
function initializeStars() {
    const starsContainer = document.getElementById('starsContainer');
    const starCount = 200;
    
    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        star.style.animationDelay = `${Math.random() * 3}s`;
        star.style.animationDuration = `${2 + Math.random() * 2}s`;
        starsContainer.appendChild(star);
    }
}

// Initialize navbar functionality
function initializeNavbar() {
    const navbar = document.querySelector('.navbar');
    const menuToggle = document.getElementById('menuToggle');
    const navLinks = document.querySelector('.nav-links');
    
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Mobile menu toggle
    menuToggle.addEventListener('click', function() {
        menuToggle.classList.toggle('active');
        navLinks.classList.toggle('active');
    });
    
    // Close mobile menu when clicking a link
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', function() {
            menuToggle.classList.remove('active');
            navLinks.classList.remove('active');
        });
    });
}

// Smooth scroll to section
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    section.scrollIntoView({ behavior: 'smooth' });
}

// Load initial data from backend
async function loadInitialData() {
    try {
        // Load stats
        await loadStats();
        
        // Load exoplanets
        await loadExoplanets();
        
        // Load chart data
        await loadChartData();
    } catch (error) {
        console.error('Error loading initial data:', error);
        showError('Failed to load data. Please try again.');
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        
        animateCounter('totalExoplanets', data.total_exoplanets);
        animateCounter('habitableExoplanets', data.habitable_exoplanets);
        animateCounter('recentDiscoveries', data.recent_discoveries);
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('totalExoplanets').textContent = '5000+';
        document.getElementById('habitableExoplanets').textContent = '60+';
        document.getElementById('recentDiscoveries').textContent = '150+';
    }
}

// Animate counter numbers
function animateCounter(elementId, targetValue) {
    const element = document.getElementById(elementId);
    const duration = 2000;
    const start = 0;
    const increment = targetValue / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= targetValue) {
            element.textContent = targetValue.toLocaleString();
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current).toLocaleString();
        }
    }, 16);
}

// Load exoplanets from backend
async function loadExoplanets(page = 1) {
    const grid = document.getElementById('exoplanetGrid');
    
    if (page === 1) {
        grid.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading exoplanets...</p></div>';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/exoplanets?page=${page}&limit=12`);
        const data = await response.json();
        
        if (page === 1) {
            allExoplanets = data.exoplanets;
            filteredExoplanets = data.exoplanets;
            displayExoplanets(filteredExoplanets);
        } else {
            allExoplanets = [...allExoplanets, ...data.exoplanets];
            filteredExoplanets = [...filteredExoplanets, ...data.exoplanets];
            appendExoplanets(data.exoplanets);
        }
        
        currentPage = page;
        
        // Show/hide load more button
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (data.has_more) {
            loadMoreBtn.style.display = 'block';
        } else {
            loadMoreBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading exoplanets:', error);
        grid.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Failed to load exoplanets. Please try again.</p>';
    }
}

// Display exoplanets in grid
function displayExoplanets(exoplanets) {
    const grid = document.getElementById('exoplanetGrid');
    
    if (exoplanets.length === 0) {
        grid.innerHTML = '<p style="text-align: center; grid-column: 1 / -1; color: var(--text-secondary);">No exoplanets found matching your criteria.</p>';
        return;
    }
    
    grid.innerHTML = '';
    exoplanets.forEach(planet => {
        grid.appendChild(createPlanetCard(planet));
    });
}

// Append exoplanets to existing grid
function appendExoplanets(exoplanets) {
    const grid = document.getElementById('exoplanetGrid');
    exoplanets.forEach(planet => {
        grid.appendChild(createPlanetCard(planet));
    });
}

// Create planet card element
function createPlanetCard(planet) {
    const card = document.createElement('div');
    card.className = 'planet-card';
    card.onclick = () => showPlanetDetails(planet);
    
    card.innerHTML = `
        <h3 class="planet-name">${planet.name}</h3>
        <div class="planet-info">
            <div class="info-row">
                <span class="info-label">Host Star</span>
                <span class="info-value">${planet.hostname || 'Unknown'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Discovery Method</span>
                <span class="info-value">${planet.discoverymethod || 'Unknown'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Discovery Year</span>
                <span class="info-value">${planet.disc_year || 'Unknown'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Distance</span>
                <span class="info-value">${planet.sy_dist ? planet.sy_dist.toFixed(2) + ' ly' : 'Unknown'}</span>
            </div>
        </div>
        <span class="planet-badge">${getPlanetType(planet)}</span>
    `;
    
    return card;
}

// Determine planet type based on radius
function getPlanetType(planet) {
    if (!planet.pl_rade) return 'Unknown Type';
    
    const radius = planet.pl_rade;
    if (radius < 1.25) return 'Earth-like';
    if (radius < 2.0) return 'Super-Earth';
    if (radius < 6.0) return 'Neptune-like';
    return 'Jupiter-like';
}

// Search exoplanets
function searchExoplanets() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    if (searchTerm === '') {
        filteredExoplanets = allExoplanets;
    } else {
        filteredExoplanets = allExoplanets.filter(planet => 
            planet.name.toLowerCase().includes(searchTerm) ||
            (planet.hostname && planet.hostname.toLowerCase().includes(searchTerm))
        );
    }
    
    displayExoplanets(filteredExoplanets);
}

// Apply filters
function applyFilters() {
    const methodFilter = document.getElementById('discoveryMethodFilter').value;
    const habitableFilter = document.getElementById('habitableFilter').value;
    
    filteredExoplanets = allExoplanets.filter(planet => {
        let matchesMethod = true;
        let matchesHabitable = true;
        
        if (methodFilter && planet.discoverymethod) {
            matchesMethod = planet.discoverymethod.includes(methodFilter);
        }
        
        if (habitableFilter && planet.pl_rade) {
            const radius = planet.pl_rade;
            if (habitableFilter === 'habitable') {
                matchesHabitable = radius >= 0.5 && radius <= 1.5;
            } else if (habitableFilter === 'hot') {
                matchesHabitable = radius < 0.5;
            } else if (habitableFilter === 'cold') {
                matchesHabitable = radius > 1.5;
            }
        }
        
        return matchesMethod && matchesHabitable;
    });
    
    displayExoplanets(filteredExoplanets);
}

// Reset filters
function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('discoveryMethodFilter').value = '';
    document.getElementById('habitableFilter').value = '';
    
    filteredExoplanets = allExoplanets;
    displayExoplanets(filteredExoplanets);
}

// Load more exoplanets
function loadMoreExoplanets() {
    loadExoplanets(currentPage + 1);
}

// Show planet details in modal
function showPlanetDetails(planet) {
    const modal = document.getElementById('planetModal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <h2 class="modal-planet-name">${planet.name}</h2>
        <p class="modal-planet-host">Orbits ${planet.hostname || 'Unknown Star'}</p>
        
        <div class="modal-info-grid">
            <div class="modal-info-item">
                <div class="modal-info-label">Discovery Method</div>
                <div class="modal-info-value">${planet.discoverymethod || 'Unknown'}</div>
            </div>
            <div class="modal-info-item">
                <div class="modal-info-label">Discovery Year</div>
                <div class="modal-info-value">${planet.disc_year || 'Unknown'}</div>
            </div>
            <div class="modal-info-item">
                <div class="modal-info-label">Planet Radius</div>
                <div class="modal-info-value">${planet.pl_rade ? planet.pl_rade.toFixed(2) + ' R⊕' : 'Unknown'}</div>
            </div>
            <div class="modal-info-item">
                <div class="modal-info-label">Planet Mass</div>
                <div class="modal-info-value">${planet.pl_bmasse ? planet.pl_bmasse.toFixed(2) + ' M⊕' : 'Unknown'}</div>
            </div>
            <div class="modal-info-item">
                <div class="modal-info-label">Orbital Period</div>
                <div class="modal-info-value">${planet.pl_orbper ? planet.pl_orbper.toFixed(2) + ' days' : 'Unknown'}</div>
            </div>
            <div class="modal-info-item">
                <div class="modal-info-label">Distance from Earth</div>
                <div class="modal-info-value">${planet.sy_dist ? planet.sy_dist.toFixed(2) + ' ly' : 'Unknown'}</div>
            </div>
            <div class="modal-info-item">
                <div class="modal-info-label">Star Temperature</div>
                <div class="modal-info-value">${planet.st_teff ? planet.st_teff + ' K' : 'Unknown'}</div>
            </div>
            <div class="modal-info-item">
                <div class="modal-info-label">Star Radius</div>
                <div class="modal-info-value">${planet.st_rad ? planet.st_rad.toFixed(2) + ' R☉' : 'Unknown'}</div>
            </div>
        </div>
    `;
    
    modal.classList.add('active');
}

// Close modal
function closeModal() {
    const modal = document.getElementById('planetModal');
    modal.classList.remove('active');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('planetModal');
    if (event.target === modal) {
        closeModal();
    }
}

// AI Prediction Form
async function predictExoplanet(event) {
    event.preventDefault();
    
    const resultsPanel = document.getElementById('resultsPanel');
    resultsPanel.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>AI is analyzing...</p></div>';
    
    const formData = {
        star_temp: parseFloat(document.getElementById('starTemp').value),
        star_radius: parseFloat(document.getElementById('starRadius').value),
        star_mass: parseFloat(document.getElementById('starMass').value),
        orbital_period: parseFloat(document.getElementById('orbitalPeriod').value),
        transit_depth: parseFloat(document.getElementById('transitDepth').value)
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        displayPredictionResult(result);
    } catch (error) {
        console.error('Error making prediction:', error);
        resultsPanel.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Prediction failed. Please try again.</p>';
    }
}

// Display AI prediction results
function displayPredictionResult(result) {
    const resultsPanel = document.getElementById('resultsPanel');
    
    const hasExoplanet = result.prediction === 1 || result.probability > 0.5;
    const confidence = (result.probability * 100).toFixed(1);
    
    resultsPanel.innerHTML = `
        <div class="prediction-result">
            <div class="result-header">
                <div class="result-status">${hasExoplanet ? '✅' : '❌'}</div>
                <div class="result-title">${hasExoplanet ? 'Exoplanet Detected!' : 'No Exoplanet Detected'}</div>
                <p style="color: var(--text-secondary); margin-top: 10px;">
                    ${hasExoplanet ? 'AI detected signs of an exoplanet' : 'AI found no strong exoplanet signals'}
                </p>
            </div>
            
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${confidence}%">
                    ${confidence}% Confidence
                </div>
            </div>
            
            <div class="result-details">
                <div class="detail-item">
                    <span class="detail-label">Prediction</span>
                    <span class="detail-value">${hasExoplanet ? 'Positive' : 'Negative'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Confidence Score</span>
                    <span class="detail-value">${confidence}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Planet Type</span>
                    <span class="detail-value">${result.planet_type || 'Unknown'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Habitability</span>
                    <span class="detail-value">${result.habitable_zone || 'Unknown'}</span>
                </div>
            </div>
        </div>
    `;
}

// Initialize Charts
function initializeCharts() {
    // Timeline Chart will be populated with real data
    // Methods Chart will be populated with real data
    // Size Chart will be populated with real data
    // Distance Chart will be populated with real data
    
    // Note: Charts will be created using Chart.js when data is loaded
    console.log('Charts will be initialized with real data from backend');
}

// Load chart data from backend
async function loadChartData() {
    try {
        const response = await fetch(`${API_BASE_URL}/chart-data`);
        const data = await response.json();
        
        createTimelineChart(data.timeline);
        createMethodsChart(data.methods);
        createSizeChart(data.sizes);
        createDistanceChart(data.distances);
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Create timeline chart (placeholder - will use Chart.js)
function createTimelineChart(data) {
    console.log('Timeline chart data:', data);
    // Chart.js implementation will go here
}

// Create methods chart (placeholder - will use Chart.js)
function createMethodsChart(data) {
    console.log('Methods chart data:', data);
    // Chart.js implementation will go here
}

// Create size chart (placeholder - will use Chart.js)
function createSizeChart(data) {
    console.log('Size chart data:', data);
    // Chart.js implementation will go here
}

// Create distance chart (placeholder - will use Chart.js)
function createDistanceChart(data) {
    console.log('Distance chart data:', data);
    // Chart.js implementation will go here
}

// Show error message
function showError(message) {
    console.error(message);
    // You can implement a toast notification here
}

// Utility function to debounce search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add debounced search to input
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        const debouncedSearch = debounce(searchExoplanets, 300);
        searchInput.addEventListener('input', debouncedSearch);
    }
});