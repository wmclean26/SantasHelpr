// Main search functionality
document.getElementById('searchBtn').addEventListener('click', performSearch);

// Allow Enter key in product input
document.getElementById('product').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

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
            const ebayCount = data.ebay.count;
            const amazonCount = data.amazon.count;
            let statusMsg = `Found ${ebayCount} eBay items, ${amazonCount} Amazon items`;
            
            if (data.amazon.error && ebayCount > 0) {
                statusMsg += ' (Amazon error - see below)';
            }
            
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
    
    // Display eBay results
    if (data.ebay.items.length > 0) {
        const ebaySection = createResultSection('eBay', data.ebay.items, false);
        results.appendChild(ebaySection);
    }
    
    // Display Amazon results or error
    if (data.amazon.items.length > 0) {
        const amazonSection = createResultSection('Amazon', data.amazon.items, true);
        results.appendChild(amazonSection);
    } else if (data.amazon.error) {
        const errorBox = document.createElement('div');
        errorBox.className = 'error-box';
        errorBox.innerHTML = `
            <h3>⚠️ Amazon API Error</h3>
            <p>${data.amazon.error}</p>
        `;
        results.appendChild(errorBox);
    }
    
    if (data.ebay.items.length === 0 && data.amazon.items.length === 0) {
        results.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">No results found. Try adjusting your filters.</p>';
    }
}

function createResultSection(source, items, isAmazon) {
    const section = document.createElement('div');
    section.className = 'result-group';
    
    const header = document.createElement('div');
    header.className = `result-header ${isAmazon ? 'amazon' : ''}`;
    header.textContent = `${source} Results (${items.length} items)`;
    section.appendChild(header);
    
    items.forEach((item, index) => {
        const card = isAmazon ? createAmazonCard(item, index) : createEbayCard(item, index);
        section.appendChild(card);
    });
    
    return section;
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
    
    // Price
    const price = document.createElement('div');
    price.className = 'item-price';
    price.textContent = `$${item.product_price || 'N/A'}`;
    
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

// Modal functionality
function showEbayDetails(item) {
    const modal = createModal('eBay Item Details');
    const body = modal.querySelector('.modal-body');
    
    // Title
    const title = document.createElement('h2');
    title.textContent = item.title || 'N/A';
    title.style.marginBottom = '20px';
    body.appendChild(title);
    
    // Images
    if (item.images && item.images.length > 0) {
        const section = createDetailSection('Images', `${item.images.filter(i => i).length} available`);
        const imgContainer = document.createElement('div');
        imgContainer.className = 'detail-images';
        item.images.slice(0, 5).forEach(imgUrl => {
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
    
    // Current Price
    const currentPriceDiv = document.createElement('div');
    currentPriceDiv.className = 'detail-item';
    currentPriceDiv.innerHTML = `<strong>Current Price:</strong><span>${item.price || 'N/A'}</span>`;
    priceGrid.appendChild(currentPriceDiv);
    
    // Original Price & Discount
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
