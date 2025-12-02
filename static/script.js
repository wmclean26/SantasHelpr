// Mode toggle functionality
const filterModeBtn = document.getElementById('filterModeBtn');
const chatModeBtn = document.getElementById('chatModeBtn');
const filterMode = document.getElementById('filterMode');
const chatMode = document.getElementById('chatMode');

filterModeBtn.addEventListener('click', () => {
    filterModeBtn.classList.add('active');
    chatModeBtn.classList.remove('active');
    filterMode.style.display = 'block';
    chatMode.style.display = 'none';
    document.getElementById('results').innerHTML = '';
    document.getElementById('status').style.display = 'none';
});

chatModeBtn.addEventListener('click', () => {
    chatModeBtn.classList.add('active');
    filterModeBtn.classList.remove('active');
    chatMode.style.display = 'block';
    filterMode.style.display = 'none';
    document.getElementById('results').innerHTML = '';
    document.getElementById('status').style.display = 'none';
});

// Main search functionality (Filter Mode)
document.getElementById('searchBtn').addEventListener('click', performSearch);

// Allow Enter key in product input
document.getElementById('product').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

// Chat Mode search functionality
document.getElementById('chatSearchBtn').addEventListener('click', performChatSearch);
document.getElementById('chatInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performChatSearch();
});

async function performChatSearch() {
    const searchBtn = document.getElementById('chatSearchBtn');
    const loading = document.getElementById('loading');
    const status = document.getElementById('status');
    const results = document.getElementById('results');
    const extractedInfo = document.getElementById('extractedInfo');
    const chatInput = document.getElementById('chatInput');
    
    const message = chatInput.value.trim();
    if (!message) {
        status.textContent = 'Please enter what you\'re looking for';
        status.className = 'status error';
        status.style.display = 'block';
        return;
    }
    
    // Show loading state
    searchBtn.disabled = true;
    loading.style.display = 'block';
    status.style.display = 'none';
    results.innerHTML = '';
    extractedInfo.style.display = 'none';
    
    try {
        const response = await fetch('/chat-search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show what was extracted
            const ext = data.extracted;
            const meta = ext.metadata;
            
            let infoHtml = `<h4>🎁 Santa Understood Your Request 🎅</h4>`;
            infoHtml += `<p><span class="label">Searching for:</span> ${ext.query}</p>`;
            
            if (ext.min_price || ext.max_price) {
                infoHtml += `<p><span class="label">Price range:</span> $${ext.min_price || '0'} - $${ext.max_price || 'any'}</p>`;
            }
            if (meta.relationship) {
                let recipientInfo = meta.relationship;
                if (meta.demographic) {
                    recipientInfo += ` (${meta.demographic})`;
                }
                infoHtml += `<p><span class="label">Recipient:</span> ${recipientInfo}</p>`;
            }
            if (meta.age) {
                infoHtml += `<p><span class="label">Age:</span> ${meta.age} years old</p>`;
            }
            if (meta.categories && meta.categories.length > 0) {
                infoHtml += `<p><span class="label">Categories:</span> ${meta.categories.join(', ')}</p>`;
            }
            if (meta.keywords && meta.keywords.length > 0) {
                infoHtml += `<p><span class="label">Keywords:</span> ${meta.keywords.slice(0, 5).join(', ')}</p>`;
            }
            
            extractedInfo.innerHTML = infoHtml;
            extractedInfo.style.display = 'block';
            
            displayResults(data);
            
            // Show status
            const totalCount = data.total_count || 0;
            const mainCount = data.products ? data.products.filter(p => p.product_type === 'main').length : 0;
            const similarCount = data.products ? data.products.filter(p => p.product_type === 'similar').length : 0;
            let statusMsg = `Found ${mainCount} main results, ${similarCount} similar recommendations`;
            
            status.textContent = statusMsg;
            status.className = 'status success';
            status.style.display = 'block';
        } else {
            throw new Error(data.error || 'Search failed');
        }
    } catch (error) {
        console.error('Chat search error:', error);
        status.textContent = `Error: ${error.message}`;
        status.className = 'status error';
        status.style.display = 'block';
    } finally {
        searchBtn.disabled = false;
        loading.style.display = 'none';
    }
}

