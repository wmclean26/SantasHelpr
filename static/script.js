// ==================== Santa's Helpr - Integrated Search ====================
// Supports Chat Mode (natural language) and Filter Mode (manual filters)
// Returns dual results: Original + AI Similar recommendations

let currentMode = 'chat'; // 'chat' or 'filter'

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    // Mode toggle buttons
    document.getElementById('chatModeBtn').addEventListener('click', () => switchMode('chat'));
    document.getElementById('filterModeBtn').addEventListener('click', () => switchMode('filter'));
    
    // Search button
    document.getElementById('searchBtn').addEventListener('click', performSearch);
    
    // Enter key handlers
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            performSearch();
        }
    });
    document.getElementById('product').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
    
    // Check LLM status
    checkLLMStatus();
});

function switchMode(mode) {
    currentMode = mode;
    
    // Update button states
    document.getElementById('chatModeBtn').classList.toggle('active', mode === 'chat');
    document.getElementById('filterModeBtn').classList.toggle('active', mode === 'filter');
    
    // Show/hide sections
    document.getElementById('chatSection').style.display = mode === 'chat' ? 'block' : 'none';
    document.getElementById('filterSection').style.display = mode === 'filter' ? 'block' : 'none';
    
    // Clear results
    clearResults();
}

async function checkLLMStatus() {
    try {
        const response = await fetch('/llm_status');
        const data = await response.json();
        if (!data.available) {
            document.getElementById('llmWarning').style.display = 'block';
        }
    } catch (e) {
        console.log('Could not check LLM status');
    }
}

function clearResults() {
    document.getElementById('originalResults').style.display = 'none';
    document.getElementById('similarResults').style.display = 'none';
    document.getElementById('originalTop3').innerHTML = '';
    document.getElementById('similarTop3').innerHTML = '';
    document.getElementById('extractionPreview').style.display = 'none';
    document.getElementById('status').style.display = 'none';
}

// ==================== Main Search Function ====================
async function performSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const status = document.getElementById('status');
    
    // Build request based on mode
    let searchParams = {
        mode: currentMode,
        sort_criteria: document.getElementById('sort_criteria').value
    };
    
    if (currentMode === 'chat') {
        searchParams.chat_input = document.getElementById('chatInput').value;
        if (!searchParams.chat_input.trim()) {
            showStatus('Please enter a gift description', 'error');
            return;
        }
    } else {
        searchParams = {
            ...searchParams,
            product: document.getElementById('product').value,
            min_price: document.getElementById('min_price').value,
            max_price: document.getElementById('max_price').value,
            condition: document.getElementById('condition').value,
            sort_by: document.getElementById('sort_by').value,
            amazon_sort: document.getElementById('amazon_sort').value,
            country: document.getElementById('country').value,
            postal: document.getElementById('postal').value,
            max_shipping: document.getElementById('max_shipping').value,
            delivery_days: document.getElementById('delivery_days').value
        };
        if (!searchParams.product.trim()) {
            showStatus('Please enter a product to search for', 'error');
            return;
        }
    }
    
    // Show loading state
    searchBtn.disabled = true;
    loading.style.display = 'block';
    clearResults();
    
    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(searchParams)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayDualResults(data);
        } else {
            throw new Error(data.error || 'Search failed');
        }
    } catch (error) {
        console.error('Search error:', error);
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        searchBtn.disabled = false;
        loading.style.display = 'none';
    }
}

function showStatus(message, type = 'success') {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = `status ${type}`;
    status.style.display = 'block';
}

