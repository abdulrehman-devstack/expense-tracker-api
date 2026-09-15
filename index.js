const API_BASE_URL = 'https://expense-tracker-api-production-dcf5.up.railway.app/';

let currentUserData = null;

try {
    const storedUser = localStorage.getItem('pro_current_user');
    currentUserData = storedUser ? JSON.parse(storedUser) : null;
} catch (e) {
    console.error("User storage parsing error:", e);
}

function getActiveUserId() {
    try {
        const stored = localStorage.getItem('pro_current_user');
        if (!stored) return 0;
        const u = JSON.parse(stored);
        // Supports JWT Token response and User ID extraction
        return u && (u.id || u.user_id) ? Number(u.id || u.user_id) : (u.access_token ? decodeUserIdFromToken(u.access_token) : 0);
    } catch (e) {
        return 0;
    }
}

// Fallback Helper for JWT Tokens
function decodeUserIdFromToken(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return Number(payload.sub || payload.user_id || payload.id || 0);
    } catch (e) {
        return 0;
    }
}

let isSignUpMode = false;
let currentUser = currentUserData || null;
let myChart = null;
let editModalInstance = null;
let editBudgetModalInstance = null;
let allTransactions = [];
let allBudgets = [];

window.onload = function () {
    checkAuthState();

    const editEl = document.getElementById('editModal');
    const editBudgetEl = document.getElementById('editBudgetModal');

    if (editEl) editModalInstance = new bootstrap.Modal(editEl);
    if (editBudgetEl) editBudgetModalInstance = new bootstrap.Modal(editBudgetEl);

    const entryDateEl = document.getElementById('entryDate');
    const budgetMonthEl = document.getElementById('budgetMonth');

    if (entryDateEl) entryDateEl.valueAsDate = new Date();
    if (budgetMonthEl) budgetMonthEl.value = new Date().toISOString().slice(0, 7);
};

function checkAuthState() {
    const authSection = document.getElementById('authSection');
    const dashboardSection = document.getElementById('dashboardSection');
    const navUserInfo = document.getElementById('navUserInfo');

    const activeId = getActiveUserId();

    if (currentUser && activeId !== 0) {
        if (authSection) authSection.classList.add('d-none');
        if (dashboardSection) dashboardSection.classList.remove('d-none');
        if (navUserInfo) navUserInfo.style.display = 'flex';

        const displayUserEl = document.getElementById('displayUsername');
        if (displayUserEl) {
            displayUserEl.innerText = `👤 ${currentUser.email || currentUser.name || 'User'}`;
        }
        loadDashboard();
        updatePrintHeader();
    } else {
        if (authSection) authSection.classList.remove('d-none');
        if (dashboardSection) dashboardSection.classList.add('d-none');
        if (navUserInfo) navUserInfo.style.display = 'none';
    }
}

function toggleAuthMode(e) {
    if (e) e.preventDefault();
    isSignUpMode = !isSignUpMode;
    const alertBox = document.getElementById('authAlert');
    if (alertBox) alertBox.classList.add('d-none');

    if (isSignUpMode) {
        document.getElementById('authTitle').innerText = "Create Account";
        document.getElementById('authSubtitle').innerText = "Sign up to track your finances securely";
        document.getElementById('nameFieldGroup').style.display = 'block';
        document.getElementById('authSubmitBtn').innerText = "Sign Up";
        document.getElementById('authToggleText').innerHTML = `Already have an account? <a href="#" onclick="toggleAuthMode(event)" class="text-primary fw-semibold text-decoration-none">Sign In</a>`;
    } else {
        document.getElementById('authTitle').innerText = "Welcome Back";
        document.getElementById('authSubtitle').innerText = "Please enter your details to sign in";
        document.getElementById('nameFieldGroup').style.display = 'none';
        document.getElementById('authSubmitBtn').innerText = "Sign In";
        document.getElementById('authToggleText').innerHTML = `Don't have an account? <a href="#" onclick="toggleAuthMode(event)" class="text-danger fw-semibold text-decoration-none">Sign Up</a>`;
    }
}