async function performSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const status = document.getElementById('status');
    const results = document.getElementById('results');
    
    // Get all search parameters
    const searchParams = {
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
    
    // Show loading state
    searchBtn.disabled = true;
    loading.style.display = 'block';
    status.style.display = 'none';
    results.innerHTML = '';
    
    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchParams)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            
            // Show status
            const totalCount = data.total_count || 0;
            const mainCount = data.products ? data.products.filter(p => p.product_type === 'main').length : 0;
            const similarCount = data.products ? data.products.filter(p => p.product_type === 'similar').length : 0;
            let statusMsg = `Found ${mainCount} main results, ${similarCount} AI-recommended similar items`;
            
            status.textContent = statusMsg;
            status.className = 'status success';
            status.style.display = 'block';
        } else {
            throw new Error(data.error || 'Search failed');
        }
    } catch (error) {
        console.error('Search error:', error);
        status.textContent = `Error: ${error.message}`;
        status.className = 'status error';
        status.style.display = 'block';
    } finally {
        searchBtn.disabled = false;
        loading.style.display = 'none';
    }
}

function displayResults(data) {
    const results = document.getElementById('results');
    results.innerHTML = '';
    
    const products = data.products || [];
    
    if (products.length === 0) {
        results.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">No results found. Try adjusting your filters.</p>';
        return;
    }
    
    // Separate main and similar products
    const mainProducts = products.filter(p => p.product_type === 'main');
    const similarProducts = products.filter(p => p.product_type === 'similar');
    
    // Display main results
    if (mainProducts.length > 0) {
        const mainSection = createUnifiedResultSection('🎁 Top Results', mainProducts, 'main');
        results.appendChild(mainSection);
    }
    
    // Display similar/recommended results
    if (similarProducts.length > 0) {
        const similarSection = createUnifiedResultSection('✨ AI-Recommended Similar Items', similarProducts, 'similar');
        results.appendChild(similarSection);
    }
}

function createUnifiedResultSection(title, items, sectionType) {
    const section = document.createElement('div');
    section.className = 'result-group';
    
    const header = document.createElement('div');
    header.className = `result-header ${sectionType === 'similar' ? 'similar' : ''}`;
    header.textContent = `${title} (${items.length} items)`;
    section.appendChild(header);
    
    items.forEach((item, index) => {
        const card = createUnifiedCard(item, index);
        section.appendChild(card);
    });
    
    return section;
}

