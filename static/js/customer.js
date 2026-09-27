/**
 * COFFEE & LOVE — Customer Ordering & Live Tracking JS
 */

const CART_KEY = 'coffee_and_love_cart';

// Get Cart from LocalStorage
function getCart() {
  try {
    const data = localStorage.getItem(CART_KEY);
    return data ? JSON.parse(data) : [];
  } catch (e) {
    return [];
  }
}

// Save Cart to LocalStorage
function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartBadge();
}

// Update Cart Floating Badge
function updateCartBadge() {
  const cart = getCart();
  const totalCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  
  const badges = document.querySelectorAll('.cart-badge-count');
  badges.forEach(b => {
    b.textContent = totalCount;
  });

  const floatBtn = document.getElementById('cartFloatingBtn');
  if (floatBtn) {
    floatBtn.style.display = totalCount > 0 ? 'flex' : 'none';
  }
}

// Add item to Cart
function addToCart(id, name, price) {
  let cart = getCart();
  const existing = cart.find(i => i.id === id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({ id: id, name: name, price: parseFloat(price), quantity: 1 });
  }
  saveCart(cart);
  showToast(`Added ${name} to cart`);
  
  // Update in-card button if on menu page
  updateItemCardControls(id);
}

// Remove or Decrement item
function removeFromCart(id) {
  let cart = getCart();
  const existing = cart.find(i => i.id === id);
  if (existing) {
    existing.quantity -= 1;
    if (existing.quantity <= 0) {
      cart = cart.filter(i => i.id !== id);
    }
  }
  saveCart(cart);
  updateItemCardControls(id);
  
  // If on cart page, re-render
  if (document.getElementById('cartItemsContainer')) {
    renderCartPage();
  }
}

// Update menu card counter
function updateItemCardControls(id) {
  const cart = getCart();
  const item = cart.find(i => i.id === id);
  const qty = item ? item.quantity : 0;
  
  const display = document.getElementById(`qtyDisplay_${id}`);
  const addBtn = document.getElementById(`addBtn_${id}`);
  const counterGroup = document.getElementById(`counterGroup_${id}`);
  
  if (display) display.textContent = qty;
  
  if (addBtn && counterGroup) {
    if (qty > 0) {
      addBtn.style.display = 'none';
      counterGroup.style.display = 'inline-flex';
    } else {
      addBtn.style.display = 'inline-flex';
      counterGroup.style.display = 'none';
    }
  }
}

// Sync all menu cards on page load
function syncMenuCards() {
  const cart = getCart();
  cart.forEach(item => {
    updateItemCardControls(item.id);
  });
  updateCartBadge();
}