// Complete Auth Handler Fix (yahan `yourData` error fix kar diya gaya hai)
document.getElementById('authForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value.trim();
    const alertBox = document.getElementById('authAlert');
    if (alertBox) alertBox.classList.add('d-none');

    try {
        let userObj = null;
        if (isSignUpMode) {
            const nameField = document.getElementById('authName');
            const name = nameField ? nameField.value.trim() : '';

            const res = await fetch(`${API_BASE_URL}auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, name })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Registration failed");
            userObj = data;
            showToast("🎉 Account created successfully! Please sign in.", "success");
            toggleAuthMode();
            return; // Sign up ke baad user ko sign in karne dein
        } else {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            // Yeh route 'auth/token' hona chahiye
            const res = await fetch(`${API_BASE_URL}auth/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Invalid email or password!");

            // Extract JWT or User Details safely
            userObj = data.user ? { ...data.user, access_token: data.access_token } : { email, access_token: data.access_token, id: data.id || 1 };
            showToast("🔑 Logged in successfully!", "success");
        }

        currentUser = userObj;
        localStorage.setItem('pro_current_user', JSON.stringify(currentUser));
        document.getElementById('authForm').reset();
        checkAuthState();

    } catch (err) {
        console.error("Auth error:", err);
        if (alertBox) {
            alertBox.innerText = err.message;
            alertBox.classList.remove('d-none');
        }
    }
});

function logout() {
    localStorage.removeItem('pro_current_user');
    currentUser = null;
    checkAuthState();
}

async function loadDashboard() {
    await Promise.all([loadTransactions(), loadBudgets()]);
    renderData(allTransactions);
    renderBudgets(allBudgets);
}

async function loadTransactions() {
    const activeUserId = getActiveUserId();
    if (!activeUserId) {
        allTransactions = [];
        return;
    }

    try {
        const [expRes, incRes] = await Promise.all([
            fetch(`${API_BASE_URL}expenses/?user_id=${activeUserId}`),
            fetch(`${API_BASE_URL}incomes/?user_id=${activeUserId}`)
        ]);

        if (!expRes.ok || !incRes.ok) throw new Error("Failed to retrieve records");

        const expenses = await expRes.json();
        const incomes = await incRes.json();

        allTransactions = [
            ...(Array.isArray(expenses) ? expenses.map(e => ({ ...e, type: 'expense' })) : []),
            ...(Array.isArray(incomes) ? incomes.map(i => ({ ...i, type: 'income' })) : [])
        ];
    } catch (err) {
        console.error("Load transactions error:", err);
        allTransactions = [];
    }
}

async function loadBudgets() {
    const activeUserId = getActiveUserId();
    if (!activeUserId) return;

    try {
        const res = await fetch(`${API_BASE_URL}budgets/?user_id=${activeUserId}`);
        if (res.ok) {
            const data = await res.json();
            allBudgets = Array.isArray(data) ? data : [];
        } else {
            allBudgets = [];
        }
    } catch (err) {
        console.error("Load budgets error:", err);
        allBudgets = [];
    }
}