function createUnifiedCard(item, index) {
    const card = document.createElement('div');
    card.className = 'item-card';
    
    const isEbay = item.source === 'eBay';
    const isAmazon = item.source === 'Amazon';
    
    // Source badge
    const sourceBadge = document.createElement('div');
    sourceBadge.className = `source-badge ${isEbay ? 'ebay' : 'amazon'}`;
    sourceBadge.textContent = item.source;
    
    // Image
    const imageDiv = document.createElement('div');
    imageDiv.className = 'item-image';
    
    // Handle different image field names from compare function vs raw data
    let imageSrc = item.image || null;
    if (!imageSrc && isEbay) {
        const images = item.images || [];
        imageSrc = images.length > 0 ? images[0] : null;
    }
    if (!imageSrc && isAmazon) {
        imageSrc = item.product_photo || null;
    }
    
    if (imageSrc) {
        const img = document.createElement('img');
        img.src = imageSrc;
        img.alt = item.title || item.product_title || 'Product';
        img.onerror = () => { imageDiv.innerHTML = 'No Image<br>Available'; imageDiv.classList.add('no-image'); };
        imageDiv.appendChild(img);
    } else {
        imageDiv.innerHTML = 'No Image<br>Available';
        imageDiv.classList.add('no-image');
    }
    imageDiv.appendChild(sourceBadge);
    
    // Details
    const details = document.createElement('div');
    details.className = 'item-details';
    
    // Title - handle both compare format (title) and raw format (product_title for Amazon)
    let titleText = item.title || item.product_title || 'Unknown Product';
    if (titleText === 'LEGO' || titleText === 'N/A') {
        titleText = extractProductNameFromUrl(item.url || item.product_url) || 'Unknown Product';
    }
    
    const titleLink = document.createElement('a');
    titleLink.className = 'item-title';
    titleLink.textContent = titleText;
    titleLink.href = item.url || item.product_url || '#';
    titleLink.target = '_blank';
    
    // Price - handle both numeric (from compare) and string formats
    const price = document.createElement('div');
    price.className = 'item-price';
    let priceText = 'N/A';
    
    if (item.price !== null && item.price !== undefined) {
        // Price from compare function is already numeric
        if (typeof item.price === 'number') {
            priceText = `$${item.price.toFixed(2)}`;
        } else {
            // String format - clean it up
            let priceVal = String(item.price).replace(/^\$/, '').replace(/^USD\s*/, '').trim();
            if (priceVal && !isNaN(parseFloat(priceVal))) {
                priceText = `$${parseFloat(priceVal).toFixed(2)}`;
            } else {
                priceText = item.price;
            }
        }
    } else if (item.product_price) {
        // Amazon raw format
        let priceVal = String(item.product_price).replace(/^\$/, '').replace(/^USD\s*/, '').trim();
        if (priceVal && !isNaN(parseFloat(priceVal))) {
            priceText = `$${parseFloat(priceVal).toFixed(2)}`;
        }
    }
    
    // Handle discount/original price - unified format for both eBay and Amazon
    if (isEbay && item.market_price && item.market_price.discount_percentage) {
        priceText += ` <span class="discount-text">(${item.market_price.discount_percentage}% off - was $${item.market_price.original})</span>`;
    }
    if (isAmazon && item.product_original_price && priceText !== 'N/A') {
        let origPrice = String(item.product_original_price).replace(/^\$/, '').trim();
        let currentPrice = parseFloat(String(item.product_price || item.price).replace(/^\$/, ''));
        let originalPrice = parseFloat(origPrice);
        
        if (!isNaN(originalPrice) && !isNaN(currentPrice) && originalPrice > currentPrice) {
            const discount = Math.round((1 - currentPrice / originalPrice) * 100);
            priceText += ` <span class="discount-text">(${discount}% off - was $${originalPrice.toFixed(2)})</span>`;
        }
    }
    price.innerHTML = priceText;
    
    // Info / Meta
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    
    if (isEbay) {
        // Condition (from compare or rich format)
        if (item.condition) {
            const condition = document.createElement('span');
            condition.textContent = `📦 ${item.condition}`;
            meta.appendChild(condition);
        }
        
        // Location (rich format only)
        if (item.itemLocation) {
            const location = document.createElement('span');
            location.textContent = `📍 ${item.itemLocation}`;
            meta.appendChild(location);
        }
        
        // Shipping (rich format)
        const shippingOpts = item.shippingOptions || [];
        if (shippingOpts.length > 0) {
            const shipping = document.createElement('span');
            const shipCost = shippingOpts[0].cost;
            if (shipCost === '0.00' || shipCost === '0.0' || shipCost === 0 || shipCost === '0') {
                shipping.innerHTML = '<span class="badge free-shipping">🚚 FREE SHIPPING</span>';
            } else {
                shipping.textContent = `🚚 $${shipCost}`;
            }
            meta.appendChild(shipping);
        }
        
        // Delivery date (from compare format) - format nicely
        if (item.min_delivery_date) {
            const delivery = document.createElement('span');
            const formattedDate = formatDeliveryDate(item.min_delivery_date);
            delivery.textContent = `📅 Arrives ${formattedDate}`;
            meta.appendChild(delivery);
        }
        
        // Seller rating (rich format)
        if (item.seller_feedbackPercentage && item.seller_feedbackPercentage !== 'N/A') {
            const seller = document.createElement('span');
            seller.textContent = `⭐ ${item.seller_feedbackPercentage}% seller`;
            meta.appendChild(seller);
        }
    } else {
        // Amazon meta
        // Rating (from compare: star_rating, or rich format: product_star_rating)
        const starRating = item.star_rating || item.product_star_rating;
        if (starRating) {
            const rating = document.createElement('span');
            rating.textContent = `⭐ ${starRating}`;
            meta.appendChild(rating);
        }
        
        if (item.is_prime) {
            const prime = document.createElement('span');
            prime.innerHTML = '<span class="badge prime">📦 Prime</span>';
            meta.appendChild(prime);
        }
        
        // Delivery date - format nicely and avoid duplicates
        let amazonDeliveryShown = false;
        if (item.min_delivery_date) {
            const delivery = document.createElement('span');
            const formattedDate = formatDeliveryDate(item.min_delivery_date);
            delivery.textContent = `📅 Arrives ${formattedDate}`;
            meta.appendChild(delivery);
            amazonDeliveryShown = true;
        }
        
        // Delivery info (rich format) - only show if not already shown
        if (!amazonDeliveryShown && item.product_delivery_info) {
            const deliveryInfo = item.product_delivery_info;
            if (typeof deliveryInfo === 'object' && deliveryInfo.minDelivery) {
                const delivery = document.createElement('span');
                const formattedDate = formatDeliveryDate(deliveryInfo.minDelivery);
                delivery.textContent = `📅 Arrives ${formattedDate}`;
                meta.appendChild(delivery);
            }
        }
    }
    
    // Similar search term badge (for similar products)
    if (item.search_term && item.product_type === 'similar') {
        const searchTermBadge = document.createElement('div');
        searchTermBadge.className = 'search-term-badge';
        searchTermBadge.textContent = `🔍 "${item.search_term}"`;
        details.appendChild(searchTermBadge);
    }
    
    // Description (eBay only, truncated)
    if (isEbay && item.description && item.description !== 'N/A') {
        const desc = document.createElement('div');
        desc.className = 'item-description';
        desc.textContent = item.description.length > 100 ? item.description.substring(0, 100) + '...' : item.description;
        details.appendChild(desc);
    }
    
    // Actions
    const actions = document.createElement('div');
    actions.className = 'item-actions';
    
    const detailsBtn = document.createElement('button');
    detailsBtn.className = 'btn btn-details';
    detailsBtn.textContent = '📋 Details';
    detailsBtn.onclick = () => isEbay ? showEbayDetails(item) : showAmazonDetails(item);
    
    const linkBtn = document.createElement('button');
    linkBtn.className = 'btn btn-link';
    linkBtn.textContent = `🔗 View on ${item.source}`;
    linkBtn.onclick = () => window.open(item.url || item.product_url, '_blank');
    
    actions.appendChild(detailsBtn);
    actions.appendChild(linkBtn);
    
    details.appendChild(titleLink);
    details.appendChild(price);
    details.appendChild(meta);
    details.appendChild(actions);
    
    card.appendChild(imageDiv);
    card.appendChild(details);
    
    return card;
}

