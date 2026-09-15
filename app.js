// ============================================================
// CONFIG
// ============================================================
const API = "http://127.0.0.1:8001";  // Same origin — koi URL nahi chahiye
const TOKEN_KEY = "expense_tracker_token";
let analyticsChartInstance = null;


// ============================================================
// HELPERS
// ============================================================
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`,
    };
}

function showMessage(el, text, type = "error") {
    el.textContent = text;
    el.className = "form-message " + type;
    setTimeout(() => {
        el.textContent = "";
        el.className = "form-message";
    }, 4000);
}

async function apiCall(url, options = {}) {
    const res = await fetch(API + url, options);
    if (res.status === 401) {
        // Token invalid/expired
        clearToken();
        showAuthPage();
        throw new Error("Session expired. Please login again.");
    }
    return res;
}


// ============================================================
// PAGE SWITCHING (Auth vs Dashboard)
// ============================================================
function showAuthPage() {
    document.getElementById("authPage").style.display = "flex";
    document.getElementById("dashboardPage").style.display = "none";
}

function showDashboardPage() {
    document.getElementById("authPage").style.display = "none";
    document.getElementById("dashboardPage").style.display = "flex";
    loadUserInfo();
    loadAllData();
}


// ============================================================
// INIT
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    const token = getToken();
    if (token) {
        showDashboardPage();
    } else {
        showAuthPage();
    }
    setupAuthTabs();
    setupAuthForms();
    setupSidebar();
    setupLogout();
    setupForms();
    setupReports();
});


// ============================================================
// AUTH TABS (Login / Register)
// ============================================================
function setupAuthTabs() {
    document.querySelectorAll(".auth-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            const target = tab.dataset.tab;
            document.querySelectorAll(".auth-tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(target + "Form").classList.add("active");
        });
    });
}


// ============================================================
// AUTH FORMS
// ============================================================
function setupAuthForms() {
    // LOGIN
    document.getElementById("loginForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = document.getElementById("loginMessage");
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;

        try {
            const res = await fetch("/auth/login-json", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();

            if (!res.ok) {
                showMessage(msg, data.detail || "Login failed");
                return;
            }

            setToken(data.access_token);
            showMessage(msg, "Login successful!", "success");
            setTimeout(() => showDashboardPage(), 400);
        } catch (err) {
            showMessage(msg, "Network error. Is server running?");
        }
    });

    // REGISTER
    document.getElementById("registerForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = document.getElementById("registerMessage");
        const email = document.getElementById("registerEmail").value.trim();
        const password = document.getElementById("registerPassword").value;

        try {
            const res = await fetch("/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();

            if (!res.ok) {
                showMessage(msg, data.detail || "Registration failed");
                return;
            }

            showMessage(msg, "Registered! Please login.", "success");
            // Switch to login tab
            setTimeout(() => {
                document.querySelector('[data-tab="login"]').click();
                document.getElementById("loginEmail").value = email;
                document.getElementById("loginPassword").value = "";
            }, 800);
        } catch (err) {
            showMessage(msg, "Network error. Is server running?");
        }
    });
}


// ============================================================
// SIDEBAR NAV
// ============================================================
function setupSidebar() {
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const section = item.dataset.section;

            document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
            item.classList.add("active");

            document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
            document.getElementById("section-" + section).classList.add("active");

            const titles = {
                dashboard: "Dashboard",
                expenses: "Expenses",
                incomes: "Incomes",
                budgets: "Budgets",
                reports: "Reports",
                analytics: "Analytics",
            };
            document.getElementById("pageTitle").textContent = titles[section] || "Dashboard";

            // Reload data when entering sections
            if (section === "analytics") loadAnalytics();
        });
    });
}


// ============================================================
// LOGOUT
// ============================================================
function setupLogout() {
    document.getElementById("logoutBtn").addEventListener("click", () => {
        clearToken();
        showAuthPage();
        // Clear forms
        document.getElementById("loginForm").reset();
        document.getElementById("registerForm").reset();
    });
}


// ============================================================
// LOAD USER INFO
// ============================================================
async function loadUserInfo() {
    try {
        const res = await apiCall("/auth/me", { headers: authHeaders() });
        if (res.ok) {
            const user = await res.json();
            document.getElementById("userEmail").textContent = user.email;
        }
    } catch (err) {
        console.error("Failed to load user info", err);
    }
}


// ============================================================
// LOAD ALL DATA
// ============================================================
async function loadAllData() {
    await Promise.all([
        loadSummary(),
        loadExpenses(),
        loadIncomes(),
        loadBudgets(),
    ]);
}


// ============================================================
// SUMMARY (Dashboard)
// ============================================================
async function loadSummary() {
    try {
        const res = await apiCall("/analytics/summary", { headers: authHeaders() });
        if (!res.ok) return;

        const data = await res.json();
        document.getElementById("statSpent").textContent = "$" + data.total_spent.toFixed(2);
        document.getElementById("statIncome").textContent = "$" + data.total_income.toFixed(2);
        document.getElementById("statBalance").textContent = "$" + data.balance.toFixed(2);
        document.getElementById("statCount").textContent = data.total_count;
    } catch (err) {
        console.error(err);
    }
}


// ============================================================
// EXPENSES
// ============================================================
async function loadExpenses() {
    try {
        const res = await apiCall("/expenses/", { headers: authHeaders() });
        if (!res.ok) return;
        const expenses = await res.json();

        // All expenses table
        const tbody = document.getElementById("expensesBody");
        if (expenses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty">No expenses yet</td></tr>';
        } else {
            tbody.innerHTML = expenses.map(e => `
                <tr>
                    <td>${e.id}</td>
                    <td>${escapeHtml(e.title)}</td>
                    <td>${escapeHtml(e.category)}</td>
                    <td>$${parseFloat(e.amount).toFixed(2)}</td>
                    <td>${e.date}</td>
                    <td>${escapeHtml(e.note || "")}</td>
                    <td><button class="btn-delete" onclick="deleteExpense(${e.id})">Delete</button></td>
                </tr>
            `).join("");
        }

        // Recent expenses (dashboard)
        const recentBody = document.getElementById("recentExpensesBody");
        const recent = expenses.slice(0, 5);
        if (recent.length === 0) {
            recentBody.innerHTML = '<tr><td colspan="4" class="empty">No expenses yet</td></tr>';
        } else {
            recentBody.innerHTML = recent.map(e => `
                <tr>
                    <td>${escapeHtml(e.title)}</td>
                    <td>${escapeHtml(e.category)}</td>
                    <td>$${parseFloat(e.amount).toFixed(2)}</td>
                    <td>${e.date}</td>
                </tr>
            `).join("");
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteExpense(id) {
    if (!confirm("Delete this expense?")) return;
    try {
        const res = await apiCall(`/expenses/${id}`, {
            method: "DELETE",
            headers: authHeaders(),
        });
        if (res.ok) {
            await loadAllData();
        }
    } catch (err) {
        console.error(err);
    }
}

// ============================================================
// INCOMES
// ============================================================
async function loadIncomes() {
    try {
        const res = await apiCall("/incomes/", { headers: authHeaders() });
        if (!res.ok) return;
        const incomes = await res.json();

        const tbody = document.getElementById("incomesBody");
        if (incomes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty">No incomes yet</td></tr>';
        } else {
            tbody.innerHTML = incomes.map(i => `
                <tr>
                    <td>${i.id}</td>
                    <td>${escapeHtml(i.source)}</td>
                    <td>$${parseFloat(i.amount).toFixed(2)}</td>
                    <td>${i.date}</td>
                    <td>${escapeHtml(i.note || "")}</td>
                    <td><button class="btn-delete" onclick="deleteIncome(${i.id})">Delete</button></td>
                </tr>
            `).join("");
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteIncome(id) {
    if (!confirm("Delete this income?")) return;
    try {
        const res = await apiCall(`/incomes/${id}`, {
            method: "DELETE",
            headers: authHeaders(),
        });
        if (res.ok) await loadAllData();
    } catch (err) {
        console.error(err);
    }
}


// ============================================================
// BUDGETS
// ============================================================
async function loadBudgets() {
    try {
        const res = await apiCall("/budgets/", { headers: authHeaders() });
        if (!res.ok) return;
        const budgets = await res.json();

        const tbody = document.getElementById("budgetsBody");
        if (budgets.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty">No budgets set</td></tr>';
        } else {
            tbody.innerHTML = budgets.map(b => `
                <tr>
                    <td>${b.id}</td>
                    <td>${escapeHtml(b.category)}</td>
                    <td>$${parseFloat(b.monthly_limit).toFixed(2)}</td>
                    <td><button class="btn-delete" onclick="deleteBudget(${b.id})">Delete</button></td>
                </tr>
            `).join("");
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteBudget(id) {
    if (!confirm("Delete this budget?")) return;
    try {
        const res = await apiCall(`/budgets/${id}`, {
            method: "DELETE",
            headers: authHeaders(),
        });
        if (res.ok) await loadAllData();
    } catch (err) {
        console.error(err);
    }
}


// ============================================================
// FORMS (Add Expense / Income / Budget)
// ============================================================
function setupForms() {
    // ADD EXPENSE
    document.getElementById("expenseForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = document.getElementById("expenseMsg");
        const payload = {
            title: document.getElementById("expTitle").value.trim(),
            amount: parseFloat(document.getElementById("expAmount").value),
            category: document.getElementById("expCategory").value.trim(),
            date: document.getElementById("expDate").value,
            note: document.getElementById("expNote").value.trim() || null,
        };

        try {
            const res = await apiCall("/expenses/", {
                method: "POST",
                headers: authHeaders(),
                body: JSON.stringify(payload),
            });
            const data = await res.json();

            if (!res.ok) {
                showMessage(msg, data.detail?.[0]?.msg || data.detail || "Failed to add expense");
                return;
            }

            showMessage(msg, "Expense added!", "success");
            e.target.reset();
            await loadAllData();
        } catch (err) {
            showMessage(msg, err.message || "Error");
        }
    });

    // ADD INCOME
    document.getElementById("incomeForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = document.getElementById("incomeMsg");
        const payload = {
            source: document.getElementById("incSource").value.trim(),
            amount: parseFloat(document.getElementById("incAmount").value),
            date: document.getElementById("incDate").value,
            note: document.getElementById("incNote").value.trim() || null,
        };

        try {
            const res = await apiCall("/incomes/", {
                method: "POST",
                headers: authHeaders(),
                body: JSON.stringify(payload),
            });
            const data = await res.json();

            if (!res.ok) {
                showMessage(msg, data.detail?.[0]?.msg || data.detail || "Failed to add income");
                return;
            }

            showMessage(msg, "Income added!", "success");
            e.target.reset();
            await loadAllData();
        } catch (err) {
            showMessage(msg, err.message || "Error");
        }
    });

    // ADD BUDGET
    document.getElementById("budgetForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = document.getElementById("budgetMsg");
        const payload = {
            category: document.getElementById("budCategory").value.trim(),
            monthly_limit: parseFloat(document.getElementById("budLimit").value),
        };

        try {
            const res = await apiCall("/budgets/", {
                method: "POST",
                headers: authHeaders(),
                body: JSON.stringify(payload),
            });
            const data = await res.json();

            if (!res.ok) {
                showMessage(msg, data.detail?.[0]?.msg || data.detail || "Failed to save budget");
                return;
            }

            showMessage(msg, "Budget saved!", "success");
            e.target.reset();
            await loadAllData();
        } catch (err) {
            showMessage(msg, err.message || "Error");
        }
    });

    // Set today's date as default in date inputs
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("expDate").value = today;
    document.getElementById("incDate").value = today;
}


// ============================================================
// REPORTS (PDF / Excel)
// ============================================================
function setupReports() {
    document.getElementById("downloadPdfBtn").addEventListener("click", () => downloadReport("pdf"));
    document.getElementById("downloadExcelBtn").addEventListener("click", () => downloadReport("excel"));
}

async function downloadReport(type) {
    const msg = document.getElementById("reportMsg");
    try {
        const res = await apiCall(`/expenses/report/${type}`, { headers: authHeaders() });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            showMessage(msg, data.detail || "Download failed");
            return;
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = type === "pdf" ? "Expense_Report.pdf" : "Expense_Report.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        showMessage(msg, "Downloaded!", "success");
    } catch (err) {
        showMessage(msg, err.message || "Download failed");
    }
}


// ============================================================
// ANALYTICS (Chart.js)
// ============================================================
async function loadAnalytics() {
    try {
        const res = await apiCall("/analytics/summary", { headers: authHeaders() });
        if (!res.ok) return;
        const data = await res.json();

        // ---- Table ----
        const tbody = document.getElementById("analyticsBody");
        const entries = Object.entries(data.category_breakdown);
        if (entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="empty">No data yet</td></tr>';
        } else {
            tbody.innerHTML = entries.map(([cat, total]) => `
                <tr>
                    <td>${escapeHtml(cat)}</td>
                    <td>$${total.toFixed(2)}</td>
                </tr>
            `).join("");
        }

        // ---- Chart ----
        const canvas = document.getElementById("analyticsChart");

        // Destroy old chart
        if (analyticsChartInstance) {
            analyticsChartInstance.destroy();
            analyticsChartInstance = null;
        }

        if (entries.length === 0) return;

        // Force canvas size detect — thoda delay
        await new Promise(resolve => setTimeout(resolve, 100));

        analyticsChartInstance = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: entries.map(([cat]) => cat),
                datasets: [{
                    data: entries.map(([, total]) => total),
                    backgroundColor: [
                        "#6366f1", "#10b981", "#f59e0b", "#ef4444",
                        "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16",
                        "#f97316", "#14b8a6"
                    ],
                    borderWidth: 2,
                    borderColor: "#ffffff",
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "right",
                        labels: { padding: 16, font: { size: 13 } },
                    },
                },
            },
        });
    } catch (err) {
        console.error("Analytics error:", err);
    }
}


// ============================================================
// UTIL: Escape HTML
// ============================================================
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}