function renderData(transactions) {
    const tbody = document.getElementById('transactionTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-4">No records found. Add your first entry!</td></tr>`;
        document.getElementById('totalBalance').innerText = "$0.00";
        document.getElementById('totalIncome').innerText = "$0.00";
        document.getElementById('totalExpense').innerText = "$0.00";
        updateChart({});
        return;
    }

    let totalBal = 0, totalInc = 0, totalExp = 0;
    let categoryMap = {};

    transactions.forEach((item, index) => {
        let amt = Number(item.amount) || 0;
        if (item.type === 'income') {
            totalInc += amt;
            totalBal += amt;
        } else {
            totalExp += amt;
            totalBal -= amt;
            const catKey = item.category || 'Uncategorized';
            categoryMap[catKey] = (categoryMap[catKey] || 0) + amt;
        }

        let badgeHtml = item.type === 'income'
            ? '<span class="badge bg-success-subtle text-success px-2 py-1 rounded-pill fw-semibold">Income</span>'
            : '<span class="badge bg-danger-subtle text-danger px-2 py-1 rounded-pill fw-semibold">Expense</span>';
        let amtColor = item.type === 'income' ? 'text-success' : 'text-danger';
        let sign = item.type === 'income' ? '+' : '-';
        let dateStr = item.date ? String(item.date).substring(0, 10) : 'N/A';

        tbody.innerHTML += `
        <tr>
            <td><span class="text-secondary small">${dateStr}</span></td>
            <td>${badgeHtml}</td>
            <td class="fw-semibold">${item.title || item.source || 'N/A'}</td>
            <td><span class="text-secondary small bg-light px-2 py-1 rounded">${item.category || 'General'}</span></td>
            <td class="${amtColor} fw-bold">${sign}$${amt.toFixed(2)}</td>
            <td class="no-print text-end">
                <button class="btn btn-sm btn-light text-warning border me-1" onclick="openEditModal(${index})" title="Edit">
                    <i class="fa-solid fa-pen-to-square"></i>
                </button>
                <button class="btn btn-sm btn-light text-danger border" onclick="deleteRecord(${index})" title="Delete">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </td>
        </tr>`;
    });

    document.getElementById('totalBalance').innerText = `$${totalBal.toFixed(2)}`;
    document.getElementById('totalIncome').innerText = `$${totalInc.toFixed(2)}`;
    document.getElementById('totalExpense').innerText = `$${totalExp.toFixed(2)}`;

    updateChart(categoryMap);
    updatePrintHeader();
}