// ==================== Display Dual Results ====================
function displayDualResults(data) {
    const originalResults = document.getElementById('originalResults');
    const similarResults = document.getElementById('similarResults');
    
    // Show extraction info for chat mode
    if (data.mode === 'chat' && data.extraction_info) {
        showExtractionPreview(data.extraction_info);
    }
    
    // Display original results
    const originalTop3 = data.original_results?.top3 || [];
    document.getElementById('originalSearchTerm').textContent = `Searching for: "${data.search_term}"`;
    displayTop3(originalTop3, 'originalTop3');
    originalResults.style.display = 'block';
    
    // Display similar results (if available)
    const similarGifts = data.similar_results?.similar_gifts || [];
    const similarTop3 = data.similar_results?.top3 || [];
    
    if (similarGifts.length > 0 && similarTop3.length > 0) {
        document.getElementById('similarGiftsList').textContent = 
            `Based on: ${similarGifts.join(', ')}`;
        displayTop3(similarTop3, 'similarTop3');
        similarResults.style.display = 'block';
    } else if (data.similar_results?.error) {
        document.getElementById('similarGiftsList').textContent = 
            `AI recommendations unavailable: ${data.similar_results.error}`;
        document.getElementById('similarTop3').innerHTML = 
            '<p class="no-results">No AI recommendations available</p>';
        similarResults.style.display = 'block';
    }
    
    // Status message
    const origCount = originalTop3.length;
    const simCount = similarTop3.length;
    let statusMsg = `Found ${origCount} top results for your search`;
    if (simCount > 0) {
        statusMsg += ` and ${simCount} AI recommended alternatives`;
    }
    showStatus(statusMsg, 'success');
}

function showExtractionPreview(info) {
    const preview = document.getElementById('extractionPreview');
    const details = document.getElementById('extractionDetails');
    
    let html = '<ul>';
    if (info.search_query) html += `<li><strong>Search Query:</strong> ${info.search_query}</li>`;
    if (info.detected_age) html += `<li><strong>Age:</strong> ${info.detected_age} years old</li>`;
    if (info.detected_relationship) html += `<li><strong>For:</strong> ${info.detected_relationship}</li>`;
    if (info.detected_budget) {
        const budget = info.detected_budget;
        let budgetStr = '';
        if (budget.min) budgetStr += `$${budget.min} - `;
        if (budget.max) budgetStr += `$${budget.max}`;
        if (budgetStr) html += `<li><strong>Budget:</strong> ${budgetStr}</li>`;
    }
    if (info.detected_categories && info.detected_categories.length > 0) {
        html += `<li><strong>Categories:</strong> ${info.detected_categories.join(', ')}</li>`;
    }
    html += '</ul>';
    
    details.innerHTML = html;
    preview.style.display = 'block';
}

function displayTop3(products, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (!products || products.length === 0) {
        container.innerHTML = '<p class="no-results">No products found matching your criteria</p>';
        return;
    }
    
    products.forEach((product, index) => {
        const card = createProductCard(product, index + 1);
        container.appendChild(card);
    });
}

// ==================== Product Card Creation ====================
function createProductCard(product, rank) {
    const card = document.createElement('div');
    card.className = `product-card ${product.source.toLowerCase()}`;
    
    // Rank badge
    const rankBadge = document.createElement('div');
    rankBadge.className = 'rank-badge';
    rankBadge.textContent = `#${rank}`;
    card.appendChild(rankBadge);
    
    // Source badge
    const sourceBadge = document.createElement('div');
    sourceBadge.className = `source-badge ${product.source.toLowerCase()}`;
    sourceBadge.textContent = product.source;
    card.appendChild(sourceBadge);
    
    // Image
    const imageDiv = document.createElement('div');
    imageDiv.className = 'product-image';
    if (product.image) {
        const img = document.createElement('img');
        img.src = product.image;
        img.alt = product.title || 'Product';
        img.onerror = () => { imageDiv.innerHTML = '🎁'; imageDiv.classList.add('no-image'); };
        imageDiv.appendChild(img);
    } else {
        imageDiv.innerHTML = '🎁';
        imageDiv.classList.add('no-image');
    }
    card.appendChild(imageDiv);
    
    // Content
    const content = document.createElement('div');
    content.className = 'product-content';
    
    // Title
    const title = document.createElement('h4');
    title.className = 'product-title';
    title.textContent = product.title || 'Unknown Product';
    content.appendChild(title);
    
    // Price
    const price = document.createElement('div');
    price.className = 'product-price';
    price.textContent = product.price ? `$${product.price.toFixed(2)}` : 'Price N/A';
    content.appendChild(price);
    
    // Meta info
    const meta = document.createElement('div');
    meta.className = 'product-meta';
    
    if (product.source === 'eBay' && product.condition) {
        const condition = document.createElement('span');
        condition.className = 'meta-item';
        condition.textContent = `📦 ${product.condition}`;
        meta.appendChild(condition);
    }
    
    if (product.source === 'Amazon' && product.star_rating) {
        const rating = document.createElement('span');
        rating.className = 'meta-item';
        rating.textContent = `⭐ ${product.star_rating}`;
        meta.appendChild(rating);
    }
    
    if (product.min_delivery_date) {
        const delivery = document.createElement('span');
        delivery.className = 'meta-item';
        delivery.textContent = `🚚 ${product.min_delivery_date}`;
        meta.appendChild(delivery);
    }
    
    if (product.quality_score !== undefined) {
        const quality = document.createElement('span');
        quality.className = 'meta-item';
        quality.textContent = `Quality: ${(product.quality_score * 100).toFixed(0)}%`;
        meta.appendChild(quality);
    }
    
    content.appendChild(meta);
    
    // View button
    if (product.url) {
        const btn = document.createElement('a');
        btn.className = 'view-btn';
        btn.href = product.url;
        btn.target = '_blank';
        btn.textContent = `View on ${product.source}`;
        content.appendChild(btn);
    }
    
    card.appendChild(content);
    return card;
}