function createEbayCard(item, index) {
    const card = document.createElement('div');
    card.className = 'item-card';
    
    // Image
    const imageDiv = document.createElement('div');
    imageDiv.className = 'item-image';
    
    const images = item.images || [];
    if (images.length > 0 && images[0]) {
        const img = document.createElement('img');
        img.src = images[0];
        img.alt = item.title;
        img.onerror = () => { imageDiv.innerHTML = 'No Image<br>Available'; imageDiv.classList.add('no-image'); };
        imageDiv.appendChild(img);
    } else {
        imageDiv.innerHTML = 'No Image<br>Available';
        imageDiv.classList.add('no-image');
    }
    
    // Details
    const details = document.createElement('div');
    details.className = 'item-details';
    
    // Title
    const title = document.createElement('a');
    title.className = 'item-title';
    title.textContent = item.title || 'N/A';
    title.href = item.url || '#';
    title.target = '_blank';
    
    // Price
    const price = document.createElement('div');
    price.className = 'item-price';
    let priceText = item.price || 'N/A';
    const marketPrice = item.market_price || {};
    if (marketPrice.discount_percentage) {
        priceText += ` (Save ${marketPrice.discount_percentage}% - was $${marketPrice.original})`;
    }
    price.textContent = priceText;
    
    // Info
    const info = document.createElement('div');
    info.className = 'item-info';
    let infoText = `Condition: ${item.condition || 'N/A'}`;
    if (item.seller_feedbackPercentage && item.seller_feedbackPercentage !== 'N/A') {
        infoText += ` | Seller: ${item.seller_feedbackPercentage}% positive`;
    }
    info.textContent = infoText;
    
    // Meta
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    
    const location = document.createElement('span');
    location.textContent = `📍 ${item.itemLocation || 'N/A'}`;
    meta.appendChild(location);
    
    const shippingOpts = item.shippingOptions || [];
    if (shippingOpts.length > 0) {
        const shipping = document.createElement('span');
        const shipCost = shippingOpts[0].cost;
        if (shipCost === '0.0' || shipCost === 0) {
            shipping.innerHTML = '<span class="badge free-shipping">🚚 FREE SHIPPING</span>';
        } else {
            shipping.textContent = `🚚 Shipping: $${shipCost}`;
        }
        meta.appendChild(shipping);
    }
    
    // Description
    if (item.description && item.description !== 'N/A') {
        const desc = document.createElement('div');
        desc.className = 'item-description';
        desc.textContent = item.description.length > 100 ? item.description.substring(0, 100) + '...' : item.description;
        details.appendChild(desc);
    }
    
    // Actions
    const actions = document.createElement('div');
    actions.className = 'item-actions';
    
    const detailsBtn = document.createElement('button');
    detailsBtn.className = 'btn btn-details';
    detailsBtn.textContent = '📋 Full Details';
    detailsBtn.onclick = () => showEbayDetails(item);
    
    const linkBtn = document.createElement('button');
    linkBtn.className = 'btn btn-link';
    linkBtn.textContent = '🔗 View on eBay';
    linkBtn.onclick = () => window.open(item.url, '_blank');
    
    actions.appendChild(detailsBtn);
    actions.appendChild(linkBtn);
    
    details.appendChild(title);
    details.appendChild(price);
    details.appendChild(info);
    details.appendChild(meta);
    details.appendChild(actions);
    
    card.appendChild(imageDiv);
    card.appendChild(details);
    
    return card;
}

