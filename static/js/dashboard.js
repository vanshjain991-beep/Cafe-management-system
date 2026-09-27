/**
 * COFFEE & LOVE — Staff & Admin Dashboard Live Real-time Polling & Actions
 */

let knownOrderIds = new Set();
let isInitialLoad = true;

// Web Audio API Ding for new incoming orders
function playNewOrderSound() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.1); // A5

    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.6);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.6);
  } catch (e) {
    // Audio might be blocked until user gesture, safe to ignore
  }
}

// Live polling for the Kanban Board
function startDashboardPolling() {
  const board = document.getElementById('kanbanBoard');
  if (!board) return;

  async function pollLiveOrders() {
    try {
      const res = await fetch('/api/orders/live');
      if (!res.ok) return;
      const data = await res.json();

      if (data.success) {
        updateKanbanView(data.orders);
        updateLiveStats();
      }
    } catch (err) {
      console.warn("Live dashboard poll failed:", err);
    }
  }

  // Poll every 6 seconds
  setInterval(pollLiveOrders, 6000);
}

// Live stats counter updater
async function updateLiveStats() {
  try {
    const res = await fetch('/api/stats/live');
    if (!res.ok) return;
    const stats = await res.json();

    if (stats.success) {
      const elNew = document.getElementById('statNewOrders');
      const elPrep = document.getElementById('statPreparingOrders');
      const elReady = document.getElementById('statReadyOrders');
      const elRev = document.getElementById('statTodayRevenue');
      const elComp = document.getElementById('statCompletedOrders');

      if (elNew) elNew.textContent = stats.new_count;
      if (elPrep) elPrep.textContent = stats.preparing_count;
      if (elReady) elReady.textContent = stats.ready_count;
      if (elRev) elRev.textContent = `₹${stats.today_revenue.toFixed(2)}`;
      if (elComp) elComp.textContent = stats.today_completed_count;
    }
  } catch (e) {}
}

// Render Order Card HTML
function createOrderCardHtml(order) {
  const itemsHtml = order.items.map(it => `
    <li>
      <span><span class="item-qty">${it.quantity}x</span> ${it.item_name}</span>
      <span>₹${it.line_total.toFixed(2)}</span>
    </li>
  `).join('');

  // Next status action buttons depending on current status
  let nextActionBtn = '';
  if (order.status === 'new') {
    nextActionBtn = `
      <button class="btn btn-sm btn-primary" onclick="quickUpdateStatus(${order.id}, 'accepted')">
        ✓ Accept
      </button>
    `;
  } else if (order.status === 'accepted') {
    nextActionBtn = `
      <button class="btn btn-sm btn-primary" onclick="quickUpdateStatus(${order.id}, 'preparing')">
        ☕ Prepare
      </button>
    `;
  } else if (order.status === 'preparing') {
    nextActionBtn = `
      <button class="btn btn-sm btn-success" onclick="quickUpdateStatus(${order.id}, 'ready')">
        🛎️ Ready
      </button>
    `;
  } else if (order.status === 'ready') {
    nextActionBtn = `
      <button class="btn btn-sm btn-primary" onclick="quickUpdateStatus(${order.id}, 'served')">
        🍽️ Serve
      </button>
    `;
  } else if (order.status === 'served') {
    nextActionBtn = `
      <button class="btn btn-sm btn-success" onclick="quickUpdateStatus(${order.id}, 'completed', true)">
        💰 Settle Bill
      </button>
    `;
  }

  return `
    <div class="order-card" id="orderCard_${order.id}">
      <div class="order-card-top">
        <span class="order-card-table">
          🪑 Table ${order.table_number || '?'}
        </span>
        <span class="order-card-time">${order.created_at.split(' ')[1]}</span>
      </div>
      <div class="order-card-customer">
        <strong>${order.order_number}</strong> • ${order.customer_name}
      </div>
      ${order.notes ? `<div style="font-size:11px; color:#fde68a; margin-bottom:6px;">⚠️ ${order.notes}</div>` : ''}
      <ul class="order-card-items">
        ${itemsHtml}
      </ul>
      <div class="order-card-footer">
        <span class="order-total-price">₹${order.total.toFixed(2)}</span>
        <div class="order-actions">
          ${nextActionBtn}
          <a href="/dashboard/order/${order.id}" class="btn btn-sm btn-outline">Detail</a>
        </div>
      </div>
    </div>
  `;
}

// Update the Kanban Columns
function updateKanbanView(orders) {
  const buckets = {
    'new': document.getElementById('colBody_new'),
    'accepted': document.getElementById('colBody_accepted'),
    'preparing': document.getElementById('colBody_preparing'),
    'ready': document.getElementById('colBody_ready'),
    'served': document.getElementById('colBody_served')
  };

  if (!buckets['new']) return;

  // Check for any newly arrived orders
  let hasNewIncoming = false;
  orders.forEach(o => {
    if (!knownOrderIds.has(o.id)) {
      knownOrderIds.add(o.id);
      if (!isInitialLoad && o.status === 'new') {
        hasNewIncoming = true;
      }
    }
  });

  if (hasNewIncoming) {
    playNewOrderSound();
  }
  isInitialLoad = false;

  // Group orders
  const grouped = { 'new': [], 'accepted': [], 'preparing': [], 'ready': [], 'served': [] };
  orders.forEach(o => {
    if (grouped[o.status]) {
      grouped[o.status].push(o);
    }
  });

  // Render each column
  Object.keys(buckets).forEach(status => {
    const list = grouped[status];
    const colBody = buckets[status];
    const badgeCount = document.getElementById(`count_${status}`);

    if (badgeCount) badgeCount.textContent = list.length;

    if (list.length === 0) {
      colBody.innerHTML = `<div style="text-align:center; padding:20px; font-size:12px; color:var(--text-muted);">No orders</div>`;
    } else {
      colBody.innerHTML = list.map(o => createOrderCardHtml(o)).join('');
    }
  });
}

// Quick status change via AJAX
async function quickUpdateStatus(orderId, newStatus, markPaid = false) {
  const formData = new FormData();
  formData.append('status', newStatus);
  if (markPaid) {
    formData.append('mark_paid', 'yes');
  }

  try {
    const res = await fetch(`/dashboard/order/${orderId}/update-status`, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: formData
    });

    if (res.ok) {
      // Trigger instant poll to update cards immediately
      const ordersRes = await fetch('/api/orders/live');
      if (ordersRes.ok) {
        const data = await ordersRes.json();
        updateKanbanView(data.orders);
        updateLiveStats();
      }
    }
  } catch (err) {
    console.error("Failed to update status:", err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Populate initial known orders
  document.querySelectorAll('.order-card').forEach(card => {
    const id = parseInt(card.id.replace('orderCard_', ''));
    if (!isNaN(id)) knownOrderIds.add(id);
  });
  isInitialLoad = false;

  startDashboardPolling();
});