function renderBudgets(budgets) {
    const container = document.getElementById('budgetSummaryContainer');
    if (!container) return;

    if (!Array.isArray(budgets) || budgets.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3 mb-0">No budgets set yet.</p>';
        return;
    }

    let html = '<div class="row g-3">';
    budgets.forEach((b, i) => {
        const cat = b.category || 'General';
        const limit = Number(b.monthly_limit || b.limit || 0);
        const month = b.month || '';

        let spent = 0;
        allTransactions.forEach(t => {
            if (t.type === 'expense' && (t.category || '').toLowerCase() === cat.toLowerCase()) {
                let tDate = t.date ? String(t.date).substring(0, 7) : '';
                if (!month || tDate === month) {
                    spent += Number(t.amount || 0);
                }
            }
        });

        let percent = limit > 0 ? Math.min((spent / limit) * 100, 100) : 0;
        let remaining = limit - spent;
        let barColor = percent >= 100 ? 'bg-danger' : (percent >= 75 ? 'bg-warning' : 'bg-success');

        html += `
        <div class="col-md-6">
            <div class="border rounded-3 p-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <h6 class="fw-bold m-0">${cat}</h6>
                        <small class="text-muted">${month || 'All time'}</small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-light text-warning border me-1" onclick="openEditBudgetModal(${i})" title="Edit budget">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button class="btn btn-sm btn-light text-danger border" onclick="deleteBudget(${i})" title="Delete budget">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </div>
                <div class="d-flex justify-content-between small mb-1">
                    <span class="text-secondary">Spent: $${spent.toFixed(2)}</span>
                    <span class="fw-semibold">Budget: $${limit.toFixed(2)}</span>
                </div>
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar ${barColor}" role="progressbar" style="width: ${percent}%"></div>
                </div>
                <small class="${remaining < 0 ? 'text-danger' : 'text-success'} fw-semibold mt-1 d-block">
                    ${remaining < 0 ? 'Over by $' + Math.abs(remaining).toFixed(2) : 'Remaining: $' + remaining.toFixed(2)}
                </small>
            </div>
        </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

function updateChart(categoryMap) {
    const chartEl = document.getElementById('expenseChart');
    if (!chartEl) return;
    const ctx = chartEl.getContext('2d');
    const labels = Object.keys(categoryMap);
    const data = Object.values(categoryMap);

    if (myChart) myChart.destroy();
    myChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.length > 0 ? labels : ['No Expenses'],
            datasets: [{
                data: data.length > 0 ? data : [1],
                backgroundColor: labels.length > 0 ? ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'] : ['#e5e7eb'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } } }
            },
            cutout: '65%'
        }
    });
}

function updatePrintHeader() {
    if (currentUser) {
        const printUser = document.getElementById('printUserInfo');
        const printDate = document.getElementById('printDate');
        if (printUser) printUser.innerText = `User: ${currentUser.name || currentUser.email}`;
        if (printDate) printDate.innerText = `Report Date: ${new Date().toLocaleString()}`;
    }
}

function checkBudgetExceeded(category) {
    const budget = allBudgets.find(b => (b.category || '').toLowerCase() === category.toLowerCase());
    if (!budget) return;
    const limit = Number(budget.monthly_limit || budget.limit || 0);
    let spent = 0;
    allTransactions.forEach(t => {
        if (t.type === 'expense' && (t.category || '').toLowerCase() === category.toLowerCase()) {
            spent += Number(t.amount || 0);
        }
    });
    if (spent > limit) {
        showToast(`🚨 Budget exceeded for "${category}" — Threshold reached!`, 'warning');
    }
}

document.getElementById('entryForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const activeUserId = getActiveUserId();

    if (!activeUserId) {
        showToast("⚠️ Please login again to refresh session!", "danger");
        return;
    }

    const type = document.getElementById('entryType').value;
    const titleOrSource = document.getElementById('entryTitle').value;
    const amount = parseFloat(document.getElementById('entryAmount').value);
    const category = document.getElementById('entryCategory').value;
    const date = document.getElementById('entryDate').value;

    const endpoint = type === 'income'
        ? `${API_BASE_URL}incomes/?user_id=${activeUserId}`
        : `${API_BASE_URL}expenses/?user_id=${activeUserId}`;

    const payload = type === 'income'
        ? { source: titleOrSource, amount, category, date, user_id: activeUserId }
        : { title: titleOrSource, amount, category, date, user_id: activeUserId };

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`Server error ${res.status}: ${errText}`);
        }

        showToast(`✅ ${type === 'income' ? 'Income' : 'Expense'} saved: ${titleOrSource}`, 'success');
        document.getElementById('entryForm').reset();
        document.getElementById('entryDate').valueAsDate = new Date();
        await loadDashboard();

        if (type === 'expense') checkBudgetExceeded(category);
    } catch (err) {
        console.error(err);
        showToast(`❌ ${err.message}`, 'danger');
    }
});

function openEditModal(index) {
    const item = allTransactions[index];
    if (!item || !editModalInstance) return;
    document.getElementById('editIndex').value = index;
    document.getElementById('editId').value = item.id || '';
    document.getElementById('editType').value = item.type;
    document.getElementById('editTitle').value = item.title || item.source || '';
    document.getElementById('editAmount').value = item.amount || 0;
    document.getElementById('editCategory').value = item.category || '';
    document.getElementById('editDate').value = item.date ? String(item.date).substring(0, 10) : '';
    editModalInstance.show();
}

async function saveEdit() {
    const activeUserId = getActiveUserId();
    const index = document.getElementById('editIndex').value;
    const original = allTransactions[index];
    if (!original || !activeUserId) return;

    const type = document.getElementById('editType').value;
    const id = document.getElementById('editId').value;
    const titleOrSourceVal = document.getElementById('editTitle').value;

    const payload = type === 'income'
        ? { source: titleOrSourceVal, amount: parseFloat(document.getElementById('editAmount').value), category: document.getElementById('editCategory').value, date: document.getElementById('editDate').value, user_id: activeUserId }
        : { title: titleOrSourceVal, amount: parseFloat(document.getElementById('editAmount').value), category: document.getElementById('editCategory').value, date: document.getElementById('editDate').value, user_id: activeUserId };

    const endpoint = type === 'income'
        ? `${API_BASE_URL}incomes/${id}?user_id=${activeUserId}`
        : `${API_BASE_URL}expenses/${id}?user_id=${activeUserId}`;

    try {
        const res = await fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`Update failed: ${res.status}`);
        showToast(`✅ Transaction updated`, 'success');
        if (editModalInstance) editModalInstance.hide();
        await loadDashboard();
    } catch (err) {
        console.error(err);
        showToast(`❌ ${err.message}`, 'danger');
    }
}

async function deleteRecord(index) {
    if (!confirm("Are you sure you want to delete this record?")) return;
    const item = allTransactions[index];
    if (!item || !item.id) {
        showToast(`❌ Record ID missing`, 'danger');
        return;
    }

    const endpoint = item.type === 'income'
        ? `${API_BASE_URL}incomes/${item.id}`
        : `${API_BASE_URL}expenses/${item.id}`;

    try {
        const res = await fetch(endpoint, { method: 'DELETE' });
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(`${res.status} - ${txt}`);
        }
        showToast(`🗑️ Record deleted`, 'success');
        await loadDashboard();
    } catch (err) {
        console.error("DELETE error:", err);
        showToast(`❌ ${err.message}`, 'danger');
    }
}

document.getElementById('budgetForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const activeUserId = getActiveUserId();
    if (!activeUserId) return;

    const category = document.getElementById('budgetCategory').value;
    const amount = parseFloat(document.getElementById('budgetAmount').value);
    const month = document.getElementById('budgetMonth').value;

    try {
        const res = await fetch(`${API_BASE_URL}budgets/?user_id=${activeUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, monthly_limit: amount, month, user_id: activeUserId })
        });
        if (!res.ok) throw new Error(`Budget save failed: ${res.status}`);
        showToast(`💰 Budget set: ${category} = $${amount}`, 'success');
        document.getElementById('budgetForm').reset();
        document.getElementById('budgetMonth').value = new Date().toISOString().slice(0, 7);
        await loadDashboard();
    } catch (err) {
        console.error(err);
        showToast(`❌ ${err.message}`, 'danger');
    }
});