function createAmazonCard(item, index) {
    const card = document.createElement('div');
    card.className = 'item-card';
    
    // Image
    const imageDiv = document.createElement('div');
    imageDiv.className = 'item-image';
    
    if (item.product_photo) {
        const img = document.createElement('img');
        img.src = item.product_photo;
        img.alt = item.product_title;
        img.onerror = () => { imageDiv.innerHTML = 'No Image<br>Available'; imageDiv.classList.add('no-image'); };
        imageDiv.appendChild(img);
    } else {
        imageDiv.innerHTML = 'No Image<br>Available';
        imageDiv.classList.add('no-image');
    }
    
    // Details
    const details = document.createElement('div');
    details.className = 'item-details';
    
    // Title - Extract from URL if needed
    let title = item.product_title || 'N/A';
    if (title === 'LEGO' || title === 'N/A') {
        title = extractProductNameFromUrl(item.product_url);
    }
    
    const titleLink = document.createElement('a');
    titleLink.className = 'item-title';
    titleLink.textContent = title;
    titleLink.href = item.product_url || '#';
    titleLink.target = '_blank';
    
    // Price - handle various formats from Amazon API
    const price = document.createElement('div');
    price.className = 'item-price';
    let priceText = null;
    let priceValue = null;
    
    // Try product_price first (most common)
    if (item.product_price !== null && item.product_price !== undefined && item.product_price !== '' && item.product_price !== 'null') {
        // Remove any existing $ sign and format
        let priceVal = String(item.product_price).replace(/^\$/, '').trim();
        if (priceVal && !isNaN(parseFloat(priceVal))) {
            priceValue = parseFloat(priceVal);
            priceText = `$${priceValue.toFixed(2)}`;
        }
    }
    // Fallback to product_original_price if product_price is not available
    else if (item.product_original_price !== null && item.product_original_price !== undefined && item.product_original_price !== '' && item.product_original_price !== 'null') {
        let priceVal = String(item.product_original_price).replace(/^\$/, '').trim();
        // Handle malformed prices like "6.496.49"
        if (priceVal.length > 6 && priceVal.indexOf('.') !== priceVal.lastIndexOf('.')) {
            priceVal = priceVal.substring(0, priceVal.length / 2);
        }
        if (priceVal && !isNaN(parseFloat(priceVal))) {
            priceValue = parseFloat(priceVal);
            priceText = `$${priceValue.toFixed(2)}`;
        }
    }
    
    // If still no price, show unavailable message
    if (priceText === null) {
        priceText = '<span class="price-unavailable">See price on Amazon</span>';
    } else {
        // Show original price with discount if available
        if (item.product_original_price !== null && item.product_original_price !== undefined && item.product_price) {
            let origPrice = String(item.product_original_price).replace(/^\$/, '').trim();
            // Handle malformed prices
            if (origPrice.length > 6 && origPrice.indexOf('.') !== origPrice.lastIndexOf('.')) {
                origPrice = origPrice.substring(0, origPrice.length / 2);
            }
            let currentPrice = parseFloat(String(item.product_price).replace(/^\$/, ''));
            let originalPrice = parseFloat(origPrice);
            
            if (!isNaN(originalPrice) && !isNaN(currentPrice) && originalPrice > currentPrice) {
                const discount = Math.round((1 - currentPrice / originalPrice) * 100);
                priceText += ` <span class="original-price">(was $${originalPrice.toFixed(2)}, ${discount}% off)</span>`;
            }
        }
    }
    
    price.innerHTML = priceText;
    
    // Info
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    
    if (item.product_star_rating) {
        const rating = document.createElement('span');
        rating.textContent = `⭐ ${item.product_star_rating} stars`;
        meta.appendChild(rating);
    }
    
    if (item.product_num_ratings) {
        const reviews = document.createElement('span');
        reviews.textContent = `(${item.product_num_ratings} reviews)`;
        meta.appendChild(reviews);
    }
    
    if (item.is_prime) {
        const prime = document.createElement('span');
        prime.innerHTML = '<span class="badge prime">📦 Prime</span>';
        meta.appendChild(prime);
    }
    
    // Delivery info
    if (item.product_delivery_info) {
        const deliveryInfo = parseDeliveryInfo(item.product_delivery_info);
        if (deliveryInfo.cost) {
            const cost = document.createElement('div');
            cost.className = 'item-info';
            cost.textContent = `🚚 Shipping: ${deliveryInfo.cost}`;
            details.appendChild(cost);
        }
        if (deliveryInfo.dates) {
            const dates = document.createElement('div');
            dates.className = 'item-info';
            dates.textContent = `📅 Delivery: ${deliveryInfo.dates}`;
            details.appendChild(dates);
        }
    }
    
    // Actions
    const actions = document.createElement('div');
    actions.className = 'item-actions';
    
    const detailsBtn = document.createElement('button');
    detailsBtn.className = 'btn btn-details';
    detailsBtn.textContent = '📋 Full Details';
    detailsBtn.onclick = () => showAmazonDetails(item);
    
    const linkBtn = document.createElement('button');
    linkBtn.className = 'btn btn-link';
    linkBtn.textContent = '🔗 View on Amazon';
    linkBtn.onclick = () => window.open(item.product_url, '_blank');
    
    actions.appendChild(detailsBtn);
    actions.appendChild(linkBtn);
    
    details.appendChild(titleLink);
    details.appendChild(price);
    details.appendChild(meta);
    details.appendChild(actions);
    
    card.appendChild(imageDiv);
    card.appendChild(details);
    
    return card;
}

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
    return 'LEGO';
}

