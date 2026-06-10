document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");
    // Se acessou login e já tem token, manda pro index
    if (token && window.location.pathname === "/login") {
        window.location.href = "/";
    }
});

const form = document.getElementById("loginForm");
if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const errorMsg = document.getElementById("errorMsg");
        
        errorMsg.style.display = "none";
        
        try {
            const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });
            
            if (res.ok) {
                const data = await res.json();
                localStorage.setItem("access_token", data.access_token);
                window.location.href = "/";
            } else {
                errorMsg.style.display = "block";
            }
        } catch (error) {
            console.error(error);
            errorMsg.innerText = "Erro ao conectar no servidor";
            errorMsg.style.display = "block";
        }
    });
}