function openEditBudgetModal(index) {
    const b = allBudgets[index];
    if (!b || !editBudgetModalInstance) return;
    document.getElementById('editBudgetId').value = b.id || '';
    document.getElementById('editBudgetCategory').value = b.category || '';
    document.getElementById('editBudgetAmount').value = b.monthly_limit || b.limit || 0;
    document.getElementById('editBudgetMonth').value = b.month || '';
    editBudgetModalInstance.show();
}

async function saveBudgetEdit() {
    const activeUserId = getActiveUserId();
    const budgetId = document.getElementById('editBudgetId').value;
    if (!activeUserId) return;

    const category = document.getElementById('editBudgetCategory').value;
    const amount = parseFloat(document.getElementById('editBudgetAmount').value);
    const month = document.getElementById('editBudgetMonth').value;

    const endpoint = budgetId ? `${API_BASE_URL}budgets/${budgetId}` : `${API_BASE_URL}budgets/?user_id=${activeUserId}`;
    const method = budgetId ? 'PUT' : 'POST';

    try {
        const res = await fetch(endpoint, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, monthly_limit: amount, month, user_id: activeUserId })
        });
        if (!res.ok) throw new Error(`Budget update failed: ${res.status}`);
        showToast(`✅ Budget updated`, 'success');
        if (editBudgetModalInstance) editBudgetModalInstance.hide();
        await loadDashboard();
    } catch (err) {
        console.error(err);
        showToast(`❌ ${err.message}`, 'danger');
    }
}

async function deleteBudget(index) {
    if (!confirm("Delete this budget?")) return;
    const b = allBudgets[index];
    if (!b || !b.id) return;

    try {
        const res = await fetch(`${API_BASE_URL}budgets/${b.id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
        showToast(`🗑️ Budget deleted`, 'success');
        await loadDashboard();
    } catch (err) {
        console.error(err);
        showToast(`❌ ${err.message}`, 'danger');
    }
}

function exportExcel() {
    const activeUserId = getActiveUserId();
    window.open(`${API_BASE_URL}expenses/report/excel?user_id=${activeUserId}`, '_blank');
    showToast(`📊 Excel download started`, 'success');
}

function exportPDF() {
    const activeUserId = getActiveUserId();
    window.open(`${API_BASE_URL}expenses/report/pdf?user_id=${activeUserId}`, '_blank');
    showToast(`📄 PDF download started`, 'success');
}

function showToast(message, type = 'info') {
    const toastEl = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastMessage');
    if (!toastEl || !toastBody) return;
    toastEl.className = `toast align-items-center border-0 text-white bg-${type}`;
    toastBody.innerText = message;
    new bootstrap.Toast(toastEl, { delay: 5000 }).show();
}