function parseDeliveryInfo(deliveryInfo) {
    const result = { cost: '', dates: '' };
    
    if (deliveryInfo.includes('FREE delivery')) {
        result.cost = 'FREE';
        const remaining = deliveryInfo.replace('FREE delivery', '').trim();
        const dateMatch = remaining.match(/([A-Z][a-z]{2}\s+\d{1,2}(?:\s*-\s*\d{1,2})?)/);
        if (dateMatch) result.dates = dateMatch[1];
    } else if (deliveryInfo.includes('$')) {
        const costMatch = deliveryInfo.match(/\$[\d.]+/);
        if (costMatch) result.cost = costMatch[0];
        
        const costEnd = deliveryInfo.indexOf('delivery');
        const remaining = costEnd !== -1 ? deliveryInfo.substring(costEnd + 8) : deliveryInfo;
        const dateMatch = remaining.match(/([A-Z][a-z]{2}\s+\d{1,2}(?:\s*-\s*\d{1,2})?)/);
        if (dateMatch) result.dates = dateMatch[1];
    }
    
    return result;
}

// Format delivery date to be more readable
function formatDeliveryDate(dateStr) {
    if (!dateStr) return 'N/A';
    
    try {
        // Handle ISO date format (2025-12-04)
        if (dateStr.match(/^\d{4}-\d{2}-\d{2}/)) {
            const date = new Date(dateStr);
            const options = { weekday: 'short', month: 'short', day: 'numeric' };
            return date.toLocaleDateString('en-US', options);
        }
        return dateStr;
    } catch (e) {
        return dateStr;
    }
}

