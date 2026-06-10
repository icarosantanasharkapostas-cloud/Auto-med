const API_URL = "/api";
let currentToken = localStorage.getItem("access_token");

// Verifica login
if (!currentToken && window.location.pathname === "/") {
    window.location.href = "/login";
}

function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
    };
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
}

// Intercepta erros 401
async function fetchAuth(url, options = {}) {
    options.headers = getHeaders();
    const res = await fetch(url, options);
    if (res.status === 401) {
        logout();
    }
    return res;
}

// ==========================================
// FUNÇÕES DE DASHBOARD
// ==========================================

async function loadStats() {
    try {
        const res = await fetchAuth(`${API_URL}/stats`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById('stat-total').innerText = data.total_clientes;
            document.getElementById('stat-ativos').innerText = data.clientes_ativos;
            document.getElementById('stat-salas').innerText = data.salas_criadas;
            document.getElementById('stat-pgtos').innerText = data.pagamentos_processados;
        }
    } catch(e) {
        console.error(e);
    }
}

async function loadClients() {
    try {
        const res = await fetchAuth(`${API_URL}/clients`);
        if (res.ok) {
            const clients = await res.json();
            const tbody = document.getElementById('clients-table-body');
            const logSelect = document.getElementById('log-client-filter');
            
            tbody.innerHTML = '';
            
            // Keep current selected log filter
            const currentSelectedLog = logSelect.value;
            logSelect.innerHTML = '<option value="">Selecione um cliente para ver os logs</option>';
            
            clients.forEach(c => {
                // Populate Table
                const tr = document.createElement('tr');
                const isOnline = c.ativo; // Em um caso ideal buscaríamos o status real também via /status
                
                tr.innerHTML = `
                    <td>${c.id}</td>
                    <td><strong>${c.nome}</strong></td>
                    <td>${c.email}</td>
                    <td>
                        <span class="badge bg-${isOnline ? 'success' : 'danger'}">
                            ${isOnline ? 'Online' : 'Offline'}
                        </span>
                    </td>
                    <td>
                        ${isOnline ? 
                            `<button class="btn btn-sm btn-outline-danger" onclick="toggleBot(${c.id}, 'stop')"><i class="fas fa-stop"></i> Parar</button>` : 
                            `<button class="btn btn-sm btn-outline-success" onclick="toggleBot(${c.id}, 'start')"><i class="fas fa-play"></i> Iniciar</button>`
                        }
                        <button class="btn btn-sm btn-outline-secondary ms-1" onclick="deleteClient(${c.id})"><i class="fas fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);

                // Populate Log Select
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.innerText = c.nome;
                if(c.id == currentSelectedLog) opt.selected = true;
                logSelect.appendChild(opt);
            });
            
            if(currentSelectedLog) {
                loadLogs(currentSelectedLog);
            }
        }
    } catch(e) { console.error(e); }
}

async function toggleBot(id, action) {
    try {
        const res = await fetchAuth(`${API_URL}/clients/${id}/${action}`, { method: 'POST' });
        if(res.ok) {
            loadClients();
            loadStats();
        } else {
            alert(`Erro ao ${action} bot.`);
        }
    } catch(e) { console.error(e); }
}

async function deleteClient(id) {
    if(confirm("Deseja deletar este cliente permanentemente?")) {
        try {
            const res = await fetchAuth(`${API_URL}/clients/${id}`, { method: 'DELETE' });
            if(res.ok) {
                loadClients();
                loadStats();
            }
        } catch(e) { console.error(e); }
    }
}

// Configs Log
document.getElementById('log-client-filter')?.addEventListener('change', (e) => {
    if(e.target.value) {
        loadLogs(e.target.value);
    } else {
        document.getElementById('logs-container').innerHTML = '';
    }
});

async function loadLogs(clientId) {
    try {
        const res = await fetchAuth(`${API_URL}/logs/${clientId}`);
        if(res.ok) {
            const logs = await res.json();
            const container = document.getElementById('logs-container');
            container.innerHTML = logs.map(l => {
                const colors = {
                    'info': 'text-info',
                    'error': 'text-danger',
                    'warning': 'text-warning',
                    'success': 'text-success'
                };
                const color = colors[l.tipo] || 'text-light';
                const date = new Date(l.timestamp).toLocaleTimeString();
                return `<div class="mb-1"><span class="text-muted">[${date}]</span> <span class="${color}">${l.mensagem}</span></div>`;
            }).join('');
            container.scrollTop = container.scrollHeight;
        }
    } catch(e) { console.error(e); }
}

// Novo Cliente Form
document.getElementById('newClientForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        nome: document.getElementById('c_nome').value,
        token: document.getElementById('c_token').value,
        email: document.getElementById('c_email').value,
        senha_email: document.getElementById('c_senha_email').value,
        config_json: {
            prefix: document.getElementById('c_prefix').value,
            categoria_id: document.getElementById('c_cat').value,
            cargo_mediador_id: document.getElementById('c_cargo').value
        }
    };

    try {
        const res = await fetchAuth(`${API_URL}/clients`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        
        if(res.ok) {
            // Fechar modal usando Bootstrap API
            const modal = bootstrap.Modal.getInstance(document.getElementById('clientModal'));
            modal.hide();
            e.target.reset();
            loadClients();
            loadStats();
        } else {
            alert('Erro ao criar cliente');
        }
    } catch(err) { console.error(err); }
});

// Websocket para auto-refresh (simples poll se WS for complexo na hospedagem limitante, mas usaremos intervalo aqui para facilitar garantias no OpenClaw/Square)
if (window.location.pathname === "/") {
    loadStats();
    loadClients();
    setInterval(() => {
        loadStats();
        loadClients(); // Atualiza silenciosamente as telas
    }, 10000);
}