// Filter menu items by Category
function filterCategory(catId, btnElement) {
  document.querySelectorAll('.category-pill').forEach(b => b.classList.remove('active'));
  if (btnElement) btnElement.classList.add('active');

  const cards = document.querySelectorAll('.menu-card');
  cards.forEach(card => {
    const cardCat = card.getAttribute('data-category-id');
    if (catId === 'all' || cardCat === catId) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

// Search menu items
function handleSearch(query) {
  const term = query.toLowerCase().trim();
  const cards = document.querySelectorAll('.menu-card');
  
  cards.forEach(card => {
    const name = (card.getAttribute('data-name') || '').toLowerCase();
    const desc = (card.getAttribute('data-desc') || '').toLowerCase();
    if (name.includes(term) || desc.includes(term)) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

// Render Cart Page
function renderCartPage() {
  const container = document.getElementById('cartItemsContainer');
  const emptyView = document.getElementById('cartEmptyView');
  const layout = document.getElementById('cartLayout');
  
  if (!container) return;

  const cart = getCart();
  if (cart.length === 0) {
    if (emptyView) emptyView.style.display = 'block';
    if (layout) layout.style.display = 'none';
    return;
  }

  if (emptyView) emptyView.style.display = 'none';
  if (layout) layout.style.display = 'grid';

  let subtotal = 0;
  let html = '';

  cart.forEach(item => {
    const lineTotal = item.price * item.quantity;
    subtotal += lineTotal;
    html += `
      <div class="cart-item-row">
        <div class="cart-item-info">
          <h4>${item.name}</h4>
          <p>₹${item.price.toFixed(2)} each</p>
        </div>
        <div class="item-qty-control">
          <button class="qty-btn" onclick="removeFromCart(${item.id})">-</button>
          <span class="qty-display">${item.quantity}</span>
          <button class="qty-btn" onclick="addToCart(${item.id}, '${item.name}', ${item.price})">+</button>
        </div>
        <div class="cart-item-total">₹${lineTotal.toFixed(2)}</div>
      </div>
    `;
  });

  container.innerHTML = html;

  const tax = subtotal * 0.05;
  const total = subtotal + tax;

  const elSubtotal = document.getElementById('billSubtotal');
  const elTax = document.getElementById('billTax');
  const elTotal = document.getElementById('billTotal');

  if (elSubtotal) elSubtotal.textContent = `₹${subtotal.toFixed(2)}`;
  if (elTax) elTax.textContent = `₹${tax.toFixed(2)}`;
  if (elTotal) elTotal.textContent = `₹${total.toFixed(2)}`;
}

// Submit Order
async function submitOrder(event) {
  event.preventDefault();
  const cart = getCart();
  if (cart.length === 0) {
    alert("Your cart is empty!");
    return;
  }

  const tableInput = document.getElementById('orderTableNumber');
  const nameInput = document.getElementById('orderCustomerName');
  const notesInput = document.getElementById('orderNotes');
  const submitBtn = document.getElementById('btnSubmitOrder');

  const tableNumber = tableInput ? tableInput.value : '';
  const customerName = nameInput ? nameInput.value : 'Guest';
  const notes = notesInput ? notesInput.value : '';

  if (!tableNumber) {
    alert("Please select or specify your Table Number!");
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Placing Order...";
  }

  try {
    const res = await fetch('/order/place', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        table_number: tableNumber,
        customer_name: customerName,
        notes: notes,
        items: cart
      })
    });

    const data = await res.json();
    if (data.success) {
      // Clear Cart
      localStorage.removeItem(CART_KEY);
      // Redirect to tracking page
      window.location.href = data.redirect_url;
    } else {
      alert(data.error || "Failed to place order.");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Confirm & Place Order";
      }
    }
  } catch (err) {
    console.error(err);
    alert("An error occurred while placing your order. Please try again.");
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Confirm & Place Order";
    }
  }
}

// Live Order Status Polling (Customer Tracking Page)
function startOrderStatusPolling(orderNumber) {
  const statusStepMap = {
    'new': 0,
    'accepted': 1,
    'preparing': 2,
    'ready': 3,
    'served': 4,
    'completed': 5
  };

  const statusDescriptions = {
    'new': 'Your order has been received and is waiting for confirmation from our staff.',
    'accepted': 'Your order has been accepted! Sending details to our barista and kitchen.',
    'preparing': 'Our baristas and chefs are preparing your delicious food and coffee!',
    'ready': 'Your order is ready! Staff is bringing it over to your table.',
    'served': 'Served at your table. Enjoy your meal with COFFEE & LOVE! ☕❤️',
    'completed': 'Order completed. Thank you for visiting COFFEE & LOVE!'
  };

  const statusIcons = {
    'new': '📝',
    'accepted': '👍',
    'preparing': '☕',
    'ready': '🛎️',
    'served': '🍽️',
    'completed': '✨'
  };

  async function poll() {
    try {
      const res = await fetch(`/api/order/${orderNumber}/status`);
      if (!res.ok) return;
      const data = await res.json();

      if (data.found) {
        const curStatus = data.status;
        const curIndex = statusStepMap[curStatus] !== undefined ? statusStepMap[curStatus] : 0;

        // Update badge
        const badge = document.getElementById('liveStatusBadge');
        if (badge) {
          badge.className = `status-badge status-${curStatus}`;
          badge.textContent = curStatus.toUpperCase();
        }

        // Update icon
        const iconEl = document.getElementById('liveStatusIcon');
        if (iconEl && statusIcons[curStatus]) {
          iconEl.textContent = statusIcons[curStatus];
        }

        // Update description
        const descEl = document.getElementById('liveStatusDesc');
        if (descEl && statusDescriptions[curStatus]) {
          descEl.textContent = statusDescriptions[curStatus];
        }

        // Update Stepper
        document.querySelectorAll('.step-item').forEach((stepEl, idx) => {
          stepEl.classList.remove('active', 'completed');
          if (idx < curIndex) {
            stepEl.classList.add('completed');
          } else if (idx === curIndex) {
            stepEl.classList.add('active');
          }
        });

        const progressBar = document.getElementById('stepperProgress');
        if (progressBar) {
          const pct = (curIndex / 5) * 100;
          progressBar.style.width = `${pct}%`;
        }

        // If completed, update payment notice
        if (curStatus === 'completed') {
          const payBanner = document.getElementById('paymentStatusNotice');
          if (payBanner) {
            payBanner.innerHTML = '<strong>✅ Settled:</strong> Bill has been paid at the counter. Have a wonderful day!';
            payBanner.style.background = 'rgba(34, 197, 94, 0.15)';
            payBanner.style.color = '#86efac';
            payBanner.style.borderColor = '#22c55e';
          }
        }
      }
    } catch (e) {
      console.warn("Polling error:", e);
    }
  }

  // Poll immediately and then every 5 seconds
  poll();
  setInterval(poll, 5000);
}

// Simple Toast Notification
function showToast(message) {
  let toast = document.getElementById('globalToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'globalToast';
    toast.style.cssText = `
      position: fixed;
      bottom: 90px;
      right: 24px;
      background: var(--bg-card);
      color: var(--gold-light);
      border: 1px solid var(--border-active);
      padding: 12px 20px;
      border-radius: var(--radius-full);
      box-shadow: 0 10px 30px rgba(0,0,0,0.6);
      font-size: 13px;
      font-weight: 600;
      z-index: 10000;
      transition: opacity 0.3s ease, transform 0.3s ease;
      opacity: 0;
      transform: translateY(10px);
    `;
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
  }, 2200);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  syncMenuCards();
  if (document.getElementById('cartItemsContainer')) {
    renderCartPage();
  }
});