// ==================== Utility Functions ====================
function extractProductNameFromUrl(url) {
    try {
        const match = url.match(/amazon\.com\/([^/]+)\/dp\//);
        if (match) {
            const namePart = decodeURIComponent(match[1]);
            return namePart.split('-').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
            ).join(' ');
        }
    } catch (e) {
        console.error('Error extracting name:', e);
    }
    return 'Product';
}
    locationDiv.innerHTML = `<strong>Location:</strong><span>${item.itemLocation || 'N/A'}</span>`;
    detailsGrid.appendChild(locationDiv);
    
    // Created Date
    const createdDiv = document.createElement('div');
    createdDiv.className = 'detail-item';
    const dateStr = item.itemCreationDate ? new Date(item.itemCreationDate).toLocaleDateString() : 'N/A';
    createdDiv.innerHTML = `<strong>Listed:</strong><span>${dateStr}</span>`;
    detailsGrid.appendChild(createdDiv);
    
    detailsSection.appendChild(detailsGrid);
    
    // Categories (separate full-width row)
    if (item.categories && item.categories.length > 0) {
        const categoriesDiv = document.createElement('div');
        categoriesDiv.className = 'detail-categories';
        categoriesDiv.innerHTML = `<strong>Categories:</strong><div>${item.categories.join(' → ')}</div>`;
        detailsSection.appendChild(categoriesDiv);
    }
    
    body.appendChild(detailsSection);
    
    // Description
    if (item.description && item.description !== 'N/A') {
        const descSection = createDetailSection('Description');
        const descInfo = document.createElement('div');
        descInfo.className = 'detail-info';
        descInfo.textContent = item.description;
        descSection.appendChild(descInfo);
        body.appendChild(descSection);
    }
    
    // Seller Info
    const sellerSection = createDetailSection('Seller Information');
    const sellerGrid = document.createElement('div');
    sellerGrid.className = 'detail-grid';
    
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'detail-item';
    feedbackDiv.innerHTML = `<strong>Feedback Score:</strong><span>${item.seller_feedbackPercentage || 'N/A'}%</span>`;
    sellerGrid.appendChild(feedbackDiv);
    
    sellerSection.appendChild(sellerGrid);
    body.appendChild(sellerSection);
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
}