// Modal functionality
function showEbayDetails(item) {
    const modal = createModal('eBay Item Details');
    const body = modal.querySelector('.modal-body');
    
    // Title - handle both compare format and rich format
    const title = document.createElement('h2');
    title.textContent = item.title || 'Unknown Product';
    title.style.marginBottom = '20px';
    body.appendChild(title);
    
    // Images (only for rich format)
    const imageSrc = item.image || (item.images && item.images.length > 0 ? item.images[0] : null);
    if (imageSrc) {
        const section = createDetailSection('Image');
        const imgContainer = document.createElement('div');
        imgContainer.className = 'detail-images';
        
        const images = item.images || [imageSrc];
        images.slice(0, 5).forEach(imgUrl => {
            if (imgUrl) {
                const img = document.createElement('img');
                img.src = imgUrl;
                img.alt = 'Product image';
                imgContainer.appendChild(img);
            }
        });
        section.appendChild(imgContainer);
        body.appendChild(section);
    }
    
    // Price
    const priceSection = createDetailSection('Price Information');
    const priceGrid = document.createElement('div');
    priceGrid.className = 'detail-grid';
    
    // Current Price - handle both numeric (compare) and string formats
    const currentPriceDiv = document.createElement('div');
    currentPriceDiv.className = 'detail-item';
    let priceDisplay = 'N/A';
    if (typeof item.price === 'number') {
        priceDisplay = `$${item.price.toFixed(2)}`;
    } else if (item.price) {
        priceDisplay = item.price;
    }
    currentPriceDiv.innerHTML = `<strong>Current Price:</strong><span>${priceDisplay}</span>`;
    priceGrid.appendChild(currentPriceDiv);
    
    // Original Price & Discount (rich format only)
    const marketPrice = item.market_price || {};
    if (marketPrice.original) {
        const origPriceDiv = document.createElement('div');
        origPriceDiv.className = 'detail-item';
        origPriceDiv.innerHTML = `<strong>Original Price:</strong><span>$${marketPrice.original}</span>`;
        priceGrid.appendChild(origPriceDiv);
        
        const discountDiv = document.createElement('div');
        discountDiv.className = 'detail-item';
        discountDiv.innerHTML = `<strong>Discount:</strong><span>$${marketPrice.discount} (${marketPrice.discount_percentage}% OFF)</span>`;
        priceGrid.appendChild(discountDiv);
    }
    
    // Shipping Cost
    const shippingOpts = item.shippingOptions || [];
    if (shippingOpts.length > 0) {
        const cost = shippingOpts[0].cost;
        const shippingDiv = document.createElement('div');
        shippingDiv.className = 'detail-item';
        shippingDiv.innerHTML = `<strong>Shipping:</strong><span>${cost === '0.0' || cost === 0 ? 'FREE' : '$' + cost}</span>`;
        priceGrid.appendChild(shippingDiv);
    }
    
    priceSection.appendChild(priceGrid);
    body.appendChild(priceSection);
    
    // Item Details
    const detailsSection = createDetailSection('Item Details');
    const detailsGrid = document.createElement('div');
    detailsGrid.className = 'detail-grid';
    
    // Condition
    const conditionDiv = document.createElement('div');
    conditionDiv.className = 'detail-item';
    conditionDiv.innerHTML = `<strong>Condition:</strong><span>${item.condition || 'N/A'}</span>`;
    detailsGrid.appendChild(conditionDiv);
    
    // Location
    const locationDiv = document.createElement('div');
    locationDiv.className = 'detail-item';
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
    // Handle both compare format (title) and rich format (product_title)
    let title = item.title || item.product_title || 'N/A';
    if (title === 'LEGO' || title === 'N/A') {
        title = extractProductNameFromUrl(item.url || item.product_url) || 'Unknown Product';
    }
    
    const modal = createModal('Amazon Item Details');
    const body = modal.querySelector('.modal-body');
    
    // Title
    const titleElem = document.createElement('h2');
    titleElem.textContent = title;
    titleElem.style.marginBottom = '20px';
    body.appendChild(titleElem);
    
    // Image - handle both compare format (image) and rich format (product_photo)
    const imageSrc = item.image || item.product_photo;
    if (imageSrc) {
        const section = createDetailSection('Product Image');
        const img = document.createElement('img');
        img.src = imageSrc;
        img.style.maxWidth = '300px';
        img.style.borderRadius = '8px';
        section.appendChild(img);
        body.appendChild(section);
    }
    
    // Price
    const priceSection = createDetailSection('Price Information');
    const priceGrid = document.createElement('div');
    priceGrid.className = 'detail-grid';
    
    // Current Price - handle both numeric (compare) and string formats
    const currentPriceDiv = document.createElement('div');
    currentPriceDiv.className = 'detail-item';
    let priceDisplay = 'N/A';
    const priceVal = item.price !== undefined ? item.price : item.product_price;
    if (typeof priceVal === 'number') {
        priceDisplay = `$${priceVal.toFixed(2)}`;
    } else if (priceVal) {
        let cleanPrice = String(priceVal).replace(/^\$/, '').trim();
        if (!isNaN(parseFloat(cleanPrice))) {
            priceDisplay = `$${parseFloat(cleanPrice).toFixed(2)}`;
        } else {
            priceDisplay = priceVal;
        }
    }
    currentPriceDiv.innerHTML = `<strong>Current Price:</strong><span>${priceDisplay}</span>`;
    priceGrid.appendChild(currentPriceDiv);
    
    // Original Price (rich format only)
    if (item.product_original_price) {
        const origPriceDiv = document.createElement('div');
        origPriceDiv.className = 'detail-item';
        origPriceDiv.innerHTML = `<strong>Original Price:</strong><span>$${item.product_original_price}</span>`;
        priceGrid.appendChild(origPriceDiv);
    }
    
    // Prime Status (rich format only)
    if (item.is_prime) {
        const primeDiv = document.createElement('div');
        primeDiv.className = 'detail-item';
        primeDiv.innerHTML = `<strong>📦 Prime Eligible:</strong><span>Yes</span>`;
        priceGrid.appendChild(primeDiv);
    }
    
    priceSection.appendChild(priceGrid);
    body.appendChild(priceSection);
    
    // Item Details Section
    const detailsSection = createDetailSection('Item Details');
    const detailsGrid = document.createElement('div');
    detailsGrid.className = 'detail-grid';
    
    // Star rating - handle both formats
    const starRating = item.star_rating || item.product_star_rating;
    if (starRating) {
        const ratingDiv = document.createElement('div');
        ratingDiv.className = 'detail-item';
        ratingDiv.innerHTML = `<strong>⭐ Rating:</strong><span>${starRating} stars</span>`;
        detailsGrid.appendChild(ratingDiv);
    }
    
    // ASIN - extract from URL if not directly available
    let asin = item.asin;
    if (!asin) {
        const productUrl = item.url || item.product_url || '';
        const asinMatch = productUrl.match(/\/dp\/([A-Z0-9]{10})/i) || productUrl.match(/\/product\/([A-Z0-9]{10})/i);
        if (asinMatch) {
            asin = asinMatch[1];
        }
    }
    if (asin) {
        const asinDiv = document.createElement('div');
        asinDiv.className = 'detail-item';
        asinDiv.innerHTML = `<strong>ASIN:</strong><span>${asin}</span>`;
        detailsGrid.appendChild(asinDiv);
    }
    
    // Availability / In Stock
    if (item.product_availability) {
        const availDiv = document.createElement('div');
        availDiv.className = 'detail-item';
        availDiv.innerHTML = `<strong>Availability:</strong><span>${item.product_availability}</span>`;
        detailsGrid.appendChild(availDiv);
    } else if (item.sales_volume) {
        // Use sales volume as proxy for stock status
        const availDiv = document.createElement('div');
        availDiv.className = 'detail-item';
        availDiv.innerHTML = `<strong>Sales:</strong><span>${item.sales_volume}</span>`;
        detailsGrid.appendChild(availDiv);
    }
    
    // Reviews Count
    if (item.product_num_ratings) {
        const reviewsDiv = document.createElement('div');
        reviewsDiv.className = 'detail-item';
        reviewsDiv.innerHTML = `<strong>Total Reviews:</strong><span>${item.product_num_ratings}</span>`;
        detailsGrid.appendChild(reviewsDiv);
    }
    
    detailsSection.appendChild(detailsGrid);
    body.appendChild(detailsSection);
    
    // Delivery & Shipping Section (single unified section)
    const deliverySection = createDetailSection('Shipping & Delivery');
    const deliveryGrid = document.createElement('div');
    deliveryGrid.className = 'detail-grid';
    
    // Determine best delivery date to show (avoid duplicates)
    let deliveryDate = null;
    if (item.product_delivery_info && typeof item.product_delivery_info === 'object') {
        deliveryDate = item.product_delivery_info.minDelivery;
    } else if (item.min_delivery_date) {
        deliveryDate = item.min_delivery_date;
    }
    
    if (deliveryDate) {
        const datesDiv = document.createElement('div');
        datesDiv.className = 'detail-item';
        const formattedDate = formatDeliveryDate(deliveryDate);
        datesDiv.innerHTML = `<strong>📅 Estimated Arrival:</strong><span>${formattedDate}</span>`;
        deliveryGrid.appendChild(datesDiv);
    }
    
    // Show max delivery date if different from min
    if (item.product_delivery_info && typeof item.product_delivery_info === 'object') {
        const maxDelivery = item.product_delivery_info.maxDelivery;
        if (maxDelivery && maxDelivery !== deliveryDate) {
            const maxDiv = document.createElement('div');
            maxDiv.className = 'detail-item';
            const formattedMax = formatDeliveryDate(maxDelivery);
            maxDiv.innerHTML = `<strong>📅 Latest Arrival:</strong><span>${formattedMax}</span>`;
            deliveryGrid.appendChild(maxDiv);
        }
    }
    
    // Shipping cost info (if Prime shows free, otherwise check raw delivery string)
    if (item.is_prime) {
        const shippingDiv = document.createElement('div');
        shippingDiv.className = 'detail-item';
        shippingDiv.innerHTML = `<strong>🚚 Shipping:</strong><span>FREE (Prime)</span>`;
        deliveryGrid.appendChild(shippingDiv);
    }
    
    if (deliveryGrid.children.length > 0) {
        deliverySection.appendChild(deliveryGrid);
        body.appendChild(deliverySection);
    }
    
    // View on Amazon button
    const actionsSection = document.createElement('div');
    actionsSection.style.marginTop = '20px';
    actionsSection.style.textAlign = 'center';
    
    const viewBtn = document.createElement('button');
    viewBtn.className = 'btn btn-link';
    viewBtn.textContent = '🔗 View on Amazon';
    viewBtn.style.padding = '12px 24px';
    viewBtn.onclick = () => window.open(item.url || item.product_url, '_blank');
    actionsSection.appendChild(viewBtn);
    body.appendChild(actionsSection);
    
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