function showAmazonDetails(item) {
    let title = item.product_title || 'N/A';
    if (title === 'LEGO' || title === 'N/A') {
        title = extractProductNameFromUrl(item.product_url);
    }
    
    const modal = createModal('Amazon Item Details');
    const body = modal.querySelector('.modal-body');
    
    // Title
    const titleElem = document.createElement('h2');
    titleElem.textContent = title;
    titleElem.style.marginBottom = '20px';
    body.appendChild(titleElem);
    
    // Image
    if (item.product_photo) {
        const section = createDetailSection('Product Image');
        const img = document.createElement('img');
        img.src = item.product_photo;
        img.style.maxWidth = '300px';
        img.style.borderRadius = '8px';
        section.appendChild(img);
        body.appendChild(section);
    }
    
    // Price
    const priceSection = createDetailSection('Price Information');
    const priceGrid = document.createElement('div');
    priceGrid.className = 'detail-grid';
    
    // Current Price
    const currentPriceDiv = document.createElement('div');
    currentPriceDiv.className = 'detail-item';
    currentPriceDiv.innerHTML = `<strong>Current Price:</strong><span>$${item.product_price || 'N/A'}</span>`;
    priceGrid.appendChild(currentPriceDiv);
    
    // Original Price
    if (item.product_original_price) {
        const origPriceDiv = document.createElement('div');
        origPriceDiv.className = 'detail-item';
        origPriceDiv.innerHTML = `<strong>Original Price:</strong><span>$${item.product_original_price}</span>`;
        priceGrid.appendChild(origPriceDiv);
    }
    
    // Prime Status
    if (item.is_prime) {
        const primeDiv = document.createElement('div');
        primeDiv.className = 'detail-item';
        primeDiv.innerHTML = `<strong>📦 Prime Eligible:</strong><span>Yes</span>`;
        priceGrid.appendChild(primeDiv);
    }
    
    priceSection.appendChild(priceGrid);
    body.appendChild(priceSection);
    
    // Reviews & Availability Combined
    const detailsSection = createDetailSection('Item Details');
    const detailsGrid = document.createElement('div');
    detailsGrid.className = 'detail-grid';
    
    // Rating
    if (item.product_star_rating) {
        const ratingDiv = document.createElement('div');
        ratingDiv.className = 'detail-item';
        ratingDiv.innerHTML = `<strong>⭐ Rating:</strong><span>${item.product_star_rating} stars</span>`;
        detailsGrid.appendChild(ratingDiv);
    }
    
    // Reviews Count
    if (item.product_num_ratings) {
        const reviewsDiv = document.createElement('div');
        reviewsDiv.className = 'detail-item';
        reviewsDiv.innerHTML = `<strong>Total Reviews:</strong><span>${item.product_num_ratings}</span>`;
        detailsGrid.appendChild(reviewsDiv);
    }
    
    // Availability
    const availDiv = document.createElement('div');
    availDiv.className = 'detail-item';
    availDiv.innerHTML = `<strong>In Stock:</strong><span>${item.product_availability || 'N/A'}</span>`;
    detailsGrid.appendChild(availDiv);
    
    // ASIN
    const asinDiv = document.createElement('div');
    asinDiv.className = 'detail-item';
    asinDiv.innerHTML = `<strong>ASIN:</strong><span>${item.asin || 'N/A'}</span>`;
    detailsGrid.appendChild(asinDiv);
    
    detailsSection.appendChild(detailsGrid);
    body.appendChild(detailsSection);
    
    // Delivery
    if (item.product_delivery_info) {
        const deliverySection = createDetailSection('Delivery Information');
        const deliveryGrid = document.createElement('div');
        deliveryGrid.className = 'detail-grid';
        
        const parsed = parseDeliveryInfo(item.product_delivery_info);
        
        // Shipping Cost
        const costDiv = document.createElement('div');
        costDiv.className = 'detail-item';
        costDiv.innerHTML = `<strong>🚚 Shipping Cost:</strong><span>${parsed.cost || 'N/A'}</span>`;
        deliveryGrid.appendChild(costDiv);
        
        // Delivery Date
        if (parsed.dates) {
            const datesDiv = document.createElement('div');
            datesDiv.className = 'detail-item';
            datesDiv.innerHTML = `<strong>📅 Estimated Arrival:</strong><span>${parsed.dates}</span>`;
            deliveryGrid.appendChild(datesDiv);
        }
        
        deliverySection.appendChild(deliveryGrid);
        body.appendChild(deliverySection);
    }
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
}

function createModal(title) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    const content = document.createElement('div');
    content.className = 'modal-content';
    
    const header = document.createElement('div');
    header.className = 'modal-header';
    
    const headerTitle = document.createElement('h2');
    headerTitle.textContent = title;
    
    const close = document.createElement('span');
    close.className = 'close';
    close.innerHTML = '&times;';
    close.onclick = () => modal.remove();
    
    header.appendChild(headerTitle);
    header.appendChild(close);
    
    const body = document.createElement('div');
    body.className = 'modal-body';
    
    content.appendChild(header);
    content.appendChild(body);
    modal.appendChild(content);
    
    // Close on outside click
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    
    return modal;
}

function createDetailSection(title, subtitle = '') {
    const section = document.createElement('div');
    section.className = 'detail-section';
    
    const heading = document.createElement('h3');
    heading.textContent = title;
    if (subtitle) {
        heading.textContent += ` (${subtitle})`;
    }
    
    section.appendChild(heading);
    return section;
}
